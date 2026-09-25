import sys
import os
import numpy as np
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__))))

from signalsight.utils.signal_generator import generate_signal, save_as_wav
from signalsight.core.file_parser import load_file
from signalsight.core.pipeline import run_pipeline
from signalsight.bitstream.correlator import find_sync_word

# 1. Generate signal
mod_name = "QPSK"
symbol_rate = 100000
sample_rate = 400000
num_symbols = 4000
snr_db = 40.0

samples, orig_bits, params = generate_signal(
    mod_name,
    symbol_rate,
    sample_rate,
    num_symbols=num_symbols,
    snr_db=snr_db,
    seed=42
)

# 2. Save as WAV
wav_path = "test_qpsk.wav"
save_as_wav(samples, wav_path, sample_rate)

# 3. Load WAV
loaded_samples, loaded_sr, metadata = load_file(wav_path)
print(f"Loaded WAV: {metadata['num_samples']} samples, {loaded_sr} Hz")

# 4. Run Pipeline
config = {
    'modulation': 'auto',
    'fec': 'none',
    'interleaver': 'none',
    'symbol_rate': None,
}
results = run_pipeline(loaded_samples, loaded_sr, config)

print("\n--- Pipeline Results ---")
print("Detected Modulation:", results.get('classification', {}).get('modulation', 'Unknown'))
print("Stages Completed:", results['stages_completed'])
print("Total Bits Recovered:", results['output']['recovered_bits'])

recovered_bits = results['output'].get('bits')
if recovered_bits is not None and len(recovered_bits) > 0:
    recovered_bits = np.array(recovered_bits)
    orig_bits = np.array(orig_bits)
    
    sync = orig_bits[:64]
    matches = find_sync_word(recovered_bits, sync, threshold=0.9)
    if matches:
        offset = matches[0]['offset']
        rx = recovered_bits[offset:]
        tx = orig_bits[64:]
        min_len = min(len(rx), len(tx))
        errors = np.sum(rx[:min_len] != tx[:min_len])
        ber = errors / min_len if min_len > 0 else 1.0
        print(f"BER (aligned): {ber:.6f} with {errors} errors out of {min_len}")
    else:
        print("Sync word not found, alignment failed.")
        min_len = min(len(recovered_bits), len(orig_bits))
        errors = np.sum(recovered_bits[:min_len] != orig_bits[:min_len])
        ber = errors / min_len
        print(f"BER (raw): {ber:.6f} with {errors} errors out of {min_len}")
else:
    print("No bits recovered.")
