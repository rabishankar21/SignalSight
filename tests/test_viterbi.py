import unittest
import numpy as np
from signalsight.demod.viterbi import ViterbiDecoder, encode

class TestViterbi(unittest.TestCase):
    def setUp(self):
        self.decoder = ViterbiDecoder(k=7, polys=(0o171, 0o133))

    def test_error_free_decoding(self):
        # Generate random bits
        np.random.seed(42)
        original_bits = np.random.randint(0, 2, 1000).astype(np.uint8)
        
        # Encode
        encoded_bits = encode(original_bits)
        
        # Decode
        recovered_bits = self.decoder.decode(encoded_bits)
        
        # Verify
        np.testing.assert_array_equal(original_bits, recovered_bits)

    def test_single_bit_error(self):
        np.random.seed(42)
        original_bits = np.random.randint(0, 2, 1000).astype(np.uint8)
        encoded_bits = encode(original_bits)
        
        # Inject one error
        encoded_bits[500] ^= 1
        
        recovered_bits = self.decoder.decode(encoded_bits)
        np.testing.assert_array_equal(original_bits, recovered_bits)

    def test_multiple_bit_errors(self):
        np.random.seed(42)
        original_bits = np.random.randint(0, 2, 1000).astype(np.uint8)
        encoded_bits = encode(original_bits)
        
        # Inject ~5% random errors
        errors = (np.random.rand(len(encoded_bits)) < 0.05).astype(np.uint8)
        received_bits = encoded_bits ^ errors
        
        recovered_bits = self.decoder.decode(received_bits)
        
        # With 5% BER in hard decision, Viterbi K=7 should recover with 0 or very few errors
        ber = np.mean(original_bits != recovered_bits)
        self.assertLess(ber, 0.005) # Should correct almost everything

    def test_short_sequence(self):
        original_bits = np.array([1, 0, 1, 1, 0], dtype=np.uint8)
        encoded_bits = encode(original_bits)
        recovered_bits = self.decoder.decode(encoded_bits)
        np.testing.assert_array_equal(original_bits, recovered_bits)
        
    def test_decode_auto_phase(self):
        np.random.seed(42)
        original_bits = np.random.randint(0, 2, 1000).astype(np.uint8)
        encoded_bits = encode(original_bits)
        
        # Phase 0
        decoded0, phase0 = self.decoder.decode_auto_phase(encoded_bits)
        self.assertEqual(phase0, 0)
        np.testing.assert_array_equal(original_bits, decoded0)
        
        # Phase 1
        encoded_bits_shifted = np.concatenate(([0], encoded_bits))
        decoded1, phase1 = self.decoder.decode_auto_phase(encoded_bits_shifted)
        self.assertEqual(phase1, 1)
        # It drops the first bit, decodes the rest, so it should match exactly
        np.testing.assert_array_equal(original_bits, decoded1)
        
        # Phase 1 with trailing incomplete pair
        encoded_bits_shifted2 = np.concatenate(([1], encoded_bits, [0]))
        decoded2, phase2 = self.decoder.decode_auto_phase(encoded_bits_shifted2)
        self.assertEqual(phase2, 1)
        np.testing.assert_array_equal(original_bits, decoded2)
        
    def test_odd_length_input(self):
        # Rate 1/2 requires even length array
        encoded = np.array([1, 0, 1], dtype=np.uint8)
        with self.assertRaises(ValueError):
            self.decoder.decode(encoded)

if __name__ == '__main__':
    unittest.main()
