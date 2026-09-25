import unittest
import os
import numpy as np
from signalsight.utils.signal_generator import save_as_wav_mono, save_as_wav
from signalsight.core.file_parser import load_file

class TestLevel3Wav(unittest.TestCase):
    def setUp(self):
        self.samples = (np.random.randn(1000) + 1j*np.random.randn(1000)).astype(np.complex64)
        self.sample_rate = 48000.0
        self.mono_path = "test_mono.wav"
        self.stereo_path = "test_stereo.wav"

    def tearDown(self):
        if os.path.exists(self.mono_path): os.remove(self.mono_path)
        if os.path.exists(self.stereo_path): os.remove(self.stereo_path)

    def test_mono_wav(self):
        save_as_wav_mono(self.samples, self.mono_path, self.sample_rate)
        s, sr, meta = load_file(self.mono_path)
        self.assertEqual(sr, self.sample_rate)
        self.assertEqual(meta['format'], 'wav')
        self.assertEqual(len(s), len(self.samples))

    def test_stereo_wav(self):
        save_as_wav(self.samples, self.stereo_path, self.sample_rate)
        s, sr, meta = load_file(self.stereo_path)
        self.assertEqual(sr, self.sample_rate)
        self.assertEqual(meta['format'], 'wav')
        self.assertEqual(len(s), len(self.samples))

if __name__ == '__main__':
    unittest.main()
