"""
BPSK demodulator with carrier recovery, timing recovery, and bit extraction.
"""
import numpy as np
from scipy import signal


def design_rrc_filter(rolloff: float, span_symbols: int, sps: int) -> np.ndarray:
    """
    Design root-raised-cosine filter.
    
    Args:
        rolloff: Roll-off factor (0 to 1)
        span_symbols: Filter span in symbol periods
        sps: Samples per symbol
    
    Returns:
        Filter coefficients (normalized to unit energy)
    """
    num_taps = span_symbols * sps + 1
    t = (np.arange(num_taps) - (num_taps - 1) / 2) / sps

    h = np.zeros(num_taps, dtype=float)
    for i in range(num_taps):
        ti = t[i]
        if ti == 0.0:
            h[i] = 1.0 - rolloff + (4 * rolloff / np.pi)
        elif rolloff > 0 and abs(abs(ti) - 1.0 / (4 * rolloff)) < 1e-8:
            h[i] = (rolloff / np.sqrt(2)) * (
                (1 + 2 / np.pi) * np.sin(np.pi / (4 * rolloff)) +
                (1 - 2 / np.pi) * np.cos(np.pi / (4 * rolloff))
            )
        else:
            denom = np.pi * ti * (1 - (4 * rolloff * ti) ** 2)
            if abs(denom) < 1e-12:
                h[i] = 1.0
            else:
                h[i] = (
                    np.sin(np.pi * ti * (1 - rolloff)) +
                    4 * rolloff * ti * np.cos(np.pi * ti * (1 + rolloff))
                ) / denom

    # Normalize to unit energy
    h = h / np.sqrt(np.sum(h ** 2))
    return h


def _estimate_freq_offset_bpsk(samples: np.ndarray, sample_rate: float) -> float:
    """
    Estimate carrier frequency offset for BPSK using the squaring method.
    x^2 removes BPSK modulation, leaving a tone at 2*f_offset.
    """
    x2 = samples ** 2

    N = len(x2)
    fft_val = np.fft.fft(x2)
    fft_freq = np.fft.fftfreq(N, d=1.0 / sample_rate)

    peak_idx = np.argmax(np.abs(fft_val))
    f_offset = fft_freq[peak_idx] / 2.0
    return f_offset


def demodulate_bpsk(
    samples: np.ndarray,
    sample_rate: float,
    symbol_rate: float,
    rolloff: float = 0.35,
) -> dict:
    """
    Demodulate BPSK signal.
    
    Pipeline:
        1. RRC matched filter
        2. Coarse frequency offset correction (squaring method)
        3. Gardner timing recovery (symbol synchronization)
        4. Costas loop (fine carrier recovery)
        5. Hard decision + bit mapping
    
    Returns dict with:
        'bits': np.ndarray of 0s and 1s
        'symbols': np.ndarray of complex symbols
        'constellation': np.ndarray of complex symbols for plotting
        'num_symbols': int
        'num_bits': int
        'carrier_freq_offset': float (estimated Hz)
        'phase_offset': float (estimated radians)
    """
    sps = int(np.round(sample_rate / symbol_rate))
    if sps < 2:
        sps = 2

    # 1. RRC Matched Filter
    h_rrc = design_rrc_filter(rolloff, 10, sps)
    rx = np.convolve(samples, h_rrc, mode='same')

    # 2. Coarse frequency offset estimation and correction
    f_offset = _estimate_freq_offset_bpsk(rx, sample_rate)
    t_arr = np.arange(len(rx)) / sample_rate
    rx = rx * np.exp(-1j * 2 * np.pi * f_offset * t_arr)

    # 3. Gardner Timing Recovery
    symbols_sync = _gardner_timing_recovery(rx, sps)

    # 4. Costas Loop for fine carrier recovery
    symbols_fine, final_phase = _costas_loop_bpsk(symbols_sync)

    # 5. Hard decision: real > 0 -> bit 0, real < 0 -> bit 1
    bits = (np.real(symbols_fine) < 0).astype(np.uint8)

    return {
        'bits': bits,
        'symbols': symbols_fine,
        'constellation': symbols_fine,
        'num_symbols': len(symbols_fine),
        'num_bits': len(bits),
        'carrier_freq_offset': float(f_offset),
        'phase_offset': float(final_phase),
    }


def _gardner_timing_recovery(rx: np.ndarray, sps: int) -> np.ndarray:
    """
    Gardner Timing Error Detector (TED) for symbol synchronization.
    Uses a decimating loop with cubic interpolation.
    
    Args:
        rx: Input samples (complex)
        sps: Samples per symbol
    
    Returns:
        Symbol-rate samples at optimal timing instants
    """
    # Normalize input to ensure consistent loop gain
    pwr = np.mean(np.abs(rx)**2)
    if pwr > 0:
        rx = rx / np.sqrt(pwr)
        
    # Loop filter parameters (2nd order)
    loop_bw = 0.0  # Set to 0 to prevent wandering on synthetic signals without clock drift
    damping = 1.0
    if loop_bw > 0:
        theta = loop_bw / (damping + 0.25 / damping)
        alpha = (4 * damping * theta) / (1 + 2 * damping * theta + theta ** 2)
        beta = (4 * theta ** 2) / (1 + 2 * damping * theta + theta ** 2)
    else:
        alpha, beta = 0.0, 0.0

    # Output buffer
    max_syms = len(rx) // sps + 10
    symbols = np.zeros(max_syms, dtype=complex)
    out_idx = 0

    freq_err = 0.0
    mu = 0.0  # Fractional timing offset (0 to 1)
    idx = sps  # Start after one full symbol period

    while idx < len(rx) - sps - 2:
        # Cubic interpolation at current, midpoint, and previous symbol
        curr_pos = idx + mu
        mid_pos = curr_pos - sps / 2.0
        prev_pos = curr_pos - sps

        s_curr = _cubic_interp(rx, curr_pos)
        s_mid = _cubic_interp(rx, mid_pos)
        s_prev = _cubic_interp(rx, prev_pos)

        # Gardner timing error
        err = np.real(s_mid * (np.conj(s_prev) - np.conj(s_curr)))

        # Loop filter update
        freq_err += beta * err
        mu += alpha * err + freq_err

        # Store symbol
        symbols[out_idx] = s_curr
        out_idx += 1

        # Advance by one symbol period, adjusted by fractional offset
        idx += sps

        # If mu drifts too far, adjust the integer index
        while mu > 0.5:
            mu -= 1.0
            idx += 1
        while mu < -0.5:
            mu += 1.0
            idx -= 1

    return symbols[:out_idx]


def _cubic_interp(sig: np.ndarray, pos: float) -> complex:
    """Cubic interpolation of complex signal at fractional position."""
    i = int(np.floor(pos))
    mu = pos - i

    if i < 1 or i >= len(sig) - 2:
        i = max(0, min(i, len(sig) - 1))
        return sig[i]

    p0 = sig[i - 1]
    p1 = sig[i]
    p2 = sig[i + 1]
    p3 = sig[i + 2]

    # Catmull-Rom cubic spline
    return (p1 + 0.5 * mu * (
        p2 - p0 + mu * (
            2.0 * p0 - 5.0 * p1 + 4.0 * p2 - p3 + mu * (
                3.0 * (p1 - p2) + p3 - p0
            )
        )
    ))


def _costas_loop_bpsk(symbols: np.ndarray) -> tuple:
    """
    Costas loop for fine carrier phase/frequency tracking (BPSK).
    
    Args:
        symbols: Complex symbols from timing recovery
    
    Returns:
        (corrected_symbols, final_phase)
    """
    # Loop filter parameters
    loop_bw = 0.02
    damping = 0.707
    theta = loop_bw / (damping + 0.25 / damping)
    alpha = (4 * damping * theta) / (1 + 2 * damping * theta + theta ** 2)
    beta = (4 * theta ** 2) / (1 + 2 * damping * theta + theta ** 2)

    freq = 0.0
    phase = 0.0
    out = np.zeros_like(symbols)

    for i in range(len(symbols)):
        # Apply phase correction
        corrected = symbols[i] * np.exp(-1j * phase)
        out[i] = corrected

        # BPSK Costas error: sign(real) * imag
        err = np.sign(np.real(corrected)) * np.imag(corrected)

        # Loop filter
        freq += beta * err
        phase += alpha * err + freq

    return out, phase
