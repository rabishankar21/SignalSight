import os
import numpy as np

from signalsight.fec.reed_solomon import ReedSolomonFEC
from signalsight.interleave.block import block_interleave
from signalsight.utils.signal_generator import generate_signal

def generate_rs_interleaved_signal():
    print("Generating RS + Interleaved test signal...")
    
    np.random.seed(42)
    
    # 1. Generate information bits
    # 32 nsym out of 100 info bytes = 132 bytes = 1056 bits
    num_info_bytes = 100
    info_bytes = np.random.randint(0, 256, num_info_bytes, dtype=np.uint8)
    info_bits = np.unpackbits(info_bytes)
    
    os.makedirs('data/ground_truth', exist_ok=True)
    os.makedirs('data/test_signals', exist_ok=True)
    np.save('data/ground_truth/rs_interleaved_bpsk_test_bits.npy', info_bits)
    
    # 2. RS Encode
    rs = ReedSolomonFEC(nsym=32)
    encoded_bytes = rs.encode_bytes(info_bytes)
    encoded_bits = np.unpackbits(encoded_bytes)
    
    # 3. Interleave (Rows=32, Cols=33 -> 1056 bits)
    interleaved_bits = block_interleave(encoded_bits, 32, 33)
    
    # 4. Modulate & Channel (SNR = 6 dB BPSK to induce some errors but not completely destroy it)
    sps = 4
    symbols = np.where(interleaved_bits == 0, 1.0 + 0j, -1.0 + 0j)
    up_symbols = np.zeros(len(symbols) * sps, dtype=complex)
    up_symbols[::sps] = symbols
    
    from signalsight.demod.bpsk import design_rrc_filter
    h_rrc = design_rrc_filter(0.35, 10, sps)
    baseband = np.convolve(up_symbols, h_rrc, mode='same')
    
    # We want a 4 dB SNR 
    snr_db = 4.0
    pwr = np.mean(np.abs(baseband)**2)
    noise_pwr = pwr / (10 ** (snr_db / 10))
    noise = np.sqrt(noise_pwr / 2) * (np.random.randn(len(baseband)) + 1j * np.random.randn(len(baseband)))
    samples = (baseband + noise).astype(np.complex64)
    
    samples.tofile('data/test_signals/rs_interleaved_bpsk_test.iq')
    
    print("Done. Saved rs_interleaved_bpsk_test.iq")
    print(f"Info payload: {len(info_bits)} bits")
    print(f"Encoded size: {len(encoded_bits)} bits")
    print(f"Interleaver: 32 rows, 33 columns")
    print(f"Modulation: BPSK")
    print(f"Sample Rate: 400000 Hz")
    print(f"Symbol Rate: 100000 sps")
    print(f"SNR: {snr_db} dB")
    print(f"Seed: 42")

if __name__ == '__main__':
    generate_rs_interleaved_signal()
