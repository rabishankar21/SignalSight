import unittest
import numpy as np
from signalsight.interleave.block import block_interleave, block_deinterleave

class TestBlockInterleave(unittest.TestCase):
    
    def test_interleave_deinterleave_exact_block(self):
        bits = np.array([1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12])
        # 3 rows, 4 cols
        # Matrix:
        # [1, 2, 3, 4]
        # [5, 6, 7, 8]
        # [9, 10, 11, 12]
        # Interleaved (read cols): 1, 5, 9, 2, 6, 10, 3, 7, 11, 4, 8, 12
        
        interleaved = block_interleave(bits, 3, 4)
        expected = np.array([1, 5, 9, 2, 6, 10, 3, 7, 11, 4, 8, 12])
        np.testing.assert_array_equal(interleaved, expected)
        
        deinterleaved = block_deinterleave(interleaved, 3, 4)
        np.testing.assert_array_equal(deinterleaved, bits)
        
    def test_multiple_blocks(self):
        bits = np.arange(24)
        interleaved = block_interleave(bits, 3, 4)
        deinterleaved = block_deinterleave(interleaved, 3, 4)
        np.testing.assert_array_equal(deinterleaved, bits)
        
    def test_tail_bits(self):
        bits = np.arange(14) # 12 + 2 tail bits
        interleaved = block_interleave(bits, 3, 4)
        deinterleaved = block_deinterleave(interleaved, 3, 4)
        np.testing.assert_array_equal(deinterleaved, bits)
        
        # Check that tail bits are unmodified
        np.testing.assert_array_equal(interleaved[-2:], bits[-2:])
        
    def test_simulated_channel_burst_error(self):
        # We will simulate a burst error and show that interleaving spreads it out
        bits = np.zeros(100, dtype=np.uint8)
        
        interleaved = block_interleave(bits, 10, 10)
        
        # Burst error of length 5
        interleaved[20:25] = 1
        
        # Deinterleave
        recovered = block_deinterleave(interleaved, 10, 10)
        
        # Now the errors should be spread out, not contiguous
        error_indices = np.where(recovered == 1)[0]
        self.assertEqual(len(error_indices), 5)
        
        # Check that they are spread by at least the row size (10)
        diffs = np.diff(error_indices)
        for d in diffs:
            self.assertEqual(d, 10)

if __name__ == '__main__':
    unittest.main()
