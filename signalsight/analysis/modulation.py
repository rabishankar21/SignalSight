"""
DSP-based modulation classification using higher-order cumulants
and signal envelope properties.
"""
import numpy as np
from typing import List, Dict, Optional


def compute_cumulants(samples: np.ndarray) -> Dict[str, complex]:
    """
    Compute 2nd and 4th order cumulants of complex samples.
    Samples are normalized to unit power before computation.
    
    Returns dict with keys: 'C20', 'C21', 'C40', 'C41', 'C42'
    """
    # Normalize to unit power
    power = np.mean(np.abs(samples) ** 2)
    if power > 0:
        x = samples / np.sqrt(power)
    else:
        x = samples.copy()

    # 2nd order moments
    M20 = np.mean(x ** 2)
    M21 = np.mean(np.abs(x) ** 2)  # Should be ~1 after normalization

    # 4th order moments
    M40 = np.mean(x ** 4)
    M41 = np.mean((np.abs(x) ** 2) * (x ** 2))
    M42 = np.mean(np.abs(x) ** 4)

    # Cumulants (moment-to-cumulant conversion)
    C20 = M20
    C21 = M21
    C40 = M40 - 3 * M20 ** 2
    C41 = M41 - 3 * M20 * M21
    C42 = M42 - np.abs(M20) ** 2 - 2 * M21 ** 2

    return {
        'C20': C20,
        'C21': C21,
        'C40': C40,
        'C41': C41,
        'C42': C42,
    }


def classify_modulation(
    samples: np.ndarray,
    sample_rate: float,
    symbol_rate: Optional[float] = None,
) -> List[Dict]:
    """
    Classify modulation type using DSP features (higher-order cumulants
    and instantaneous frequency analysis).
    
    Returns ranked list of candidates:
        [{'type': 'QPSK', 'confidence': 0.85}, ...]
    
    Supported types: BPSK, QPSK, 8PSK, 2FSK, 4FSK, 16QAM
    """
    # Normalize to unit power
    power = np.mean(np.abs(samples) ** 2)
    if power > 0:
        x = samples / np.sqrt(power)
    else:
        return [{'type': 'Unknown', 'confidence': 0.0}]

    # ----- Feature 1: Envelope statistics -----
    env = np.abs(x)
    env_mean = np.mean(env)
    env_std = np.std(env)
    # Coefficient of variation (std / mean)
    # For constant-envelope signals (PSK, FSK) after RRC pulse shaping,
    # this is typically 0.1-0.3. For QAM, it's typically 0.3-0.6.
    env_cv = env_std / env_mean if env_mean > 0 else 0

    # ----- Feature 2: Instantaneous frequency analysis for FSK detection -----
    inst_phase = np.unwrap(np.angle(x))
    inst_freq = np.diff(inst_phase) * sample_rate / (2 * np.pi)

    # Check if instantaneous frequency clusters into discrete levels
    # FSK has discrete freq levels; PSK/QAM have continuous inst. freq distribution
    iq_std = np.std(inst_freq)
    iq_median = np.median(np.abs(inst_freq - np.mean(inst_freq)))

    # Kurtosis of instantaneous frequency: FSK has high kurtosis (peaky histogram)
    from scipy.stats import kurtosis as scipy_kurtosis
    try:
        iq_kurtosis = scipy_kurtosis(inst_freq, fisher=True)
    except Exception:
        iq_kurtosis = 0.0

    # ----- Feature 3: Higher-order cumulants and Circular Phase Concentration -----
    # If symbol_rate is available, we can decimate to optimal symbol instants
    # to bypass the statistical smearing caused by the RRC filter.
    if symbol_rate and symbol_rate > 0 and sample_rate >= symbol_rate * 2:
        sps = int(np.round(sample_rate / symbol_rate))
        # Find optimal symbol sampling phase by maximum energy
        energies = [np.sum(np.abs(x[i::sps])**2) for i in range(sps)]
        best_offset = np.argmax(energies)
        syms = x[best_offset::sps]
    else:
        syms = x  # Fallback to raw samples if no symbol rate is provided

    # Normalize symbols for cumulant computation
    sym_power = np.mean(np.abs(syms)**2)
    if sym_power > 0:
        syms_norm = syms / np.sqrt(sym_power)
    else:
        syms_norm = syms

    # Compute traditional cumulants on symbols
    cumulants = compute_cumulants(syms_norm)
    C40_mag = np.abs(cumulants['C40'])
    C42_mag = np.abs(cumulants['C42'])

    # Circular phase concentration via FFT to bypass carrier offset
    # syms**2 collapses BPSK phase states; syms**4 collapses QPSK phase states.
    # The max FFT magnitude represents the degree of concentration (R2, R4).
    # This is incredibly robust to AWGN compared to cumulants.
    if len(syms_norm) > 16:
        R2 = np.max(np.abs(np.fft.fft(syms_norm**2))) / len(syms_norm)
        R4 = np.max(np.abs(np.fft.fft(syms_norm**4))) / len(syms_norm)
    else:
        R2 = 0.0
        R4 = 0.0

    candidates = []

    # ----- Step 1: Check for FSK -----
    is_fsk = False
    if env_cv < 0.15 and iq_kurtosis < 1.0:
        hist, bin_edges = np.histogram(inst_freq, bins=100)
        peak_threshold = np.max(hist) * 0.3
        peaks = []
        for i in range(1, len(hist) - 1):
            if hist[i] > peak_threshold and hist[i] >= hist[i-1] and hist[i] >= hist[i+1]:
                peaks.append(i)

        if len(peaks) > 0:
            is_fsk = True
            if len(peaks) >= 3:
                candidates.append({'type': '4FSK', 'confidence': 0.85})
                candidates.append({'type': '2FSK', 'confidence': 0.15})
            else:
                candidates.append({'type': '2FSK', 'confidence': 0.85})
                candidates.append({'type': '4FSK', 'confidence': 0.15})

    if not is_fsk:
        # ----- Step 2: Distinguish PSK vs QAM using R2/R4 and Cumulants -----

        # BPSK: R2 is extremely high (usually >0.5 even at low SNR)
        # We use a logistic-like distance metric mapped to R2
        dist_bpsk = max(0, 1.0 - R2)
        conf_bpsk = 1.0 / (1.0 + 3.0 * dist_bpsk)
        candidates.append({'type': 'BPSK', 'confidence': float(conf_bpsk)})

        # QPSK: R2 is near 0, but R4 is high.
        # Penalize if R2 is high (meaning it's BPSK) or env_cv is high (meaning it's QAM).
        sym_env = np.abs(syms_norm)
        sym_env_cv = np.std(sym_env) / np.mean(sym_env) if np.mean(sym_env) > 0 else 0
        
        dist_qpsk = max(0, 1.0 - R4) + R2 * 2.0
        penalty_qpsk = 2.0 if sym_env_cv > 0.32 else 0.0
        conf_qpsk = 1.0 / (1.0 + 3.0 * dist_qpsk + penalty_qpsk)
        candidates.append({'type': 'QPSK', 'confidence': float(conf_qpsk)})

        # 8PSK: R4 is low, R8 would be high. Both R2 and R4 are low.
        dist_8psk = R2 + R4
        penalty_8psk = 2.0 if sym_env_cv > 0.32 else 0.0
        conf_8psk = 1.0 / (1.0 + 3.0 * dist_8psk + 0.5 + penalty_8psk)
        candidates.append({'type': '8PSK', 'confidence': float(conf_8psk)})

        # 16QAM: R4 is moderately high, but envelope CV is higher (since it's QAM)
        dist_16qam = np.sqrt((C40_mag - 0.68)**2 + (C42_mag - 0.68)**2)
        # Increase confidence if envelope CV indicates amplitude variations
        penalty_16qam = 2.0 if sym_env_cv < 0.32 else 0.5
        conf_16qam = 1.0 / (1.0 + 3.0 * dist_16qam + penalty_16qam)
        candidates.append({'type': '16QAM', 'confidence': float(conf_16qam)})

        # 64QAM: Higher envelope variation than 16QAM, different cumulant profile
        dist_64qam = np.sqrt((C40_mag - 0.62)**2 + (C42_mag - 0.62)**2)
        penalty_64qam = 1.5 if sym_env_cv < 0.32 else 0.3
        conf_64qam = 1.0 / (1.0 + 3.0 * dist_64qam + penalty_64qam)
        candidates.append({'type': '64QAM', 'confidence': float(conf_64qam)})

    # Add family field to all candidates
    family_map = {'BPSK': 'PSK', 'QPSK': 'PSK', '8PSK': 'PSK',
                  '2FSK': 'FSK', '4FSK': 'FSK',
                  '16QAM': 'QAM', '64QAM': 'QAM', 'Unknown': 'Unknown'}
    for c in candidates:
        c['family'] = family_map.get(c['type'], 'Unknown')

    # Sort by confidence descending
    candidates.sort(key=lambda c: c['confidence'], reverse=True)

    return candidates
