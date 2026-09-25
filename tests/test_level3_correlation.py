import unittest
import numpy as np
from signalsight.bitstream.correlator import (
    autocorrelate, find_sync_word, detect_repeated_pattern,
    detect_frame_boundaries, correlate_patterns
)

class TestLevel3Correlation(unittest.TestCase):
    def setUp(self):
        self.sync_word = np.array([1,0,1,0,1,0,1,1,1,0,0,0,1,1,0,1], dtype=np.uint8)
        self.payload = np.random.randint(0, 2, 100).astype(np.uint8)
        self.frame = np.concatenate([self.sync_word, self.payload])
        self.bits = np.tile(self.frame, 5) # 5 frames

    def test_sync_word(self):
        matches = find_sync_word(self.bits, self.sync_word, threshold=0.9)
        self.assertEqual(len(matches), 5)
        self.assertEqual(matches[0]['offset'], 0)

    def test_repeated_pattern(self):
        patterns = detect_repeated_pattern(self.bits, min_period=10, max_period=200)
        self.assertTrue(len(patterns) > 0)
        self.assertEqual(patterns[0]['period'], len(self.frame))

    def test_frame_boundaries(self):
        res = detect_frame_boundaries(self.bits, self.sync_word)
        self.assertEqual(res['frame_length'], len(self.frame))
        self.assertEqual(res['method'], 'sync_word')

if __name__ == '__main__':
    unittest.main()
