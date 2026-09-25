import numpy as np
from signalsight.utils.signal_generator import generate_signal
from signalsight.analysis.modulation import classify_modulation

def run_tests():
    snrs = [20, 15, 10, 5]
    mods = ['BPSK', 'QPSK']
    
    print("--- Modulation Classification Validation ---")
    
    for mod in mods:
        for snr in snrs:
            samples, bits, meta = generate_signal(mod, symbol_rate=100000, sample_rate=400000, num_symbols=2000, snr_db=snr, seed=42)
            candidates = classify_modulation(samples, 400000, 100000)
            top = candidates[0]
            status = "PASS" if top['type'] == mod else "FAIL"
            print(f"{mod} @ {snr}dB: {top['type']} (conf: {top['confidence']:.2f}) - {status}")
            
    print("\n--- Phase Rotated Validation ---")
    for mod in mods:
        samples, bits, meta = generate_signal(mod, symbol_rate=100000, sample_rate=400000, num_symbols=2000, snr_db=20, seed=123)
        # Apply arbitrary phase rotation (e.g., pi/3)
        samples = samples * np.exp(1j * np.pi / 3)
        candidates = classify_modulation(samples, 400000, 100000)
        top = candidates[0]
        status = "PASS" if top['type'] == mod else "FAIL"
        print(f"{mod} rotated @ 20dB: {top['type']} (conf: {top['confidence']:.2f}) - {status}")

if __name__ == '__main__':
    run_tests()
