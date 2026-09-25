import unittest
import numpy as np
from signalsight.core.pipeline import run_pipeline
from signalsight.utils.signal_generator import generate_signal

class TestLevel3Pipeline(unittest.TestCase):
    def test_end_to_end_pipeline(self):
        # Generate clean QPSK
        samples, bits, _ = generate_signal('QPSK', 100000, 400000, 1000, snr_db=30.0, seed=42)
        
        config = {
            'modulation': 'auto',
            'fec': 'none',
            'interleaver': 'none'
        }
        
        results = run_pipeline(samples, 400000.0, config)
        
        self.assertIn('classification', results)
        self.assertEqual(results['classification']['modulation'], 'QPSK')
        
        self.assertIn('demodulation', results)
        self.assertTrue(results['output']['recovered_bits'] > 0)

if __name__ == '__main__':
    unittest.main()
