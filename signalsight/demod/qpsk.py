"""
QPSK demodulator with carrier recovery, timing recovery, and bit extraction.
"""
import numpy as np
from .bpsk import design_rrc_filter, _gardner_timing_recovery, _cubic_interp


def _estimate_freq_offset_qpsk(samples: np.ndarray, sample_rate: float) -> float:
    """
    Estimate carrier frequency offset for QPSK using the 4th power method.
    x^4 removes QPSK modulation, leaving a tone at 4*f_offset.
    """
    x4 = samples ** 4

    N = len(x4)
    fft_val = np.fft.fft(x4)
    fft_freq = np.fft.fftfreq(N, d=1.0 / sample_rate)

    peak_idx = np.argmax(np.abs(fft_val))
    f_offset = fft_freq[peak_idx] / 4.0
    return f_offset


def _costas_loop_qpsk(symbols: np.ndarray) -> tuple:
    """
    Decision-directed Costas loop for QPSK carrier phase/frequency tracking.
    
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

        # Decision-directed error for QPSK:
        # Nearest QPSK constellation point
        dec_i = 1.0 if np.real(corrected) > 0 else -1.0
        dec_q = 1.0 if np.imag(corrected) > 0 else -1.0
        decision = (dec_i + 1j * dec_q) / np.sqrt(2)

        # Phase error = Im(corrected * conj(decision))
        err = np.imag(corrected * np.conj(decision))

        # Loop filter
        freq += beta * err
        phase += alpha * err + freq

    return out, phase


def demodulate_qpsk(
    samples: np.ndarray,
    sample_rate: float,
    symbol_rate: float,
    rolloff: float = 0.35,
) -> dict:
    """
    Demodulate QPSK signal.
    
    Pipeline:
        1. RRC matched filter
        2. Coarse frequency offset correction (4th power method)
        3. Gardner timing recovery (symbol synchronization)
        4. Decision-directed Costas loop (fine carrier recovery)
        5. Quadrant hard decision + Gray demapping
    
    Returns dict with:
        'bits': np.ndarray of 0s and 1s (2 bits per symbol, flat)
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
    f_offset = _estimate_freq_offset_qpsk(rx, sample_rate)
    t_arr = np.arange(len(rx)) / sample_rate
    rx = rx * np.exp(-1j * 2 * np.pi * f_offset * t_arr)

    # 3. Gardner Timing Recovery (reuse from bpsk module)
    symbols_sync = _gardner_timing_recovery(rx, sps)

    # 4. Costas Loop (decision-directed for QPSK)
    symbols_fine, final_phase = _costas_loop_qpsk(symbols_sync)

    # 5. Hard decision + Gray-coded demapping
    # QPSK constellation (Gray coded):
    #   Q1 (+I, +Q) -> 00
    #   Q2 (-I, +Q) -> 01
    #   Q3 (-I, -Q) -> 11
    #   Q4 (+I, -Q) -> 10
    bits = np.zeros(len(symbols_fine) * 2, dtype=np.uint8)
    for i in range(len(symbols_fine)):
        re = np.real(symbols_fine[i])
        im = np.imag(symbols_fine[i])

        if re > 0 and im > 0:      # Q1
            b0, b1 = 0, 0
        elif re < 0 and im > 0:    # Q2
            b0, b1 = 0, 1
        elif re < 0 and im < 0:    # Q3
            b0, b1 = 1, 1
        else:                       # Q4
            b0, b1 = 1, 0

        bits[2 * i] = b0
        bits[2 * i + 1] = b1

    return {
        'bits': bits,
        'symbols': symbols_fine,
        'constellation': symbols_fine,
        'num_symbols': len(symbols_fine),
        'num_bits': len(bits),
        'carrier_freq_offset': float(f_offset),
        'phase_offset': float(final_phase),
    }
