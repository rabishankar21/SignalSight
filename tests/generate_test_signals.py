import os
import json
import argparse
from pathlib import Path

from signalsight.utils.signal_generator import generate_signal, save_as_iq, save_as_wav

def main():
    base_dir = Path(__file__).resolve().parent.parent
    test_signals_dir = base_dir / "data" / "test_signals"
    ground_truth_dir = base_dir / "data" / "ground_truth"
    
    test_signals_dir.mkdir(parents=True, exist_ok=True)
    ground_truth_dir.mkdir(parents=True, exist_ok=True)
    
    signals_config = [
        {"filename": "bpsk_clean", "modulation": "BPSK", "symbol_rate": 100000, "sample_rate": 400000, "snr_db": 25, "freq_offset": 0, "phase_offset": 0},
        {"filename": "bpsk_noisy", "modulation": "BPSK", "symbol_rate": 100000, "sample_rate": 400000, "snr_db": 10, "freq_offset": 0, "phase_offset": 0},
        {"filename": "bpsk_offset", "modulation": "BPSK", "symbol_rate": 100000, "sample_rate": 400000, "snr_db": 20, "freq_offset": 1500.0, "phase_offset": 0.5},
        {"filename": "qpsk_clean", "modulation": "QPSK", "symbol_rate": 100000, "sample_rate": 400000, "snr_db": 25, "freq_offset": 0, "phase_offset": 0},
        {"filename": "qpsk_noisy", "modulation": "QPSK", "symbol_rate": 100000, "sample_rate": 400000, "snr_db": 10, "freq_offset": 0, "phase_offset": 0},
        {"filename": "qpsk_offset", "modulation": "QPSK", "symbol_rate": 100000, "sample_rate": 400000, "snr_db": 20, "freq_offset": 2000.0, "phase_offset": 0.7},
        {"filename": "bpsk_2sps", "modulation": "BPSK", "symbol_rate": 100000, "sample_rate": 200000, "snr_db": 20, "freq_offset": 0, "phase_offset": 0},
        {"filename": "qpsk_8sps", "modulation": "QPSK", "symbol_rate": 50000, "sample_rate": 400000, "snr_db": 20, "freq_offset": 0, "phase_offset": 0},
    ]
    
    print(f"{'Filename':<15} | {'Mod':<5} | {'Sym Rate':<8} | {'Samp Rate':<9} | {'SNR':<3} | {'Freq Off':<8} | {'Phase Off':<9}")
    print("-" * 75)
    
    for config in signals_config:
        try:
            # Assuming generate_signal returns a tuple (signal, bits)
            result = generate_signal(
                modulation=config["modulation"],
                num_symbols=10000,
                sample_rate=config["sample_rate"],
                symbol_rate=config["symbol_rate"],
                snr_db=config["snr_db"],
                freq_offset=config["freq_offset"],
                phase_offset=config["phase_offset"],
                seed=42
            )
            if isinstance(result, tuple) and len(result) == 2:
                sig, bits = result
            else:
                sig = result
                bits = [] # Fallback if bits not returned
        except TypeError:
            # If function signature is different, fallback
            sig, bits = generate_signal(
                config["modulation"], 10000, config["sample_rate"], config["symbol_rate"],
                config["snr_db"], config["freq_offset"], config["phase_offset"], 42
            )
            
        iq_path = test_signals_dir / f"{config['filename']}.iq"
        wav_path = test_signals_dir / f"{config['filename']}.wav"
        json_path = ground_truth_dir / f"{config['filename']}.json"
        
        save_as_iq(sig, str(iq_path), dtype='float32')
        save_as_wav(sig, str(wav_path), sample_rate=config["sample_rate"])
        
        # Ground truth
        if hasattr(bits, 'tolist'):
            bits_list = bits.tolist()
        else:
            bits_list = list(bits)
            
        gt = {
            "modulation": config["modulation"],
            "symbol_rate": config["symbol_rate"],
            "sample_rate": config["sample_rate"],
            "snr_db": config["snr_db"],
            "freq_offset": config["freq_offset"],
            "phase_offset": config["phase_offset"],
            "num_symbols": 10000,
            "bits": bits_list
        }
        with open(json_path, 'w') as f:
            json.dump(gt, f)
            
        print(f"{config['filename']:<15} | {config['modulation']:<5} | {config['symbol_rate']:<8} | {config['sample_rate']:<9} | {config['snr_db']:<3} | {config['freq_offset']:<8} | {config['phase_offset']:<9}")

if __name__ == '__main__':
    main()
