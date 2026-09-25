"""
8PSK demodulator with carrier recovery, timing recovery, and bit extraction.
"""
import numpy as np
from scipy import signal
from .bpsk import design_rrc_filter, _gardner_timing_recovery, _cubic_interp

def _estimate_freq_offset_8psk(samples: np.ndarray, sample_rate: float) -> float:
    """
    Estimate carrier frequency offset for 8PSK using the 8th power method.
    """
    x8 = samples ** 8

    N = len(x8)
    fft_val = np.fft.fft(x8)
    fft_freq = np.fft.fftfreq(N, d=1.0 / sample_rate)

    peak_idx = np.argmax(np.abs(fft_val))
    f_offset = fft_freq[peak_idx] / 8.0
    return f_offset

def _pll_8psk(symbols: np.ndarray) -> tuple:
    """
    Decision-directed PLL for 8PSK fine carrier phase/frequency tracking.
    """
    # Loop filter parameters
    loop_bw = 0.01
    damping = 0.707
    theta = loop_bw / (damping + 0.25 / damping)
    alpha = (4 * damping * theta) / (1 + 2 * damping * theta + theta ** 2)
    beta = (4 * theta ** 2) / (1 + 2 * damping * theta + theta ** 2)

    freq = 0.0
    phase = 0.0
    out = np.zeros_like(symbols)
    
    # 8PSK constellation points
    constellation = np.exp(1j * np.arange(8) * np.pi / 4.0)

    for i in range(len(symbols)):
        corrected = symbols[i] * np.exp(-1j * phase)
        out[i] = corrected

        # Find nearest constellation point
        distances = np.abs(corrected - constellation)
        nearest = constellation[np.argmin(distances)]

        # Decision-directed error
        err = np.imag(corrected * np.conj(nearest))

        # Loop filter
        freq += beta * err
        phase += alpha * err + freq

    return out, phase

def demodulate_8psk(
    samples: np.ndarray,
    sample_rate: float,
    symbol_rate: float,
    rolloff: float = 0.35,
) -> dict:
    """
    Demodulate 8PSK signal.
    """
    sps = int(np.round(sample_rate / symbol_rate))
    if sps < 2:
        sps = 2

    # 1. RRC Matched Filter
    h_rrc = design_rrc_filter(rolloff, 10, sps)
    rx = np.convolve(samples, h_rrc, mode='same')

    # 2. Coarse frequency offset estimation and correction
    f_offset = _estimate_freq_offset_8psk(rx, sample_rate)
    t_arr = np.arange(len(rx)) / sample_rate
    rx = rx * np.exp(-1j * 2 * np.pi * f_offset * t_arr)

    # 3. Gardner Timing Recovery
    symbols_sync = _gardner_timing_recovery(rx, sps)

    # 4. Decision-directed PLL
    symbols_fine, final_phase = _pll_8psk(symbols_sync)

    # 5. Gray-coded demapping
    constellation = np.exp(1j * np.arange(8) * np.pi / 4.0)
    # Map phase index to Gray code: 0->0, 1->1, 2->3, 3->2, 4->6, 5->7, 6->5, 7->4
    gray_map = np.array([0, 1, 3, 2, 6, 7, 5, 4], dtype=np.uint8)
    
    # Demap symbols to bits
    bits = np.zeros(len(symbols_fine) * 3, dtype=np.uint8)
    for i, sym in enumerate(symbols_fine):
        distances = np.abs(sym - constellation)
        idx = np.argmin(distances)
        val = gray_map[idx]
        bits[i*3] = (val >> 2) & 1
        bits[i*3+1] = (val >> 1) & 1
        bits[i*3+2] = val & 1

    return {
        'bits': bits,
        'symbols': symbols_fine,
        'constellation': symbols_fine,
        'num_symbols': len(symbols_fine),
        'num_bits': len(bits),
        'carrier_freq_offset': float(f_offset),
        'phase_offset': float(final_phase),
    }
