"""
End-to-end pipeline tests for SignalSight MVP.
Tests BPSK/QPSK demodulation at various SNR, frequency offset, phase offset,
and samples-per-symbol configurations. Also tests bandwidth estimation,
SNR estimation, and modulation classification.
"""
import unittest
import numpy as np

from signalsight.core.preprocessor import preprocess
from signalsight.analysis.spectral import compute_psd
from signalsight.analysis.estimator import estimate_bandwidth, estimate_snr, estimate_symbol_rate
from signalsight.analysis.modulation import classify_modulation
from signalsight.demod import demodulate_bpsk, demodulate_qpsk
from signalsight.utils.signal_generator import generate_signal


def compute_ber(original_bits, recovered_bits, mod_type='BPSK'):
    """
    Compute Bit Error Rate between original and recovered bit sequences.
    Handles:
    - Different array lengths (trims to shorter)
    - Alignment offset (searches small shift range)
    - Phase ambiguity: BPSK (bit inversion), QPSK (4 rotations)
    """
    if original_bits is None or recovered_bits is None:
        return 1.0
    if len(original_bits) == 0 or len(recovered_bits) == 0:
        return 1.0

    original_bits = np.array(original_bits, dtype=np.uint8)
    recovered_bits = np.array(recovered_bits, dtype=np.uint8)

    # Skip initial convergence period (carrier/timing recovery transient)
    skip = 300
    if len(original_bits) > skip * 2:
        orig = original_bits[skip:]
    else:
        orig = original_bits
    if len(recovered_bits) > skip * 2:
        recov = recovered_bits[skip:]
    else:
        recov = recovered_bits

    min_len = min(len(orig), len(recov))
    if min_len == 0:
        return 1.0
    orig = orig[:min_len]
    recov = recov[:min_len]

    def calc_best_error(o, r):
        """Find the minimum BER using cross-correlation for alignment."""
        if len(o) < 200 or len(r) < 200:
            return 1.0
        
        # Use cross-correlation to find the shift
        o_bipolar = o.astype(int) * 2 - 1
        r_bipolar = r.astype(int) * 2 - 1
        
        # Correlate a chunk from the middle of o with r
        chunk_size = min(1000, len(o) - 100)
        o_chunk = o_bipolar[100:100+chunk_size]
        
        corr = np.correlate(r_bipolar, o_chunk, mode='valid')
        if len(corr) == 0:
            return 1.0
            
        best_start_r = np.argmax(np.abs(corr))
        
        # best_start_r is the index in r where o[100] starts.
        # So o[100] aligns with r[best_start_r].
        # o[0] aligns with r[best_start_r - 100].
        shift = best_start_r - 100
        
        if shift < 0:
            o_aligned = o[-shift:]
            r_aligned = r[:len(o_aligned)]
        else:
            o_aligned = o[:len(r) - shift]
            r_aligned = r[shift:shift + len(o_aligned)]
            
        compare_len = min(len(o_aligned), len(r_aligned))
        if compare_len == 0:
            return 1.0
            
        err = np.mean(o_aligned[:compare_len] != r_aligned[:compare_len])
        return err

    if mod_type == 'BPSK':
        # Try normal and inverted (180-degree phase ambiguity)
        err_normal = calc_best_error(orig, recov)
        err_inverted = calc_best_error(orig, 1 - recov)
        return min(err_normal, err_inverted)

    elif mod_type == 'QPSK':
        # QPSK has 4 possible phase rotations (0, 90, 180, 270 degrees)
        # Each rotation remaps the Gray-coded bit pairs
        best_ber = 1.0

        # Try all 4 rotations by remapping bit pairs
        for rotation in range(4):
            if rotation == 0:
                r_test = recov.copy()
            elif rotation == 1:
                # 90 degree: swap I/Q bits and invert new Q
                r_test = recov.copy()
                for i in range(0, len(r_test) - 1, 2):
                    b0, b1 = r_test[i], r_test[i + 1]
                    r_test[i] = b1
                    r_test[i + 1] = 1 - b0
            elif rotation == 2:
                # 180 degree: invert both bits
                r_test = 1 - recov
            elif rotation == 3:
                # 270 degree: swap I/Q and invert new I
                r_test = recov.copy()
                for i in range(0, len(r_test) - 1, 2):
                    b0, b1 = r_test[i], r_test[i + 1]
                    r_test[i] = 1 - b1
                    r_test[i + 1] = b0

            err = calc_best_error(orig, r_test)
            best_ber = min(best_ber, err)

        return best_ber

    return calc_best_error(orig, recov)


class TestPipeline(unittest.TestCase):
    """End-to-end pipeline tests for BPSK and QPSK."""

    def _generate(self, mod, snr_db, freq_offset=0.0, phase_offset=0.0,
                  symbol_rate=100000, sample_rate=400000, num_symbols=5000):
        """Helper to generate a test signal and return (samples, original_bits)."""
        samples, bits, gt = generate_signal(
            modulation=mod,
            symbol_rate=symbol_rate,
            sample_rate=sample_rate,
            num_symbols=num_symbols,
            snr_db=snr_db,
            freq_offset=freq_offset,
            phase_offset=phase_offset,
            rolloff=0.35,
            seed=42,
        )
        return samples, bits, sample_rate, symbol_rate

    # ---- BPSK Clean ----
    def test_bpsk_demod_clean(self):
        samples, bits, sr, sym_r = self._generate("BPSK", 25)
        processed = preprocess(samples, sr)
        result = demodulate_bpsk(processed, sr, sym_r)
        ber = compute_ber(bits, result['bits'], 'BPSK')
        print(f"  BPSK clean: BER={ber:.4f}")
        self.assertLess(ber, 0.01, f"BPSK clean BER too high: {ber:.4f}")

    # ---- QPSK Clean ----
    def test_qpsk_demod_clean(self):
        samples, bits, sr, sym_r = self._generate("QPSK", 25)
        processed = preprocess(samples, sr)
        result = demodulate_qpsk(processed, sr, sym_r)
        ber = compute_ber(bits, result['bits'], 'QPSK')
        print(f"  QPSK clean: BER={ber:.4f}")
        self.assertLess(ber, 0.01, f"QPSK clean BER too high: {ber:.4f}")

    # ---- Frequency offset tests ----
    def test_bpsk_demod_with_freq_offset(self):
        samples, bits, sr, sym_r = self._generate("BPSK", 20, freq_offset=1500.0)
        processed = preprocess(samples, sr)
        result = demodulate_bpsk(processed, sr, sym_r)
        ber = compute_ber(bits, result['bits'], 'BPSK')
        print(f"  BPSK freq_offset=1500Hz: BER={ber:.4f}")
        self.assertLess(ber, 0.05, f"BPSK freq offset BER too high: {ber:.4f}")

    def test_qpsk_demod_with_freq_offset(self):
        samples, bits, sr, sym_r = self._generate("QPSK", 20, freq_offset=2000.0)
        processed = preprocess(samples, sr)
        result = demodulate_qpsk(processed, sr, sym_r)
        ber = compute_ber(bits, result['bits'], 'QPSK')
        print(f"  QPSK freq_offset=2000Hz: BER={ber:.4f}")
        self.assertLess(ber, 0.05, f"QPSK freq offset BER too high: {ber:.4f}")

    # ---- Phase offset tests ----
    def test_bpsk_demod_with_phase_offset(self):
        samples, bits, sr, sym_r = self._generate("BPSK", 20, phase_offset=np.pi / 3)
        processed = preprocess(samples, sr)
        result = demodulate_bpsk(processed, sr, sym_r)
        ber = compute_ber(bits, result['bits'], 'BPSK')
        print(f"  BPSK phase_offset=pi/3: BER={ber:.4f}")
        self.assertLess(ber, 0.05, f"BPSK phase offset BER too high: {ber:.4f}")

    def test_qpsk_demod_with_phase_offset(self):
        samples, bits, sr, sym_r = self._generate("QPSK", 20, phase_offset=np.pi / 4)
        processed = preprocess(samples, sr)
        result = demodulate_qpsk(processed, sr, sym_r)
        ber = compute_ber(bits, result['bits'], 'QPSK')
        print(f"  QPSK phase_offset=pi/4: BER={ber:.4f}")
        self.assertLess(ber, 0.05, f"QPSK phase offset BER too high: {ber:.4f}")

    # ---- SNR sweeps ----
    def test_bpsk_snr_sweep(self):
        print("\n  BPSK SNR sweep:")
        for snr in [5, 10, 15, 20, 25]:
            samples, bits, sr, sym_r = self._generate("BPSK", snr)
            processed = preprocess(samples, sr)
            result = demodulate_bpsk(processed, sr, sym_r)
            ber = compute_ber(bits, result['bits'], 'BPSK')
            print(f"    SNR={snr:2d} dB  BER={ber:.4f}")
            if snr == 15:
                self.assertLess(ber, 0.1, f"BPSK BER too high at SNR=15: {ber}")
            elif snr == 25:
                self.assertLess(ber, 0.01, f"BPSK BER too high at SNR=25: {ber}")

    def test_qpsk_snr_sweep(self):
        print("\n  QPSK SNR sweep:")
        for snr in [5, 10, 15, 20, 25]:
            samples, bits, sr, sym_r = self._generate("QPSK", snr)
            processed = preprocess(samples, sr)
            result = demodulate_qpsk(processed, sr, sym_r)
            ber = compute_ber(bits, result['bits'], 'QPSK')
            print(f"    SNR={snr:2d} dB  BER={ber:.4f}")
            if snr == 15:
                self.assertLess(ber, 0.1, f"QPSK BER too high at SNR=15: {ber}")
            elif snr == 25:
                self.assertLess(ber, 0.01, f"QPSK BER too high at SNR=25: {ber}")

    # ---- Bandwidth estimation ----
    def test_bandwidth_estimation(self):
        samples, _, sr, _ = self._generate("QPSK", 30, symbol_rate=100000)
        processed = preprocess(samples, sr)
        freqs, psd_db = compute_psd(processed, sr)
        bw, f_low, f_high = estimate_bandwidth(freqs, psd_db)
        expected_bw = 100000 * (1 + 0.35)  # ~135 kHz
        print(f"  BW estimated: {bw:.0f} Hz, expected ~{expected_bw:.0f} Hz")
        self.assertGreater(bw, expected_bw * 0.5,
                           f"Estimated BW {bw:.0f} too low (expected ~{expected_bw:.0f})")
        self.assertLess(bw, expected_bw * 2.0,
                        f"Estimated BW {bw:.0f} too high (expected ~{expected_bw:.0f})")

    # ---- SNR estimation ----
    def test_snr_estimation(self):
        samples, _, sr, _ = self._generate("QPSK", 20, symbol_rate=100000)
        processed = preprocess(samples, sr)
        freqs, psd_db = compute_psd(processed, sr)
        bw, _, _ = estimate_bandwidth(freqs, psd_db)
        if bw <= 0:
            bw = 135000  # fallback
        snr_est = estimate_snr(processed, sr, bw)
        print(f"  SNR estimated: {snr_est:.1f} dB, true: 20 dB")
        self.assertGreater(snr_est, 10, f"SNR estimate {snr_est:.1f} too low")
        self.assertLess(snr_est, 30, f"SNR estimate {snr_est:.1f} too high")

    # ---- Modulation classification ----
    def test_modulation_classification_bpsk(self):
        samples, _, sr, _ = self._generate("BPSK", 25)
        processed = preprocess(samples, sr)
        candidates = classify_modulation(processed, sr)
        top_type = candidates[0]['type']
        print(f"  BPSK classification: top={top_type} (candidates: {candidates})")
        self.assertEqual(top_type, 'BPSK',
                         f"Expected BPSK, got {top_type}. Candidates: {candidates}")

    def test_modulation_classification_qpsk(self):
        samples, _, sr, _ = self._generate("QPSK", 25)
        processed = preprocess(samples, sr)
        candidates = classify_modulation(processed, sr)
        top_type = candidates[0]['type']
        print(f"  QPSK classification: top={top_type} (candidates: {candidates})")
        self.assertEqual(top_type, 'QPSK',
                         f"Expected QPSK, got {top_type}. Candidates: {candidates}")

    # ---- Different samples per symbol ----
    def test_different_sps(self):
        print("\n  Different SPS:")
        for sps in [2, 4, 8]:
            sym_r = 400000 // sps
            samples, bits, sr, _ = self._generate(
                "BPSK", 25, symbol_rate=sym_r, sample_rate=400000)
            processed = preprocess(samples, sr)
            result = demodulate_bpsk(processed, sr, sym_r)
            ber = compute_ber(bits, result['bits'], 'BPSK')
            print(f"    SPS={sps} (sym_rate={sym_r}): BER={ber:.4f}")
            self.assertLess(ber, 0.05, f"Failed for SPS={sps}, BER={ber:.4f}")

    def test_bandwidth_estimation(self):
        samples, bits, meta = generate_signal('BPSK', 100000, 400000, num_symbols=2000, snr_db=15, seed=42)
        freqs, psd = compute_psd(samples, 400000)
        bw, f_low, f_high = estimate_bandwidth(freqs, psd)
        
        # A 100ksps BPSK signal with 0.35 rolloff has approx 115-120 kHz smoothed bandwidth.
        self.assertGreater(bw, 100000)
        self.assertLess(bw, 130000)

    def test_snr_estimation(self):
        # SNR estimation should track physically
        samples_high, _, _ = generate_signal('BPSK', 100000, 400000, num_symbols=2000, snr_db=20, seed=42)
        samples_low, _, _ = generate_signal('BPSK', 100000, 400000, num_symbols=2000, snr_db=10, seed=42)
        
        freqs_h, psd_h = compute_psd(samples_high, 400000)
        bw_h, _, _ = estimate_bandwidth(freqs_h, psd_h)
        snr_high = estimate_snr(samples_high, 400000, bw_h)
        
        freqs_l, psd_l = compute_psd(samples_low, 400000)
        bw_l, _, _ = estimate_bandwidth(freqs_l, psd_l)
        snr_low = estimate_snr(samples_low, 400000, bw_l)
        
        self.assertGreater(snr_high, 12.0)
        self.assertGreater(snr_high, snr_low + 5.0)
        self.assertLess(snr_low, snr_high - 5.0)

    def test_symbol_rate_estimation(self):
        samples, _, _ = generate_signal('QPSK', 100000, 400000, num_symbols=2000, snr_db=15, seed=42)
        from signalsight.analysis.estimator import estimate_symbol_rate
        rate, conf = estimate_symbol_rate(samples, 400000)
        self.assertAlmostEqual(rate, 100000, delta=5000)

    def test_carrier_offset_estimation(self):
        samples, _, _ = generate_signal('BPSK', 100000, 400000, num_symbols=2000, snr_db=20, freq_offset=5000.0, seed=42)
        from signalsight.demod.bpsk import _estimate_freq_offset_bpsk
        est = _estimate_freq_offset_bpsk(samples, 400000)
        self.assertAlmostEqual(est, 5000.0, delta=100.0)

if __name__ == '__main__':
    unittest.main(verbosity=2)
