import numpy as np
from signalsight.core.preprocessor import preprocess
from signalsight.demod.bpsk import demodulate_bpsk
from signalsight.demod.viterbi import ViterbiDecoder, encode

def generate_signal_with_bits(bits, snr_db):
    num_symbols = len(bits)
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

def align_viterbi(o, r):
    o_bipolar = o.astype(int) * 2 - 1
    r_bipolar = r.astype(int) * 2 - 1
    chunk_size = min(1000, len(o) - 100)
    o_chunk = o_bipolar[100:100+chunk_size]
    corr = np.correlate(r_bipolar, o_chunk, mode='valid')
    best_start_r = np.argmax(np.abs(corr))
    shift = best_start_r - 100
    
    for i in range(100):
        j = i - shift
        if j >= 0 and j % 2 == 0:
            start_r = i
            start_o = j
            break
            
    r_a = r[start_r:]
    o_a = o[start_o:]
    L = min(len(r_a), len(o_a))
    return o_a[:L], r_a[:L]

def align_info(o, r):
    o_bipolar = o.astype(int) * 2 - 1
    r_bipolar = r.astype(int) * 2 - 1
    chunk_size = min(1000, len(o) - 100)
    o_chunk = o_bipolar[100:100+chunk_size]
    corr = np.correlate(r_bipolar, o_chunk, mode='valid')
    best_start_r = np.argmax(np.abs(corr))
    shift = best_start_r - 100
    
    for i in range(100):
        j = i - shift
        if j >= 0:
            start_r = i
            start_o = j
            break
            
    r_a = r[start_r:]
    o_a = o[start_o:]
    L = min(len(r_a), len(o_a))
    return o_a[:L], r_a[:L]

def run_validation():
    snrs = [-5.0, 0.0, 5.0, 10.0, 15.0, 20.0]
    seeds = [42, 123, 999]
    num_info_bits = 5000
    
    print(f"{'SNR':<8} | {'Seed':<6} | {'Raw BER':<10} | {'Vit BER':<10} | {'Improv (x)':<10} | {'Status'}")
    print("-" * 65)
    
    results = {snr: [] for snr in snrs}
    
    decoder = ViterbiDecoder(k=7, polys=(0o171, 0o133))
    
    for snr in snrs:
        for seed in seeds:
            np.random.seed(seed)
            info_bits = np.random.randint(0, 2, num_info_bits).astype(np.uint8)
            encoded_bits = encode(info_bits)
            
            samples = generate_signal_with_bits(encoded_bits, snr)
            processed = preprocess(samples, 400000)
            
            demod_result = demodulate_bpsk(processed, 400000, 100000)
            raw_bits = demod_result['bits']
            
            o_aligned_enc, r_aligned_raw = align_viterbi(encoded_bits, raw_bits)
            if len(r_aligned_raw) % 2 != 0:
                r_aligned_raw = r_aligned_raw[:-1]
                o_aligned_enc = o_aligned_enc[:-1]
                
            err_raw = np.mean(o_aligned_enc != r_aligned_raw) if len(o_aligned_enc) > 0 else 1.0
            
            decoded_info = decoder.decode(r_aligned_raw)
            o_aligned_info, r_aligned_info = align_info(info_bits, decoded_info)
            
            err_vit = np.mean(o_aligned_info != r_aligned_info) if len(o_aligned_info) > 0 else 1.0
            
            if err_vit > 0:
                improv = err_raw / err_vit
                improv_str = f"{improv:.1f}x"
            elif err_raw > 0:
                improv = float('inf')
                improv_str = "INF"
            else:
                improv = 1.0
                improv_str = "N/A"
                
            status = "PASS" if err_vit <= err_raw else "FAIL"
            
            print(f"{snr:<8.1f} | {seed:<6} | {err_raw*100:<9.4f}% | {err_vit*100:<9.4f}% | {improv_str:<10} | {status}")
            
            results[snr].append((err_raw, err_vit))
            
    print("\n--- Summary Table (Mean over seeds) ---")
    print(f"{'SNR':<8} | {'Mean Raw BER':<15} | {'Mean Viterbi BER':<18} | {'Avg Improvement'}")
    print("-" * 65)
    for snr in snrs:
        raw_mean = np.mean([r[0] for r in results[snr]])
        vit_mean = np.mean([r[1] for r in results[snr]])
        if vit_mean > 0:
            imp = raw_mean / vit_mean
            imp_str = f"{imp:.1f}x"
        elif raw_mean > 0:
            imp_str = "INF"
        else:
            imp_str = "N/A"
        print(f"{snr:<8.1f} | {raw_mean*100:<14.4f}% | {vit_mean*100:<17.4f}% | {imp_str}")

if __name__ == '__main__':
    run_validation()
