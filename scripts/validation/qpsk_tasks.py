import os
import numpy as np
import scipy.io.wavfile
from signalsight.utils.signal_generator import generate_signal
from signalsight.core.file_parser import load_file
from signalsight.core.preprocessor import preprocess
from signalsight.analysis.modulation import classify_modulation
from signalsight.analysis.spectral import compute_psd
from signalsight.analysis.estimator import estimate_bandwidth, estimate_snr, estimate_symbol_rate
from signalsight.demod.qpsk import demodulate_qpsk

def align_and_measure_ber(gt_bits, rec_bits):
    if len(rec_bits) == 0: return 1.0
    best_ber = 1.0
    for offset in range(-50, 50):
        if offset < 0:
            o = gt_bits[-offset:]
            r = rec_bits[:len(o)]
        else:
            o = gt_bits
            r = rec_bits[offset:offset+len(o)]
            
        m = min(len(o), len(r))
        if m < len(gt_bits) // 2: continue
        
        o = o[:m]
        r = r[:m]
        
        # Test 4 phase rotations for QPSK
        for rot in range(4):
            r_test = r.copy()
            if rot == 1: # 90 deg
                for i in range(0, len(r_test)-1, 2):
                    b0, b1 = r_test[i], r_test[i+1]
                    r_test[i], r_test[i+1] = b1, 1 - b0
            elif rot == 2: # 180 deg
                for i in range(0, len(r_test)-1, 2):
                    b0, b1 = r_test[i], r_test[i+1]
                    r_test[i], r_test[i+1] = 1 - b0, 1 - b1
            elif rot == 3: # 270 deg
                for i in range(0, len(r_test)-1, 2):
                    b0, b1 = r_test[i], r_test[i+1]
                    r_test[i], r_test[i+1] = 1 - b1, b0
                    
            ber = np.sum(o != r_test) / m
            if ber < best_ber:
                best_ber = ber
    return best_ber

def run_tests():
    os.makedirs('data/test_signals', exist_ok=True)
    os.makedirs('data/ground_truth', exist_ok=True)
    
    print("--- TASK 1: QPSK Ground Truth Generation ---")
    samples, bits, meta = generate_signal('QPSK', 100000, 400000, 2000, 10.0, seed=42)
    # Save as complex64
    samples.astype(np.complex64).tofile('data/test_signals/qpsk_ground_truth.iq')
    np.save('data/ground_truth/qpsk_ground_truth_bits.npy', bits)
    print("Saved QPSK Ground Truth files.\n")
    
    print("--- TASK 2: End-to-End QPSK Validation ---")
    iq_samples, sr, iq_meta = load_file('data/test_signals/qpsk_ground_truth.iq', sample_rate=400000, iq_format='complex64')
    processed = preprocess(iq_samples, sr, dc_remove=True, normalize=True)
    
    freqs, psd = compute_psd(processed, sr)
    bw, _, _ = estimate_bandwidth(freqs, psd)
    snr = estimate_snr(processed, sr, bw)
    sym_rate, _ = estimate_symbol_rate(processed, sr)
    
    candidates = classify_modulation(processed, sr, sym_rate)
    top_mod = candidates[0]['type']
    
    print(f"Est SNR: {snr:.1f} dB")
    print(f"Est BW: {bw/1000:.1f} kHz")
    print(f"Est SymRate: {sym_rate/1000:.1f} ksps")
    print(f"Classifier Mod: {top_mod} (conf: {candidates[0]['confidence']:.2f})")
    
    if top_mod == 'QPSK':
        demod_res = demodulate_qpsk(processed, sr, sym_rate, rolloff=0.35)
        raw_bits = demod_res['bits']
        ber = align_and_measure_ber(bits, raw_bits)
        print(f"Raw bit count: {len(raw_bits)}")
        print(f"BER: {ber:.6f}\n")
    else:
        print("FAIL: Not QPSK\n")
        
    print("--- TASK 3: QPSK Frequency Offset Tests ---")
    for offset in [0, 5000, -5000, 10000, -10000]:
        s, b, _ = generate_signal('QPSK', 100000, 400000, 2000, 20.0, freq_offset=offset, seed=42)
        p = preprocess(s, 400000, dc_remove=True, normalize=True)
        res = demodulate_qpsk(p, 400000, 100000)
        est_off = res['carrier_freq_offset']
        ber = align_and_measure_ber(b, res['bits'])
        print(f"Offset {offset:6d} Hz -> Est: {est_off:7.1f} Hz | BER: {ber:.6f}")
        
    print("\n--- TASK 4: QPSK SNR Sweep ---")
    for snr_val in [20, 15, 10, 5]:
        s, b, _ = generate_signal('QPSK', 100000, 400000, 2000, snr_val, seed=42)
        p = preprocess(s, 400000, dc_remove=True, normalize=True)
        res = demodulate_qpsk(p, 400000, 100000)
        ber = align_and_measure_ber(b, res['bits'])
        print(f"SNR {snr_val} dB -> BER: {ber:.6f}")
        
    print("\n--- TASK 5: WAV Validation ---")
    # Generate a real WAV by keeping I and Q as two channels
    s, b, _ = generate_signal('BPSK', 100000, 400000, 2000, 20.0, seed=42)
    wav_data = np.column_stack((s.real, s.imag))
    # Normalize to int16 range
    wav_data = np.int16(wav_data / np.max(np.abs(wav_data)) * 32767)
    scipy.io.wavfile.write('data/test_signals/test.wav', 400000, wav_data)
    
    wav_samples, wav_sr, wav_meta = load_file('data/test_signals/test.wav')
    print(f"WAV loaded: format={wav_meta['format']}, sr={wav_sr}, samples={len(wav_samples)}")
    wp = preprocess(wav_samples, wav_sr, dc_remove=True, normalize=True)
    w_freqs, w_psd = compute_psd(wp, wav_sr)
    w_bw, _, _ = estimate_bandwidth(w_freqs, w_psd)
    w_snr = estimate_snr(wp, wav_sr, w_bw)
    w_sym, _ = estimate_symbol_rate(wp, wav_sr)
    print(f"WAV params -> BW: {w_bw/1000:.1f} kHz, SNR: {w_snr:.1f} dB, SymRate: {w_sym/1000:.1f} ksps")
    
    print("\n--- TASK 6: IQ Format Robustness ---")
    for fmt in ['float32', 'int16', 'complex64']:
        s, b, _ = generate_signal('BPSK', 100000, 400000, 2000, 20.0, seed=42)
        fn = f'data/test_signals/test_{fmt}.iq'
        if fmt == 'float32':
            data = np.zeros(len(s)*2, dtype=np.float32)
            data[0::2] = s.real
            data[1::2] = s.imag
            data.tofile(fn)
        elif fmt == 'int16':
            data = np.zeros(len(s)*2, dtype=np.int16)
            data[0::2] = np.int16(s.real * 32767)
            data[1::2] = np.int16(s.imag * 32767)
            data.tofile(fn)
        elif fmt == 'complex64':
            s.astype(np.complex64).tofile(fn)
            
        iq_s, iq_sr, iq_m = load_file(fn, sample_rate=400000, iq_format=fmt)
        print(f"Loaded {fmt}: max real={np.max(np.abs(iq_s.real)):.3f}, len={len(iq_s)}")

if __name__ == '__main__':
    run_tests()
