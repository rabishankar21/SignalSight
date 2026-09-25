import numpy as np

def _generate_H_and_G(n=256, m=128, seed=42) -> tuple[np.ndarray, np.ndarray]:
    rng = np.random.default_rng(seed)
    k = n - m
    
    # Generate P matrix (m x k) with sparsity ~ 3 ones per column
    P = np.zeros((m, k), dtype=np.uint8)
    for j in range(k):
        rows = rng.choice(m, 3, replace=False)
        P[rows, j] = 1
        
    # Systematic H = [P | I]
    H = np.hstack((P, np.eye(m, dtype=np.uint8)))
    
    # Systematic G = [I | P.T]
    G = np.hstack((np.eye(k, dtype=np.uint8), P.T))
    
    return H, G

class LDPCCodec:
    """
    Minimal LDPC encoder/decoder using belief propagation (min-sum algorithm).
    IMPORTANT: Only supports the specific (256, 128) code generated internally.
    """
    def __init__(self, n=256, m=128, col_weight=3, max_iter=50, seed=42):
        self.n = n
        self.m = m
        self.k = n - m
        self.col_weight = col_weight
        self.max_iter = max_iter
        self.seed = seed
        self.H, self.G = _generate_H_and_G(n, m, seed)

    def encode(self, info_bits: np.ndarray) -> np.ndarray:
        if len(info_bits) != self.k:
            raise ValueError(f"Expected {self.k} info bits")
        return (info_bits @ self.G) % 2

    def decode(self, received_bits: np.ndarray) -> tuple[np.ndarray, bool, int]:
        L_ci = np.where(received_bits == 0, 1.0, -1.0)
        L_q = np.zeros((self.m, self.n))
        L_r = np.zeros((self.m, self.n))
        
        for j in range(self.m):
            for i in range(self.n):
                if self.H[j, i] == 1:
                    L_q[j, i] = L_ci[i]
                    
        converged = False
        iterations = 0
        decoded = received_bits.copy()
        
        for it in range(self.max_iter):
            for j in range(self.m):
                connected_vars = np.where(self.H[j, :] == 1)[0]
                for i in connected_vars:
                    sign = 1
                    min_val = np.inf
                    for i_prime in connected_vars:
                        if i_prime != i:
                            val = L_q[j, i_prime]
                            sign *= np.sign(val) if val != 0 else 1
                            min_val = min(min_val, abs(val))
                    L_r[j, i] = sign * min_val
                    
            for i in range(self.n):
                connected_checks = np.where(self.H[:, i] == 1)[0]
                total_L = L_ci[i]
                for j in connected_checks:
                    total_L += L_r[j, i]
                    
                decoded[i] = 0 if total_L > 0 else 1
                
                for j in connected_checks:
                    L_q[j, i] = L_ci[i] + sum(L_r[j_prime, i] for j_prime in connected_checks if j_prime != j)
                    
            syndrome = (self.H @ decoded) % 2
            iterations += 1
            if not np.any(syndrome):
                converged = True
                break
                
        return decoded[:self.k], converged, iterations

    def encode_bits(self, bits: np.ndarray) -> np.ndarray:
        if len(bits) % self.k != 0:
            pad_len = self.k - (len(bits) % self.k)
            bits = np.pad(bits, (0, pad_len))
        
        num_blocks = len(bits) // self.k
        encoded = np.zeros(num_blocks * self.n, dtype=np.uint8)
        for i in range(num_blocks):
            block = bits[i * self.k : (i + 1) * self.k]
            encoded[i * self.n : (i + 1) * self.n] = self.encode(block)
        return encoded

    def decode_bits(self, bits: np.ndarray) -> np.ndarray:
        if len(bits) % self.n != 0:
            pad_len = self.n - (len(bits) % self.n)
            bits = np.pad(bits, (0, pad_len))
            
        num_blocks = len(bits) // self.n
        decoded = np.zeros(num_blocks * self.k, dtype=np.uint8)
        for i in range(num_blocks):
            block = bits[i * self.n : (i + 1) * self.n]
            dec_block, _, _ = self.decode(block)
            decoded[i * self.k : (i + 1) * self.k] = dec_block
        return decoded
