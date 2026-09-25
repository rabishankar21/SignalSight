import unittest
import numpy as np
from signalsight.fec.ldpc import LDPCCodec
from signalsight.fec.concatenated import ConcatenatedFEC
from signalsight.analysis.fec_detector import detect_fec
from signalsight.analysis.interleaver_detector import detect_interleaver

class TestLevel3FEC(unittest.TestCase):
    def setUp(self):
        self.bits = np.random.randint(0, 2, 512).astype(np.uint8)

    def test_ldpc(self):
        ldpc = LDPCCodec()
        enc = ldpc.encode_bits(self.bits)
        errs = np.zeros(len(enc), dtype=np.uint8)
        errs[10] = 1; errs[20] = 1 # add errors
        dec = ldpc.decode_bits(enc ^ errs)
        self.assertTrue(np.array_equal(self.bits, dec))

    def test_concatenated(self):
        cfec = ConcatenatedFEC()
        enc = cfec.encode(self.bits)
        dec = cfec.decode(enc)
        self.assertTrue(dec['success'])
        min_len = min(len(self.bits), len(dec['decoded_bits']))
        self.assertTrue(np.array_equal(self.bits[:min_len], dec['decoded_bits'][:min_len]))

    def test_fec_detector(self):
        ldpc = LDPCCodec()
        enc = ldpc.encode_bits(self.bits)
        candidates = detect_fec(enc)
        self.assertTrue(len(candidates) > 0)

if __name__ == '__main__':
    unittest.main()
