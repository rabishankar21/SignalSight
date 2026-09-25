import unittest
import numpy as np
from signalsight.interleave.convolutional import convolutional_interleave, convolutional_deinterleave
from signalsight.interleave.diagonal import diagonal_interleave, diagonal_deinterleave
from signalsight.interleave.pseudo_random import pseudo_random_interleave, pseudo_random_deinterleave

class TestLevel3Deinterleaving(unittest.TestCase):
    def setUp(self):
        self.bits = np.random.randint(0, 2, 2000).astype(np.uint8)

    def test_convolutional(self):
        b, d = 4, 3
        delay_syms = b * (b - 1) * d
        int_c = convolutional_interleave(self.bits, b, d)
        deint_c = convolutional_deinterleave(int_c, b, d)
        trim_c = deint_c[delay_syms:delay_syms+len(self.bits)]
        self.assertTrue(np.array_equal(self.bits, trim_c))

    def test_diagonal(self):
        int_d = diagonal_interleave(self.bits, 10, 10)
        deint_d = diagonal_deinterleave(int_d, 10, 10)
        self.assertTrue(np.array_equal(self.bits, deint_d[:len(self.bits)]))

    def test_pseudo_random(self):
        int_pr = pseudo_random_interleave(self.bits, 100, 42)
        deint_pr = pseudo_random_deinterleave(int_pr, 100, 42)
        self.assertTrue(np.array_equal(self.bits, deint_pr[:len(self.bits)]))

if __name__ == '__main__':
    unittest.main()
