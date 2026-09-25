import numpy as np
import scipy.io.wavfile
from signalsight.demod.bpsk import design_rrc_filter

def generate_signal(
    modulation: str,
    symbol_rate: float,
    sample_rate: float,
    num_symbols: int = 10000,
    snr_db: float = 20.0,
    freq_offset: float = 0.0,
    phase_offset: float = 0.0,
    rolloff: float = 0.35,
    seed: int | None = None,
) -> tuple[np.ndarray, np.ndarray, dict]:
    """
    Generate a synthetic modulated signal with known parameters.
    """
    rng = np.random.default_rng(seed)
    sps = int(np.round(sample_rate / symbol_rate))
    
    modulation = modulation.upper()
    
    if modulation == 'BPSK':
        bits = rng.integers(0, 2, num_symbols)
        symbols = np.where(bits == 0, 1.0 + 0j, -1.0 + 0j)
    elif modulation == 'QPSK':
        bits = rng.integers(0, 2, num_symbols * 2)
        symbols = np.zeros(num_symbols, dtype=complex)
        for i in range(num_symbols):
            b1, b2 = bits[2*i], bits[2*i+1]
            if b1 == 0 and b2 == 0:
                symbols[i] = (1 + 1j) / np.sqrt(2)
            elif b1 == 0 and b2 == 1:
                symbols[i] = (-1 + 1j) / np.sqrt(2)
            elif b1 == 1 and b2 == 1:
                symbols[i] = (-1 - 1j) / np.sqrt(2)
            else:
                symbols[i] = (1 - 1j) / np.sqrt(2)
    elif modulation == '8PSK':
        bits = rng.integers(0, 2, num_symbols * 3)
        # Gray-coded 8PSK mapping: 3 bits -> phase index
        gray_map = {(0,0,0): 0, (0,0,1): 1, (0,1,1): 2, (0,1,0): 3,
                    (1,1,0): 4, (1,1,1): 5, (1,0,1): 6, (1,0,0): 7}
        symbols = np.zeros(num_symbols, dtype=complex)
        for i in range(num_symbols):
            b = tuple(bits[3*i:3*i+3])
            phase_idx = gray_map[b]
            symbols[i] = np.exp(1j * phase_idx * np.pi / 4)
    elif modulation == '16QAM':
        bits = rng.integers(0, 2, num_symbols * 4)
        levels = np.array([-3, -1, 1, 3]) / np.sqrt(10)
        # Gray mapping: 00->-3, 01->-1, 11->1, 10->3
        gray_map_4 = [0, 1, 3, 2]  # 2-bit Gray to level index
        symbols = np.zeros(num_symbols, dtype=complex)
        for i in range(num_symbols):
            i_bits = bits[4*i:4*i+2]
            q_bits = bits[4*i+2:4*i+4]
            i_idx = gray_map_4[int(i_bits[0])*2 + int(i_bits[1])]
            q_idx = gray_map_4[int(q_bits[0])*2 + int(q_bits[1])]
            symbols[i] = levels[i_idx] + 1j * levels[q_idx]
    elif modulation == '64QAM':
        bits = rng.integers(0, 2, num_symbols * 6)
        levels = np.array([-7, -5, -3, -1, 1, 3, 5, 7]) / np.sqrt(42)
        # Gray mapping for 3 bits: 000->0, 001->1, 011->2, 010->3, 110->4, 111->5, 101->6, 100->7
        gray_map_8 = [0, 1, 3, 2, 7, 6, 4, 5]
        symbols = np.zeros(num_symbols, dtype=complex)
        for i in range(num_symbols):
            i_bits = bits[6*i:6*i+3]
            q_bits = bits[6*i+3:6*i+6]
            i_idx = gray_map_8[int(i_bits[0])*4 + int(i_bits[1])*2 + int(i_bits[2])]
            q_idx = gray_map_8[int(q_bits[0])*4 + int(q_bits[1])*2 + int(q_bits[2])]
            symbols[i] = levels[i_idx] + 1j * levels[q_idx]
    elif modulation in ['2FSK', '4FSK']:
        # Simplified FSK
        M = int(modulation[0])
        bits = rng.integers(0, 2, num_symbols * int(np.log2(M)))
        symbols = np.zeros(num_symbols, dtype=complex) # Not used directly for FSK
    else:
        raise ValueError(f"Unsupported modulation: {modulation}")
        
    # Pulse shaping / Modulation
    if modulation in ['BPSK', 'QPSK', '8PSK', '16QAM', '64QAM']:
        up_symbols = np.zeros(num_symbols * sps, dtype=complex)
        up_symbols[::sps] = symbols
        
        h_rrc = design_rrc_filter(rolloff, 10, sps)
        baseband = np.convolve(up_symbols, h_rrc, mode='same')
    elif modulation in ['2FSK', '4FSK']:
        fd = symbol_rate / 4.0
        M = int(modulation[0])
        if M == 2:
            sym_vals = bits
        elif M == 4:
            sym_vals = bits[0::2] * 2 + bits[1::2]
        freqs = (2 * sym_vals - (M - 1)) * fd
        up_freqs = np.repeat(freqs, sps)
        phases = np.cumsum(2 * np.pi * up_freqs / sample_rate)
        baseband = np.exp(1j * phases)
        
    # Apply freq/phase offset
    t = np.arange(len(baseband)) / sample_rate
    baseband = baseband * np.exp(1j * 2 * np.pi * freq_offset * t + 1j * phase_offset)
    
    # AWGN
    signal_power = np.mean(np.abs(baseband)**2)
    noise_power = signal_power / (10 ** (snr_db / 10.0))
    noise = np.sqrt(noise_power / 2.0) * (rng.standard_normal(len(baseband)) + 1j * rng.standard_normal(len(baseband)))
    samples = baseband + noise
    
    ground_truth = {
        'modulation': modulation,
        'symbol_rate': symbol_rate,
        'sample_rate': sample_rate,
        'num_symbols': num_symbols,
        'snr_db': snr_db,
        'freq_offset': freq_offset,
        'phase_offset': phase_offset,
        'rolloff': rolloff
    }
    
    return samples, bits, ground_truth

def save_as_iq(samples: np.ndarray, filepath: str, fmt: str = 'float32') -> None:
    """Save complex samples as interleaved IQ file."""
    if fmt == 'float32':
        interleaved = np.zeros(2 * len(samples), dtype=np.float32)
        interleaved[0::2] = np.real(samples)
        interleaved[1::2] = np.imag(samples)
        interleaved.tofile(filepath)
    elif fmt == 'int16':
        # Scale to int16 range
        max_val = np.max(np.abs(np.concatenate([np.real(samples), np.imag(samples)])))
        scaled = samples / max_val * 32767.0
        interleaved = np.zeros(2 * len(samples), dtype=np.int16)
        interleaved[0::2] = np.real(scaled)
        interleaved[1::2] = np.imag(scaled)
        interleaved.tofile(filepath)
    else:
        raise ValueError(f"Unsupported format: {fmt}")

def save_as_wav(samples: np.ndarray, filepath: str, sample_rate: float) -> None:
    """Save complex samples as 2-channel WAV file (I=ch1, Q=ch2)."""
    max_val = np.max(np.abs(np.concatenate([np.real(samples), np.imag(samples)])))
    scaled = samples / max_val * 32767.0
    
    iq_array = np.column_stack((np.real(scaled), np.imag(scaled))).astype(np.int16)
    scipy.io.wavfile.write(filepath, int(sample_rate), iq_array)

def save_as_wav_mono(samples: np.ndarray, filepath: str, sample_rate: float) -> None:
    """Save real-valued signal as mono WAV file."""
    real_signal = np.real(samples).astype(np.float64)
    max_val = np.max(np.abs(real_signal))
    if max_val > 0:
        scaled = (real_signal / max_val * 32767.0).astype(np.int16)
    else:
        scaled = np.zeros(len(real_signal), dtype=np.int16)
    scipy.io.wavfile.write(filepath, int(sample_rate), scaled)
