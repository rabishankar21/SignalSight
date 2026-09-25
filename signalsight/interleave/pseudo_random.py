import numpy as np

def pseudo_random_interleave(bits: np.ndarray, block_size: int, seed: int) -> np.ndarray:
    rng = np.random.default_rng(seed)
    perm = rng.permutation(block_size)
    
    num_blocks = len(bits) // block_size
    out_bits = np.zeros_like(bits)
    
    for b in range(num_blocks):
        block = bits[b * block_size : (b + 1) * block_size]
        out_block = np.zeros_like(block)
        for i in range(block_size):
            out_block[perm[i]] = block[i]
        out_bits[b * block_size : (b + 1) * block_size] = out_block
        
    tail = bits[num_blocks * block_size:]
    if len(tail) > 0:
        out_bits[num_blocks * block_size:] = tail
        
    return out_bits

def pseudo_random_deinterleave(bits: np.ndarray, block_size: int, seed: int) -> np.ndarray:
    rng = np.random.default_rng(seed)
    perm = rng.permutation(block_size)
    
    num_blocks = len(bits) // block_size
    out_bits = np.zeros_like(bits)
    
    for b in range(num_blocks):
        block = bits[b * block_size : (b + 1) * block_size]
        out_block = np.zeros_like(block)
        for i in range(block_size):
            out_block[i] = block[perm[i]]
        out_bits[b * block_size : (b + 1) * block_size] = out_block
        
    tail = bits[num_blocks * block_size:]
    if len(tail) > 0:
        out_bits[num_blocks * block_size:] = tail
        
    return out_bits
