import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import numpy as np
from signalsight.utils.signal_generator import generate_signal
from signalsight.core.preprocessor import preprocess
from signalsight.demod.qpsk import demodulate_qpsk

def align_and_measure_ber_qpsk(gt_bits, rec_bits):
    """
    Find best alignment by testing all 4 phase rotations and varying time shifts.
    Returns: (best_offset, best_rot, num_compared, bit_errors, ber)
    """
    if len(rec_bits) == 0:
        return 0, 0, 0, 0, 1.0
        
    best_ber = 1.0
    best_res = (0, 0, 0, 0, 1.0)
    
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
                    
            errs = np.sum(o != r_test)
            ber = errs / m
            if ber < best_ber:
                best_ber = ber
                best_res = (offset, rot, m, errs, ber)
                
    return best_res

def run_qpsk_test(snr_db, phase_rot_deg=0):
    print(f"\n[QPSK TEST] SNR: {snr_db} dB, Injected Phase: {phase_rot_deg} deg")
    
    # Generate signal
    phase_offset = phase_rot_deg * np.pi / 180.0
    samples, original_bits, _ = generate_signal('QPSK', 100000, 400000, 10000, snr_db, phase_offset=phase_offset, seed=42)
    transmitted_bits = len(original_bits)
    
    # Process
    processed = preprocess(samples, 400000, dc_remove=True, normalize=True)
    res = demodulate_qpsk(processed, 400000, 100000)
    received_bits = len(res['bits'])
    
    # Measure
    offset, rot, m, errs, ber = align_and_measure_ber_qpsk(original_bits, res['bits'])
    
    print(f"  Original bits generated: {transmitted_bits}")
    print(f"  Received raw bits: {received_bits}")
    print(f"  Alignment offset: {offset} bits")
    print(f"  Phase ambiguity resolved: Rotation {rot*90} degrees")
    print(f"  Number of compared bits: {m}")
    print(f"  Bit errors: {errs}")
    print(f"  BER: {ber:.6f}")
    
    return ber

def main():
    print("=== SignalSight MVP Validation Script ===")
    
    print("\n--- PHASE 3: QPSK Phase Ambiguity Tests ---")
    for angle in [0, 90, 180, 270]:
        run_qpsk_test(20, phase_rot_deg=angle)
        
    print("\n--- PHASE 4: QPSK Low SNR Sweep ---")
    for snr in [20, 15, 10, 5, 3, 0]:
        run_qpsk_test(snr)

if __name__ == '__main__':
    main()
