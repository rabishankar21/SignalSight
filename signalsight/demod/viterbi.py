import numpy as np
from typing import Tuple

class ViterbiDecoder:
    """
    Basic Viterbi Decoder for Convolutional Codes.
    Defaults to Rate 1/2, Constraint Length K=7.
    Standard polynomials: G1=171 (octal), G2=133 (octal).
    Uses hard-decision decoding (Hamming distance).
    """
    def __init__(self, k: int = 7, polys: Tuple[int, int] = (0o171, 0o133)):
        self.k = k
        self.polys = polys
        self.num_states = 2 ** (k - 1)
        
        # Precompute state transitions and outputs
        # state represents the k-1 previous bits.
        # Shift register sr = (input_bit << (k - 1)) | state
        
        self.outputs = np.zeros((self.num_states, 2, 2), dtype=int)
        
        # For vectorized decoding: 
        # For each next_state, what are the two possible previous states?
        self.prev_states = np.zeros((self.num_states, 2), dtype=int)
        # What input bit caused the transition from prev_state to next_state?
        self.prev_inputs = np.zeros((self.num_states, 2), dtype=int)
        # What was the expected output (y0, y1) for that transition?
        self.prev_outputs = np.zeros((self.num_states, 2, 2), dtype=int)
        
        for state in range(self.num_states):
            for input_bit in (0, 1):
                sr = (input_bit << (k - 1)) | state
                
                out1 = 0
                out2 = 0
                for i in range(k):
                    bit = (sr >> i) & 1
                    poly1_bit = (polys[0] >> i) & 1
                    poly2_bit = (polys[1] >> i) & 1
                    
                    out1 ^= (bit & poly1_bit)
                    out2 ^= (bit & poly2_bit)
                
                next_st = sr >> 1
                
                # The oldest bit of 'state' was lost (sr & 1)
                # The newest bit of 'next_st' is input_bit
                lost_bit = state & 1
                
                self.prev_states[next_st, lost_bit] = state
                self.prev_inputs[next_st, lost_bit] = input_bit
                self.prev_outputs[next_st, lost_bit, 0] = out1
                self.prev_outputs[next_st, lost_bit, 1] = out2

    def decode(self, bits: np.ndarray, return_metric: bool = False):
        """
        Decode a hard-decision received bitstream.
        Length of bits must be even (rate 1/2).
        Returns the recovered information bits.
        If return_metric is True, returns (decoded_bits, final_min_path_metric).
        """
        if len(bits) % 2 != 0:
            raise ValueError("Input bit array length must be a multiple of 2 for rate 1/2 code.")
            
        num_symbols = len(bits) // 2
        y = bits.reshape(-1, 2)
        
        path_metrics = np.full(self.num_states, np.inf)
        path_metrics[0] = 0.0  # Assume encoder starts in state 0
        
        # traceback matrix: stores the choice (0 or 1) of the previous state
        backpointers = np.zeros((num_symbols, self.num_states), dtype=np.uint8)
        
        # Pre-slice outputs for broadcasting
        # shape: (num_states, 2) -> (out0, out1) for the two possible paths into each state
        po_0 = self.prev_outputs[:, :, 0]
        po_1 = self.prev_outputs[:, :, 1]
        
        for i in range(num_symbols):
            y0, y1 = y[i, 0], y[i, 1]
            
            # Compute branch metrics for all incoming paths to all states
            bm = (po_0 != y0).astype(int) + (po_1 != y1).astype(int)
            
            # Total path metric for candidate paths
            pm_candidates = path_metrics[self.prev_states] + bm
            
            # Select the best (minimum metric) path for each state
            best_prev_idx = np.argmin(pm_candidates, axis=1)
            
            # Extract the minimum metrics
            path_metrics = pm_candidates[np.arange(self.num_states), best_prev_idx]
            
            # Record the decision for traceback
            backpointers[i, :] = best_prev_idx
            
        # Traceback
        decoded = np.zeros(num_symbols, dtype=np.uint8)
        
        # Start traceback from the state with minimum path metric
        min_idx = np.argmin(path_metrics)
        curr_state = min_idx
        
        for i in range(num_symbols - 1, -1, -1):
            choice = backpointers[i, curr_state]
            prev_state = self.prev_states[curr_state, choice]
            input_bit = self.prev_inputs[curr_state, choice]
            
            decoded[i] = input_bit
            curr_state = prev_state
            
        if return_metric:
            return decoded, path_metrics[min_idx]
        return decoded

    def decode_auto_phase(self, bits: np.ndarray) -> tuple[np.ndarray, int]:
        """
        Attempts to decode using both possible codeword boundary phases (0 and 1).
        Selects the phase with the lowest normalized path metric.
        Returns (decoded_bits, chosen_phase_offset).
        """
        # Phase 0
        bits0 = bits if len(bits) % 2 == 0 else bits[:-1]
        if len(bits0) == 0:
            return np.array([], dtype=np.uint8), 0
            
        decoded0, metric0 = self.decode(bits0, return_metric=True)
        norm_metric0 = metric0 / max(1, len(bits0))
        
        # Phase 1
        bits1 = bits[1:]
        bits1 = bits1 if len(bits1) % 2 == 0 else bits1[:-1]
        if len(bits1) == 0:
            return decoded0, 0
            
        decoded1, metric1 = self.decode(bits1, return_metric=True)
        norm_metric1 = metric1 / max(1, len(bits1))
        
        if norm_metric0 <= norm_metric1:
            return decoded0, 0
        else:
            return decoded1, 1


def encode(bits: np.ndarray, k: int = 7, polys: Tuple[int, int] = (0o171, 0o133)) -> np.ndarray:
    """
    Convolutionally encode bits. Rate 1/2.
    Assumes initial state is 0.
    Returns encoded bits (length = 2 * len(bits)).
    """
    num_states = 2 ** (k - 1)
    state = 0
    
    encoded = np.zeros(len(bits) * 2, dtype=np.uint8)
    
    for i, bit in enumerate(bits):
        sr = (bit << (k - 1)) | state
        
        out1 = 0
        out2 = 0
        for j in range(k):
            sr_bit = (sr >> j) & 1
            poly1_bit = (polys[0] >> j) & 1
            poly2_bit = (polys[1] >> j) & 1
            
            out1 ^= (sr_bit & poly1_bit)
            out2 ^= (sr_bit & poly2_bit)
            
        encoded[2*i] = out1
        encoded[2*i+1] = out2
        
        state = sr >> 1
        
    return encoded
