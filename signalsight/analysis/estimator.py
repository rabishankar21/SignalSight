import numpy as np
import scipy.signal as signal
from typing import Tuple

def estimate_bandwidth(
    frequencies: np.ndarray,
    psd_db: np.ndarray,
    threshold_db: float = 6.0,
) -> Tuple[float, float, float]:
    """
    Estimate signal bandwidth from PSD.
    Returns (bandwidth_hz, lower_freq_hz, upper_freq_hz).
    Method: -10 dB bandwidth relative to peak, bounded by noise floor, using smoothed PSD.
    """
    # Smooth the PSD to prevent noise fragmentation
    smoothed_psd = signal.medfilt(psd_db, kernel_size=21)
    
    noise_floor = np.median(smoothed_psd)
    peak_psd = np.max(smoothed_psd)
    
    snr_est_rough = peak_psd - noise_floor
    if snr_est_rough < 3.0:
        threshold = noise_floor + snr_est_rough * 0.5
    else:
        # Standard -10dB bandwidth, but bound it to be at least 3dB above noise floor
        threshold = max(noise_floor + 3.0, peak_psd - 10.0)
    
    above_thresh = smoothed_psd > threshold
    
    from itertools import groupby
    regions = []
    start = 0
    for k, g in groupby(above_thresh):
        length = len(list(g))
        if k:
            regions.append((start, start+length))
        start += length
        
    if not regions:
        return 0.0, frequencies[0], frequencies[-1]
        
    largest_region = max(regions, key=lambda x: x[1] - x[0])
    idx_start, idx_end = largest_region
    idx_end = min(idx_end, len(frequencies)-1)
    
    lower_freq = frequencies[idx_start]
    upper_freq = frequencies[idx_end]
    bw = upper_freq - lower_freq
    
    return bw, lower_freq, upper_freq

def estimate_snr(
    samples: np.ndarray,
    sample_rate: float,
    signal_bandwidth: float,
) -> float:
    """
    Estimate SNR in dB.
    Method: compute power in signal bandwidth vs power outside signal bandwidth.
    Uses proper density interpolation to separate in-band noise from signal power.
    """
    from .spectral import compute_psd
    freqs, psd_db = compute_psd(samples, sample_rate, fft_size=1024)
    psd_lin = 10**(psd_db / 10.0)
    
    center_idx = len(freqs)//2
    bw_bins = int((signal_bandwidth / sample_rate) * len(freqs))
    half_bw = max(1, bw_bins // 2)
    
    idx_min = max(0, center_idx - half_bw)
    idx_max = min(len(freqs), center_idx + half_bw)
    
    p_in = np.sum(psd_lin[idx_min:idx_max])
    p_total = np.sum(psd_lin)
    p_out = p_total - p_in
    
    frac_out = (len(freqs) - (idx_max - idx_min)) / len(freqs)
    frac_in = (idx_max - idx_min) / len(freqs)
    
    # Avoid divide by zero if signal occupies entire band
    if frac_out < 0.05:
        total_noise = np.median(psd_lin) * len(freqs)
    else:
        total_noise = p_out / frac_out
        
    in_band_noise = total_noise * frac_in
    signal_power = max(1e-12, p_in - in_band_noise)
    
    snr = 10 * np.log10(signal_power / total_noise)
    return snr

def estimate_symbol_rate(
    samples: np.ndarray,
    sample_rate: float,
) -> Tuple[float, float]:
    """
    Estimate symbol rate using spectral analysis of |x|^2 and |x|^4.
    Returns (estimated_symbol_rate_hz, confidence).
    """
    def process_power(p: int):
        x = np.abs(samples)**p
        x -= np.mean(x)
        N = min(8192, len(x))
        X = np.abs(np.fft.fft(x[:N]))
        X = X[:N//2]
        freqs = np.fft.fftfreq(N, 1/sample_rate)[:N//2]
        
        cutoff = int(N * 0.01)
        X[:cutoff] = 0
        
        peaks, props = signal.find_peaks(X, prominence=0)
        if len(peaks) == 0:
            return 0.0, 0.0
            
        max_idx = np.argmax(props['prominences'])
        best_peak = peaks[max_idx]
        prominence = props['prominences'][max_idx]
        return freqs[best_peak], prominence
        
    rate2, prom2 = process_power(2)
    rate4, prom4 = process_power(4)
    
    if prom4 > prom2 * 1.5:
        max_prom = prom4
        rate = rate4
    else:
        max_prom = prom2
        rate = rate2
        
    # Arbitrary normalization for confidence in MVP
    sig_power = np.max(np.abs(samples)**2 * len(samples))
    conf = min(1.0, max_prom / (sig_power + 1e-12))
    return rate, 0.5 + 0.5*conf
