import numpy as np

def diagonal_interleave(bits: np.ndarray, rows: int, cols: int) -> np.ndarray:
    block_size = rows * cols
    num_blocks = len(bits) // block_size
    
    out_bits = []
    
    for b in range(num_blocks):
        block = bits[b * block_size : (b + 1) * block_size].reshape((rows, cols))
        for d in range(cols):
            for i in range(rows):
                j = (d + i) % cols
                out_bits.append(block[i, j])
                
    tail = bits[num_blocks * block_size:]
    if len(tail) > 0:
        out_bits.extend(tail)
        
    return np.array(out_bits, dtype=bits.dtype)

def diagonal_deinterleave(bits: np.ndarray, rows: int, cols: int) -> np.ndarray:
    block_size = rows * cols
    num_blocks = len(bits) // block_size
    
    out_bits = np.zeros_like(bits)
    idx = 0
    for b in range(num_blocks):
        block = np.zeros((rows, cols), dtype=bits.dtype)
        for d in range(cols):
            for i in range(rows):
                j = (d + i) % cols
                block[i, j] = bits[idx]
                idx += 1
        out_bits[b * block_size : (b + 1) * block_size] = block.flatten()
        
    tail = bits[num_blocks * block_size:]
    if len(tail) > 0:
        out_bits[num_blocks * block_size:] = tail
        
    return out_bits
