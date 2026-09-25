import numpy as np

def block_interleave(bits: np.ndarray, rows: int, cols: int) -> np.ndarray:
    """
    Block Interleaver.
    Writes bits row-by-row into a (rows x cols) matrix and reads them column-by-column.
    If the length of bits is not a multiple of (rows * cols), the remaining bits are appended un-interleaved.
    """
    block_size = rows * cols
    num_blocks = len(bits) // block_size
    
    if num_blocks == 0:
        return bits.copy()
        
    main_len = num_blocks * block_size
    main_bits = bits[:main_len]
    tail_bits = bits[main_len:]
    
    # Reshape into (num_blocks, rows, cols)
    # Write row-by-row means the array is filled in C-order (default)
    matrix = main_bits.reshape((num_blocks, rows, cols))
    
    # Read column-by-column means we transpose the last two dimensions
    # and flatten.
    interleaved = matrix.transpose((0, 2, 1)).flatten()
    
    if len(tail_bits) > 0:
        interleaved = np.concatenate([interleaved, tail_bits])
        
    return interleaved

def block_deinterleave(bits: np.ndarray, rows: int, cols: int) -> np.ndarray:
    """
    Block De-interleaver.
    Writes bits column-by-column into a (rows x cols) matrix and reads them row-by-row.
    """
    block_size = rows * cols
    num_blocks = len(bits) // block_size
    
    if num_blocks == 0:
        return bits.copy()
        
    main_len = num_blocks * block_size
    main_bits = bits[:main_len]
    tail_bits = bits[main_len:]
    
    # Writing column-by-column is equivalent to writing row-by-row into a (cols x rows) matrix
    matrix = main_bits.reshape((num_blocks, cols, rows))
    
    # Read row-by-row of the original matrix means transpose back to (rows x cols)
    deinterleaved = matrix.transpose((0, 2, 1)).flatten()
    
    if len(tail_bits) > 0:
        deinterleaved = np.concatenate([deinterleaved, tail_bits])
        
    return deinterleaved
