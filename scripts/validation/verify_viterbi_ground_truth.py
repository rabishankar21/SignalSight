import numpy as np
from signalsight.core.file_parser import load_file
from signalsight.core.preprocessor import preprocess
from signalsight.demod.bpsk import demodulate_bpsk
from signalsight.demod.viterbi import ViterbiDecoder

def align_bits(o, r, require_even_o=False):
    if len(o) < 200 or len(r) < 200: return o, r, 1.0, 0
    o_bipolar = o.astype(int) * 2 - 1
    r_bipolar = r.astype(int) * 2 - 1
    chunk_size = min(1000, len(o) - 100)
    o_chunk = o_bipolar[100:100+chunk_size]
    corr = np.correlate(r_bipolar, o_chunk, mode='valid')
    if len(corr) == 0: return o, r, 1.0, 0
    
    best_start_r = np.argmax(np.abs(corr))
    shift = best_start_r - 100
    
    start_r, start_o = 0, 0
    for i in range(100):
        j = i - shift
        if j >= 0:
            if require_even_o and j % 2 != 0:
                continue
            start_r = i
            start_o = j
            break
            
    r_a = r[start_r:]
    o_a = o[start_o:]
    L = min(len(r_a), len(o_a))
    return o_a[:L], r_a[:L], shift

def verify_viterbi_ground_truth():
    print("--- Ground Truth Viterbi Verification ---\n")
    
    # 1. Load Files
    iq_path = 'data/test_signals/viterbi_bpsk_test.iq'
    npy_path = 'data/ground_truth/viterbi_bpsk_test_bits.npy'
    
    samples, sample_rate, meta = load_file(iq_path, sample_rate=400000.0, iq_format='complex64')
    info_bits_gt = np.load(npy_path)
    
    print(f"Loaded signal: {len(samples)} samples")
    print(f"Loaded ground truth: {len(info_bits_gt)} bits")
    
    # 2. Raw Demodulation
    processed = preprocess(samples, sample_rate, dc_remove=True, normalize=True)
    demod_result = demodulate_bpsk(processed, sample_rate, symbol_rate=100000.0, rolloff=0.35)
    raw_bits = demod_result['bits']
    print(f"Raw demodulated bits: {len(raw_bits)}")
    
    # We must align the raw sequence correctly for the Viterbi decoder.
    # To decode correctly, we mathematically ensure the sequence starts on an EVEN codeword boundary.
    # We use a dummy encoder to find the boundary offset.
    from signalsight.demod.viterbi import encode
    encoded_bits_gt = encode(info_bits_gt)
    
    o_aligned_enc, r_aligned_raw, enc_shift = align_bits(encoded_bits_gt, raw_bits, require_even_o=True)
    
    if len(r_aligned_raw) % 2 != 0:
        r_aligned_raw = r_aligned_raw[:-1]
        o_aligned_enc = o_aligned_enc[:-1]
        
    err_raw = np.sum(o_aligned_enc != r_aligned_raw)
    ber_raw = err_raw / len(o_aligned_enc) if len(o_aligned_enc) > 0 else 1.0
    print(f"Raw Demodulator Shift (Code boundary offset): {enc_shift} bits")
    print(f"Raw Demodulated BER (aligned): {ber_raw*100:.4f}% ({err_raw} errors / {len(o_aligned_enc)})\n")
    
    # 3. Viterbi Decoding
    decoder = ViterbiDecoder(k=7, polys=(0o171, 0o133))
    decoded_bits = decoder.decode(r_aligned_raw)
    print(f"Viterbi decoded bits: {len(decoded_bits)}")
    
    # 4. Final Ground-Truth Comparison
    o_aligned_info, r_aligned_info, info_shift = align_bits(info_bits_gt, decoded_bits, require_even_o=False)
    
    compare_len = min(len(o_aligned_info), len(r_aligned_info))
    bit_errors = int(np.sum(o_aligned_info != r_aligned_info))
    ber = bit_errors / compare_len if compare_len > 0 else 1.0
    
    exact_match = (bit_errors == 0)
    
    print("--- Ground-Truth Comparison Result ---")
    print(f"Algorithmic Alignment Offset: {info_shift} bits")
    print(f"Exact Length after alignment: {compare_len} bits")
    print(f"Number of Bit Errors:         {bit_errors}")
    print(f"Measured BER:                 {ber * 100:.6f}%")
    print(f"Exact Sequence Match:         {'YES' if exact_match else 'NO'}")

if __name__ == '__main__':
    verify_viterbi_ground_truth()
