import numpy as np

def _conv_process(bits: np.ndarray, num_branches: int, delay_increment: int, deinterleave: bool = False) -> np.ndarray:
    # We must flush the shift registers, so we append enough zeros to push all real bits out
    flush_len = num_branches * (num_branches - 1) * delay_increment
    
    pad_len = (num_branches - (len(bits) % num_branches)) % num_branches
    total_pad = pad_len + flush_len
    
    bits_padded = np.concatenate([bits, np.zeros(total_pad, dtype=bits.dtype)])

    delays = [k * delay_increment for k in range(num_branches)]
    if deinterleave:
        delays = [(num_branches - 1 - k) * delay_increment for k in range(num_branches)]
    
    shift_registers = [np.zeros(d, dtype=bits.dtype).tolist() for d in delays]
    out_bits = []
    
    for i, b in enumerate(bits_padded):
        branch_idx = i % num_branches
        
        if delays[branch_idx] > 0:
            shift_registers[branch_idx].append(b)
            out_bits.append(shift_registers[branch_idx].pop(0))
        else:
            out_bits.append(b)
            
    return np.array(out_bits, dtype=bits.dtype)

def convolutional_interleave(bits: np.ndarray, num_branches: int, delay_increment: int) -> np.ndarray:
    """Convolutional interleaver/de-interleaver (Forney/Ramsey type)."""
    return _conv_process(bits, num_branches, delay_increment, deinterleave=False)

def convolutional_deinterleave(bits: np.ndarray, num_branches: int, delay_increment: int) -> np.ndarray:
    """Convolutional de-interleaver."""
    return _conv_process(bits, num_branches, delay_increment, deinterleave=True)
