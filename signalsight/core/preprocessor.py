import numpy as np
import scipy.signal as signal
from typing import Optional

def preprocess(
    samples: np.ndarray,
    sample_rate: float,
    dc_remove: bool = True,
    normalize: bool = True,
    filter_bw: Optional[float] = None,
    filter_center: float = 0.0,
    resample_rate: Optional[float] = None,
) -> np.ndarray:
    """
    Preprocess complex IQ samples.
    Returns preprocessed complex numpy array.
    """
    out = samples.copy()
    
    # 1. DC removal
    if dc_remove:
        out = out - (np.mean(out.real) + 1j * np.mean(out.imag))
        
    # 2. Bandpass filter
    if filter_bw is not None:
        numtaps = 101
        nyq = 0.5 * sample_rate
        cutoff = filter_bw / 2.0 / nyq
        if cutoff >= 1.0: 
            cutoff = 0.99
            
        taps = signal.firwin(numtaps, cutoff)
        
        if filter_center != 0.0:
            t = np.arange(len(out))
            shift = np.exp(-1j * 2 * np.pi * filter_center * t / sample_rate)
            out = out * shift
            out = signal.lfilter(taps, 1.0, out)
            out = out * np.conj(shift)
        else:
            out = signal.lfilter(taps, 1.0, out)
            
    # 3. Resample
    if resample_rate is not None and resample_rate != sample_rate:
        import fractions
        frac = fractions.Fraction(resample_rate / sample_rate).limit_denominator(100)
        out = signal.resample_poly(out, frac.numerator, frac.denominator)
        
    # 4. Normalize
    if normalize:
        rms = np.sqrt(np.mean(np.abs(out)**2))
        if rms > 0:
            out = out / rms
            
    return out
