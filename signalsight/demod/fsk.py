"""
2FSK/4FSK demodulator using FM discriminator approach.
"""
import numpy as np
from scipy import signal

def demodulate_fsk(
    samples: np.ndarray,
    sample_rate: float,
    symbol_rate: float,
    num_tones: int = 2,
    rolloff: float = 0.35,
) -> dict:
    """
    Demodulate 2FSK/4FSK signal.
    """
    if num_tones not in (2, 4):
        raise ValueError("num_tones must be 2 or 4")

    sps = int(np.round(sample_rate / symbol_rate))
    if sps < 2:
        sps = 2

    # 1. Bandpass filter (optional, we'll skip or just use a simple one if needed)
    # 2. FM discriminator
    phase = np.unwrap(np.angle(samples))
    inst_freq = np.diff(phase) * sample_rate / (2 * np.pi)
    # Pad to keep length same
    inst_freq = np.append(inst_freq, inst_freq[-1])

    # 3. Low-pass filter the instantaneous frequency
    cutoff = symbol_rate / sample_rate
    num_taps = max(11, int(2 / cutoff) if cutoff > 0 else 11)
    if num_taps % 2 == 0:
        num_taps += 1
    lpf = signal.firwin(num_taps, cutoff)
    filtered_freq = signal.lfilter(lpf, 1.0, inst_freq)

    # 4. Decimate to symbol rate
    # Simple decimation: sample at optimal timing (assuming max variance or just center)
    # Better approach: find delay to center of symbols. Since this is simple, we take samples starting from num_taps//2 every sps.
    start_idx = num_taps // 2
    symbols = filtered_freq[start_idx::sps]
    
    # 5. Demapping
    mean_freq = np.mean(symbols)
    
    if num_tones == 2:
        # 2FSK
        bits = (symbols > mean_freq).astype(np.uint8)
    else:
        # 4FSK
        bits = np.zeros(len(symbols) * 2, dtype=np.uint8)
        std_freq = np.std(symbols)
        # 4 levels typically: -3, -1, 1, 3
        # Thresholds: -2, 0, 2 (scaled by spacing)
        # Using K-means or simple amplitude binning
        levels = np.sort(np.unique(np.round(symbols / (std_freq/2)))) # approximation
        # Let's map standard levels:
        # A simple approach: 
        # > mean_freq + threshold -> 3
        # mean_freq .. mean_freq+threshold -> 1
        # mean_freq-threshold .. mean_freq -> -1
        # < mean_freq-threshold -> -3
        
        # Determine threshold from symbol distribution or assume spacing
        # For a 4FSK signal, symbols are clustered in 4 groups.
        # Let's use percentile or sort.
        s_sorted = np.sort(symbols)
        L = len(s_sorted)
        t1 = (s_sorted[L//8] + s_sorted[3*L//8]) / 2 if L > 8 else mean_freq - std_freq
        t3 = (s_sorted[5*L//8] + s_sorted[7*L//8]) / 2 if L > 8 else mean_freq + std_freq
        t2 = mean_freq
        
        for i, sym in enumerate(symbols):
            if sym < t1:
                val = 0  # 00
            elif sym < t2:
                val = 1  # 01
            elif sym < t3:
                val = 2  # 10
            else:
                val = 3  # 11
            
            bits[i*2] = (val >> 1) & 1
            bits[i*2+1] = val & 1
            
    # For constellation plotting, treat frequency values as complex or real
    constellation = symbols + 0j

    return {
        'bits': bits,
        'symbols': symbols,
        'constellation': constellation,
        'num_symbols': len(symbols),
        'num_bits': len(bits),
        'carrier_freq_offset': float(mean_freq),
        'phase_offset': 0.0,
    }
