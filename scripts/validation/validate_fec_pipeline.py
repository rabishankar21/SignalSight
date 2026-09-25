import numpy as np
from signalsight.utils.signal_generator import generate_signal
from signalsight.core.preprocessor import preprocess
from signalsight.demod.bpsk import demodulate_bpsk
from signalsight.demod.viterbi import ViterbiDecoder, encode

def run_fec_validation():
    print("=== SignalSight FEC End-to-End Validation (Basic Viterbi K=7, R=1/2) ===")
    
    # 1. Generate original information bits
    np.random.seed(42)
    num_info_bits = 5000
    info_bits = np.random.randint(0, 2, num_info_bits).astype(np.uint8)
    
    # 2. Convolutionally encode bits (length becomes 10000)
    encoded_bits = encode(info_bits)
    
    # 3. Generate BPSK signal with the encoded bits
    # We monkeypatch the generator to use our specific bits
    import signalsight.utils.signal_generator as sg
    
    def generate_signal_with_bits(bits, snr_db):
        num_symbols = len(bits)
        sample_rate = 400000
        symbol_rate = 100000
        sps = 4
        
        symbols = np.where(bits == 0, 1.0 + 0j, -1.0 + 0j)
        
        up_symbols = np.zeros(num_symbols * sps, dtype=complex)
        up_symbols[::sps] = symbols
        
        from signalsight.demod.bpsk import design_rrc_filter
        h_rrc = design_rrc_filter(0.35, 10, sps)
        baseband = np.convolve(up_symbols, h_rrc, mode='same')
        
        pwr = np.mean(np.abs(baseband)**2)
        noise_pwr = pwr / (10 ** (snr_db / 10))
        noise = np.sqrt(noise_pwr / 2) * (np.random.randn(len(baseband)) + 1j * np.random.randn(len(baseband)))
        
        samples = baseband + noise
        return samples

    snr_db = -5.0  # Very noisy to cause some errors before FEC
    print(f"\nGenerating BPSK signal containing {len(encoded_bits)} encoded bits at SNR = {snr_db} dB...")
    samples = generate_signal_with_bits(encoded_bits, snr_db)
    
    # 4. Demodulate the signal (Raw bits)
    print("Demodulating signal...")
    processed = preprocess(samples, 400000)
    demod_result = demodulate_bpsk(processed, 400000, 100000)
    raw_recovered_bits = demod_result['bits']
    
    # 5. BER Comparison (Before FEC)
    def calc_best_error(o, r):
        if len(o) < 200 or len(r) < 200: return 1.0
        o_bipolar = o.astype(int) * 2 - 1
        r_bipolar = r.astype(int) * 2 - 1
        chunk_size = min(1000, len(o) - 100)
        o_chunk = o_bipolar[100:100+chunk_size]
        corr = np.correlate(r_bipolar, o_chunk, mode='valid')
        if len(corr) == 0: return 1.0
        best_start_r = np.argmax(np.abs(corr))
        shift = best_start_r - 100
        if shift < 0:
            o_aligned = o[-shift:]
            r_aligned = r[:len(o_aligned)]
        else:
            o_aligned = o[:len(r) - shift]
            r_aligned = r[shift:shift + len(o_aligned)]
        compare_len = min(len(o_aligned), len(r_aligned))
        if compare_len == 0: return 1.0
        return np.mean(o_aligned[:compare_len] != r_aligned[:compare_len])
    
    err_before_fec = calc_best_error(encoded_bits, raw_recovered_bits)
    print(f"RAW DEMODULATED BER (Before FEC): {err_before_fec * 100:.4f}%")
    
    # 6. Apply Viterbi Decoder
    print("\nApplying Viterbi Decoder...")
    decoder = ViterbiDecoder(k=7, polys=(0o171, 0o133))
    
    # Since the demodulator drops a few bits (usually ~5-10 symbols), the stream might be misaligned
    # by an odd number of bits, or missing the first few. Viterbi needs exactly the aligned sequence
    # to decode correctly. We'll use the cross-correlation shift to find the exact start index.
    def align_viterbi(o, r):
        o_bipolar = o.astype(int) * 2 - 1
        r_bipolar = r.astype(int) * 2 - 1
        chunk_size = min(1000, len(o) - 100)
        o_chunk = o_bipolar[100:100+chunk_size]
        corr = np.correlate(r_bipolar, o_chunk, mode='valid')
        best_start_r = np.argmax(np.abs(corr))
        shift = best_start_r - 100
        
        for i in range(10):
            j = i - shift
            if j >= 0 and j % 2 == 0:
                start_r = i
                start_o = j
                break
                
        r_a = r[start_r:]
        o_a = o[start_o:]
        L = min(len(r_a), len(o_a))
        return o_a[:L], r_a[:L]

    o_aligned_encoded, r_aligned_raw = align_viterbi(encoded_bits, raw_recovered_bits)
    
    if len(r_aligned_raw) % 2 != 0:
        r_aligned_raw = r_aligned_raw[:-1]
        
    decoded_info_bits = decoder.decode(r_aligned_raw)
    
    err_after_fec = calc_best_error(info_bits, decoded_info_bits)
    
    print(f"VITERBI DECODED BER (After FEC):  {err_after_fec * 100:.4f}%")
    
    if err_after_fec < err_before_fec:
        print("\nSUCCESS: Viterbi Decoder significantly reduced the Bit Error Rate!")
    else:
        print("\nFAILURE: Viterbi Decoder did not improve the Bit Error Rate.")

if __name__ == '__main__':
    run_fec_validation()
