import unittest
import numpy as np
from signalsight.utils.signal_generator import generate_signal
from signalsight.demod.psk8 import demodulate_8psk
from signalsight.demod.fsk import demodulate_fsk
from signalsight.demod.qam import demodulate_qam
from signalsight.analysis.modulation import classify_modulation

class TestLevel3Modulation(unittest.TestCase):
    def setUp(self):
        self.sample_rate = 400000
        self.symbol_rate = 100000
        self.num_symbols = 1000
        
    def _test_demod(self, mod_name, demod_fn, **kwargs):
        samples, bits_gt, _ = generate_signal(mod_name, self.symbol_rate, self.sample_rate, self.num_symbols, snr_db=30.0, seed=42)
        res = demod_fn(samples, self.sample_rate, self.symbol_rate, **kwargs)
        
        bits_rec = res['bits']
        min_len = min(len(bits_gt), len(bits_rec))
        self.assertTrue(min_len > 0, f"{mod_name} returned 0 bits")
        
        best_errors = min_len
        for shift in range(-20, 21):
            if shift < 0:
                gt = bits_gt[-shift:min_len]
                rec = bits_rec[:min_len+shift]
            else:
                gt = bits_gt[:min_len-shift]
                rec = bits_rec[shift:min_len]
            err = np.sum(gt != rec)
            if err < best_errors:
                best_errors = err
                
        ber = best_errors / len(bits_gt)
        self.assertLess(ber, 0.05, f"{mod_name} BER {ber} too high")

    def test_8psk_demod(self):
        self._test_demod('8PSK', demodulate_8psk)

    def test_2fsk_demod(self):
        self._test_demod('2FSK', demodulate_fsk, num_tones=2)
        
    def test_16qam_demod(self):
        self._test_demod('16QAM', demodulate_qam, order=16)

    def test_64qam_demod(self):
        self._test_demod('64QAM', demodulate_qam, order=64)

    def _test_class(self, mod_name):
        samples, _, _ = generate_signal(mod_name, self.symbol_rate, self.sample_rate, 4000, snr_db=40.0, seed=42)
        candidates = classify_modulation(samples, self.sample_rate, self.symbol_rate)
        self.assertTrue(len(candidates) > 0)
        self.assertEqual(candidates[0]['family'], 'QAM' if 'QAM' in mod_name else 'PSK')
        
    def test_classifier_8psk(self):
        self._test_class('8PSK')
        
    def test_classifier_16qam(self):
        self._test_class('16QAM')

if __name__ == '__main__':
    unittest.main()
