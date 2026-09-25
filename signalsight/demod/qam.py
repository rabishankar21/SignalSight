"""
16QAM and 64QAM demodulator.
"""
import numpy as np
from scipy import signal
from .bpsk import design_rrc_filter, _gardner_timing_recovery

def _estimate_freq_offset_qam(samples: np.ndarray, sample_rate: float) -> float:
    """
    Estimate carrier frequency offset for QAM using the 4th power method.
    """
    x4 = samples ** 4

    N = len(x4)
    fft_val = np.fft.fft(x4)
    fft_freq = np.fft.fftfreq(N, d=1.0 / sample_rate)

    peak_idx = np.argmax(np.abs(fft_val))
    f_offset = fft_freq[peak_idx] / 4.0
    return f_offset

def _get_qam_constellation(order: int) -> tuple:
    if order == 16:
        scale = np.sqrt(10)
        levels = np.array([-3, -1, 1, 3]) / scale
    elif order == 64:
        scale = np.sqrt(42)
        levels = np.array([-7, -5, -3, -1, 1, 3, 5, 7]) / scale
    else:
        raise ValueError("Only 16QAM and 64QAM are supported")
        
    X, Y = np.meshgrid(levels, levels)
    constellation = X.flatten() + 1j * Y.flatten()
    return levels, constellation

def _pll_qam(symbols: np.ndarray, constellation: np.ndarray) -> tuple:
    """
    Decision-directed PLL for QAM fine carrier phase/frequency tracking.
    """
    # Loop filter parameters
    loop_bw = 0.005
    damping = 0.707
    theta = loop_bw / (damping + 0.25 / damping)
    alpha = (4 * damping * theta) / (1 + 2 * damping * theta + theta ** 2)
    beta = (4 * theta ** 2) / (1 + 2 * damping * theta + theta ** 2)

    freq = 0.0
    phase = 0.0
    out = np.zeros_like(symbols)

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

def demodulate_qam(
    samples: np.ndarray,
    sample_rate: float,
    symbol_rate: float,
    order: int = 16,
    rolloff: float = 0.35,
) -> dict:
    """
    Demodulate 16QAM/64QAM signal.
    """
    sps = int(np.round(sample_rate / symbol_rate))
    if sps < 2:
        sps = 2

    # 1. RRC Matched Filter
    h_rrc = design_rrc_filter(rolloff, 10, sps)
    rx = np.convolve(samples, h_rrc, mode='same')

    # 2. Coarse frequency offset estimation and correction (4th power)
    f_offset = _estimate_freq_offset_qam(rx, sample_rate)
    t_arr = np.arange(len(rx)) / sample_rate
    rx = rx * np.exp(-1j * 2 * np.pi * f_offset * t_arr)

    # 3. Gardner Timing Recovery
    symbols_sync = _gardner_timing_recovery(rx, sps)
    
    # 5. AGC: normalize symbol amplitudes
    # Average power of constellation is 1.0 (due to scale)
    # So we normalize the symbols to average power 1.0
    power = np.mean(np.abs(symbols_sync)**2)
    if power > 0:
        symbols_sync = symbols_sync / np.sqrt(power)

    # 4. Decision-directed PLL
    levels, constellation = _get_qam_constellation(order)
    symbols_fine, final_phase = _pll_qam(symbols_sync, constellation)

    # 6. Nearest-point demapping
    if order == 16:
        # -3 -> 00 (0), -1 -> 01 (1), 1 -> 11 (3), 3 -> 10 (2)
        gray_map = {0: [0, 0], 1: [0, 1], 2: [1, 1], 3: [1, 0]}
        bits_per_dim = 2
    else:
        # -7 -> 000 (0), -5 -> 001 (1), -3 -> 011 (3), -1 -> 010 (2), 1 -> 110 (6), 3 -> 111 (7), 5 -> 101 (5), 7 -> 100 (4)
        gray_map = {0: [0, 0, 0], 1: [0, 0, 1], 2: [0, 1, 1], 3: [0, 1, 0], 
                    4: [1, 1, 0], 5: [1, 1, 1], 6: [1, 0, 1], 7: [1, 0, 0]}
        bits_per_dim = 3
        
    num_bits = len(symbols_fine) * bits_per_dim * 2
    bits = np.zeros(num_bits, dtype=np.uint8)
    
    for i, sym in enumerate(symbols_fine):
        # I channel
        i_val = np.real(sym)
        i_idx = np.argmin(np.abs(i_val - levels))
        i_bits = gray_map[i_idx]
        
        # Q channel
        q_val = np.imag(sym)
        q_idx = np.argmin(np.abs(q_val - levels))
        q_bits = gray_map[q_idx]
        
        idx = i * bits_per_dim * 2
        bits[idx:idx+bits_per_dim] = i_bits
        bits[idx+bits_per_dim:idx+bits_per_dim*2] = q_bits

    return {
        'bits': bits,
        'symbols': symbols_fine,
        'constellation': symbols_fine,
        'num_symbols': len(symbols_fine),
        'num_bits': len(bits),
        'carrier_freq_offset': float(f_offset),
        'phase_offset': float(final_phase),
    }
