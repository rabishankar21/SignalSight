import numpy as np
import scipy.signal as signal
from typing import Tuple

def compute_psd(
    samples: np.ndarray,
    sample_rate: float,
    fft_size: int = 4096,
    window: str = 'blackmanharris',
    overlap_frac: float = 0.5,
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Compute Power Spectral Density using Welch's method.
    Returns (frequencies_hz, psd_db) where psd_db is in dBFS.
    frequencies should be centered (fftshift applied).
    """
    if len(samples) < fft_size:
        fft_size = len(samples)
        
    noverlap = int(fft_size * overlap_frac)
    freqs, psd = signal.welch(
        samples, fs=sample_rate, window=window, 
        nperseg=fft_size, noverlap=noverlap, 
        return_onesided=False
    )
    
    freqs = np.fft.fftshift(freqs)
    psd = np.fft.fftshift(psd)
    
    psd_db = 10 * np.log10(np.maximum(psd, 1e-12))
    psd_db = np.clip(psd_db, a_min=-120.0, a_max=None)
    
    return freqs, psd_db

def compute_spectrogram(
    samples: np.ndarray,
    sample_rate: float,
    fft_size: int = 1024,
    overlap_frac: float = 0.75,
    window: str = 'blackmanharris',
) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Compute spectrogram (waterfall data).
    Returns (times_sec, frequencies_hz, power_db_2d).
    power_db_2d shape: (num_freq_bins, num_time_bins)
    frequencies should be centered (fftshift applied).
    """
    if len(samples) < fft_size:
        fft_size = len(samples)
        
    noverlap = int(fft_size * overlap_frac)
    freqs, times, Sxx = signal.spectrogram(
        samples, fs=sample_rate, window=window,
        nperseg=fft_size, noverlap=noverlap,
        return_onesided=False, mode='psd'
    )
    
    freqs = np.fft.fftshift(freqs)
    Sxx = np.fft.fftshift(Sxx, axes=0)
    
    power_db = 10 * np.log10(np.maximum(Sxx, 1e-12))
    power_db = np.clip(power_db, a_min=-120.0, a_max=None)
    
    return times, freqs, power_db
