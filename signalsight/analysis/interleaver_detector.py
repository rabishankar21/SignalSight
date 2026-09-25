import numpy as np

def detect_interleaver(bits: np.ndarray, fec_type='none', max_candidates=5) -> list[dict]:
    """
    Candidate-based interleaver detection.
    IMPORTANT: Do NOT claim universal blind detection. This is bounded candidate search.
    """
    results = []
    
    block_rows = [4, 8, 16, 32, 64]
    block_cols = [4, 8, 16, 32, 33, 64]
    conv_branches = [4, 8, 12]
    conv_delays = [1, 2, 4, 8, 17]
    diag_rows = [4, 8, 16, 32]
    diag_cols = [4, 8, 16, 32]
    rand_seeds = [0, 1, 42, 100]
    rand_blocks = [64, 128, 256, 512, 1024]
    
    for r in block_rows:
        for c in block_cols:
            if len(bits) < r * c:
                continue
                
            try:
                from signalsight.interleave.block import block_deinterleave
                deint = block_deinterleave(bits[:r*c], r, c)
                
                conf = 0.5
                val_msg = "Proxy score"
                
                if fec_type == 'none':
                    # very basic proxy
                    ac = np.correlate(deint - 0.5, deint - 0.5, mode='full')
                    if len(ac) > 0:
                        peak = ac[len(ac)//2]
                        conf = 0.5 + 0.1 * (peak / len(deint))
                
                results.append({
                    "type": "Block",
                    "params": {"rows": r, "cols": c},
                    "confidence": conf,
                    "validation": val_msg
                })
            except ImportError:
                pass
                
    results.sort(key=lambda x: x['confidence'], reverse=True)
    return results[:max_candidates]
