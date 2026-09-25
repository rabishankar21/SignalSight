import os
import numpy as np
import scipy.io.wavfile as wavfile
import scipy.signal as signal
from typing import Tuple, Dict, Optional

def load_file(filepath: str, sample_rate: Optional[float] = None, iq_format: str = 'auto') -> Tuple[np.ndarray, float, Dict]:
    """
    Load an IQ or WAV file.
    
    Args:
        filepath: Path to .iq or .wav file
        sample_rate: Sample rate in Hz (required for IQ files without metadata, extracted from WAV header)
        iq_format: For IQ files - 'float32', 'int16', 'complex64', 'auto'
    
    Returns:
        samples: Complex numpy array (complex64)
        sample_rate: float in Hz
        metadata: dict with keys like 'format', 'num_samples', 'duration_sec', 'filename', 'filesize_bytes'
    """
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"File not found: {filepath}")
        
    ext = os.path.splitext(filepath)[1].lower()
    filesize = os.path.getsize(filepath)
    
    metadata = {
        'filename': os.path.basename(filepath),
        'filesize_bytes': filesize,
        'format': 'unknown',
        'num_samples': 0,
        'duration_sec': 0.0
    }

    if ext == '.wav':
        rate, data = wavfile.read(filepath)
        metadata['format'] = 'wav'
        if data.ndim == 1:
            # 1 channel -> analytic signal
            samples = signal.hilbert(data)
        elif data.ndim == 2:
            # 2 channels -> I + jQ
            samples = data[:, 0] + 1j * data[:, 1]
        else:
            raise ValueError(f"Unsupported WAV channel count: {data.shape[1]}")
            
        samples = samples.astype(np.complex64)
        sample_rate = float(rate)
        
    elif ext in ['.iq', '.bin', '.raw']:
        if iq_format == 'auto':
            # float32 interleaved (I,Q,I,Q,...) is the most common SDR format.
            # complex64 is the same byte layout -- numpy just reads pairs natively.
            # Default to float32 interleaved as it's the explicit, safer choice.
            if filesize % 4 == 0:
                iq_format = 'float32'
            elif filesize % 2 == 0:
                iq_format = 'int16'
            else:
                iq_format = 'float32'
                
        if iq_format == 'float32':
            data = np.fromfile(filepath, dtype=np.float32)
            if len(data) % 2 != 0: data = data[:-1]
            samples = data[0::2] + 1j * data[1::2]
            metadata['format'] = 'iq_float32'
        elif iq_format == 'int16':
            data = np.fromfile(filepath, dtype=np.int16)
            if len(data) % 2 != 0: data = data[:-1]
            samples = (data[0::2] + 1j * data[1::2]).astype(np.complex64)
            samples /= 32768.0
            metadata['format'] = 'iq_int16'
        elif iq_format == 'complex64':
            samples = np.fromfile(filepath, dtype=np.complex64)
            metadata['format'] = 'iq_complex64'
        else:
            print(f"Warning: Unknown IQ format {iq_format}, falling back to complex64")
            samples = np.fromfile(filepath, dtype=np.complex64)
            metadata['format'] = 'iq_complex64'
            
        if sample_rate is None:
            sample_rate = 1.0 # Default fallback if not provided
            
    else:
        raise ValueError(f"Unsupported file extension: {ext}")
        
    metadata['num_samples'] = len(samples)
    metadata['duration_sec'] = len(samples) / float(sample_rate)
    
    return samples.astype(np.complex64), float(sample_rate), metadata
