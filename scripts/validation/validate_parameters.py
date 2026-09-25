import numpy as np
from signalsight.utils.signal_generator import generate_signal
from signalsight.analysis.spectral import compute_psd
from signalsight.analysis.estimator import estimate_bandwidth, estimate_snr, estimate_symbol_rate

def run_tests():
    snrs = [20, 15, 10, 5]
    mods = ['BPSK', 'QPSK']
    
    print("--- Parameter Estimator Validation ---")
    
    for mod in mods:
        for snr in snrs:
            samples, bits, meta = generate_signal(
                mod, 
                symbol_rate=100000, 
                sample_rate=400000, 
                num_symbols=4000, 
                snr_db=snr, 
                seed=42
            )
            
            # Bandwidth & SNR
            freqs, psd_db = compute_psd(samples, 400000)
            bw, f_low, f_high = estimate_bandwidth(freqs, psd_db)
            est_snr = estimate_snr(samples, 400000, bw)
            
            # Symbol rate
            sym_rate, conf = estimate_symbol_rate(samples, 400000)
            
            print(f"{mod} @ {snr}dB Configured:")
            print(f"  BW: {bw/1000:.2f} kHz")
            print(f"  SNR: {est_snr:.2f} dB")
            print(f"  SymRate: {sym_rate/1000:.2f} ksym/s (conf: {conf:.2f})")

if __name__ == '__main__':
    run_tests()
