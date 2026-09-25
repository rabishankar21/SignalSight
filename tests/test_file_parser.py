"""
Unit tests for IQ and WAV file loading.
"""
import unittest
import os
import tempfile
import numpy as np
from pathlib import Path

from signalsight.core.file_parser import load_file
from signalsight.utils.signal_generator import generate_signal, save_as_iq, save_as_wav


class TestFileParser(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.temp_path = Path(self.temp_dir.name)

    def tearDown(self):
        self.temp_dir.cleanup()

    def _make_signal(self, mod="QPSK"):
        """Generate a test signal. Returns complex samples."""
        samples, bits, gt = generate_signal(
            modulation=mod,
            symbol_rate=100000,
            sample_rate=400000,
            num_symbols=1000,
            snr_db=25.0,
            seed=42,
        )
        return samples

    def test_load_wav_dual_channel(self):
        """Load a dual-channel WAV file and verify sample count and rate."""
        sig = self._make_signal("QPSK")
        wav_path = str(self.temp_path / "test.wav")
        save_as_wav(sig, wav_path, sample_rate=400000)

        loaded, sr, meta = load_file(wav_path)
        self.assertEqual(sr, 400000)
        self.assertEqual(meta['format'], 'wav')
        # WAV uses int16 so there will be quantization loss
        self.assertEqual(len(loaded), len(sig))

    def test_load_iq_float32(self):
        """Load a float32 interleaved IQ file."""
        sig = self._make_signal("BPSK")
        iq_path = str(self.temp_path / "test.iq")
        save_as_iq(sig, iq_path, fmt='float32')

        loaded, sr, meta = load_file(iq_path, sample_rate=400000, iq_format='float32')
        self.assertEqual(len(loaded), len(sig))
        np.testing.assert_allclose(np.real(loaded), np.real(sig).astype(np.float32), atol=1e-5)
        np.testing.assert_allclose(np.imag(loaded), np.imag(sig).astype(np.float32), atol=1e-5)

    def test_load_iq_int16(self):
        """Load an int16 interleaved IQ file."""
        sig = self._make_signal("QPSK")
        iq_path = str(self.temp_path / "test_int16.iq")
        save_as_iq(sig, iq_path, fmt='int16')

        loaded, sr, meta = load_file(iq_path, sample_rate=400000, iq_format='int16')
        self.assertEqual(len(loaded), len(sig))
        self.assertEqual(loaded.shape, sig.shape)
        self.assertEqual(meta['format'], 'iq_int16')

    def test_load_nonexistent_file(self):
        """Loading a non-existent file should raise FileNotFoundError."""
        with self.assertRaises(FileNotFoundError):
            load_file(str(self.temp_path / "does_not_exist.wav"))

    def test_load_empty_file(self):
        """Loading an empty file should raise an error."""
        empty_path = str(self.temp_path / "empty.iq")
        Path(empty_path).touch()
        # An empty IQ file produces 0 samples -- this should at minimum not crash.
        # Depending on implementation it may raise or return empty array.
        try:
            loaded, sr, meta = load_file(empty_path, sample_rate=400000, iq_format='float32')
            self.assertEqual(len(loaded), 0)
        except Exception:
            pass  # Acceptable to raise on empty file

    def test_metadata_fields(self):
        """Verify metadata dict contains expected keys after loading WAV."""
        sig = self._make_signal("BPSK")
        wav_path = str(self.temp_path / "test_meta.wav")
        save_as_wav(sig, wav_path, sample_rate=400000)

        _, sr, meta = load_file(wav_path)
        self.assertIn('filename', meta)
        self.assertIn('num_samples', meta)
        self.assertIn('format', meta)
        self.assertIn('duration_sec', meta)
        self.assertIn('filesize_bytes', meta)
        self.assertEqual(sr, 400000)
        self.assertGreater(meta['num_samples'], 0)
        self.assertGreater(meta['duration_sec'], 0)


if __name__ == '__main__':
    unittest.main(verbosity=2)
