import os
import numpy as np
from signalsight.demod.viterbi import encode

def generate_viterbi_gui_test():
    # 1. Create directories
    os.makedirs('data/test_signals', exist_ok=True)
    os.makedirs('data/ground_truth', exist_ok=True)
    
    # 2. Parameters
    seed = 42
    num_info_bits = 2000
    sample_rate = 400000
    symbol_rate = 100000
    sps = int(sample_rate / symbol_rate)
    snr_db = 10.0
    
    # 3. Generate information bits
    np.random.seed(seed)
    info_bits = np.random.randint(0, 2, num_info_bits).astype(np.uint8)
    
    # 4. Encode bits (Rate 1/2)
    encoded_bits = encode(info_bits)
    
    # 5. Modulate to BPSK baseband
    symbols = np.where(encoded_bits == 0, 1.0 + 0j, -1.0 + 0j)
    up_symbols = np.zeros(len(symbols) * sps, dtype=complex)
    up_symbols[::sps] = symbols
    
    from signalsight.demod.bpsk import design_rrc_filter
    h_rrc = design_rrc_filter(0.35, 10, sps)
    baseband = np.convolve(up_symbols, h_rrc, mode='same')
    
    # 6. Add Noise
    pwr = np.mean(np.abs(baseband)**2)
    noise_pwr = pwr / (10 ** (snr_db / 10))
    noise = np.sqrt(noise_pwr / 2) * (np.random.randn(len(baseband)) + 1j * np.random.randn(len(baseband)))
    samples = (baseband + noise).astype(np.complex64)
    
    # 7. Save to disk
    iq_path = 'data/test_signals/viterbi_bpsk_test.iq'
    npy_path = 'data/ground_truth/viterbi_bpsk_test_bits.npy'
    
    with open(iq_path, 'wb') as f:
        samples.tofile(f)
        
    np.save(npy_path, info_bits)
    
    # The demodulator usually drops around (span * sps / 2) / sps = span/2 = 5 symbols at the start
    # and 5 at the end, so total dropped symbols ~ 10.
    dropped_symbols = 10
    expected_raw_bits = len(encoded_bits) - dropped_symbols
    # The expected Viterbi count is half of the raw bit count, truncated if odd
    expected_vit_bits = expected_raw_bits // 2
    
    # Print report
    print(f"Filename: {iq_path}")
    print(f"Ground Truth: {npy_path}")
    print(f"Sample Rate: {sample_rate} Hz")
    print(f"Number of original information bits: {num_info_bits}")
    print(f"Number of encoded bits: {len(encoded_bits)}")
    print(f"Expected raw demodulated bit count: ~{expected_raw_bits}")
    print(f"Expected Viterbi decoded bit count: ~{expected_vit_bits}")

if __name__ == '__main__':
    generate_viterbi_gui_test()
