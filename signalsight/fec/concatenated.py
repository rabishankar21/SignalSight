import numpy as np

# Import from existing modules
try:
    from signalsight.demod.viterbi import ViterbiDecoder, encode as viterbi_encode
    from signalsight.fec.reed_solomon import ReedSolomonFEC
    from signalsight.interleave.block import block_interleave, block_deinterleave
except ImportError:
    pass

class ConcatenatedFEC:
    def __init__(self, inner_fec='viterbi', outer_fec='rs', interleaver='block',
                 viterbi_k=7, viterbi_polys=(0o171, 0o133),
                 rs_nsym=32, int_rows=None, int_cols=None):
        self.inner_fec = inner_fec
        self.outer_fec = outer_fec
        self.interleaver = interleaver
        self.viterbi_k = viterbi_k
        self.viterbi_polys = viterbi_polys
        self.rs_nsym = rs_nsym
        self.int_rows = int_rows
        self.int_cols = int_cols
        
        if self.inner_fec == 'viterbi':
            self.viterbi = ViterbiDecoder(k=viterbi_k, polys=viterbi_polys)
        if self.outer_fec == 'rs':
            self.rs = ReedSolomonFEC(nsym=rs_nsym)

    def encode(self, bits: np.ndarray) -> np.ndarray:
        data = bits
        if self.outer_fec == 'rs':
            data = self.rs.encode_bits(data)
            
        if self.interleaver == 'block':
            rows = self.int_rows if self.int_rows else 32
            cols = self.int_cols if self.int_cols else len(data) // rows
            data = block_interleave(data, rows, cols)
            
        if self.inner_fec == 'viterbi':
            data = viterbi_encode(data, self.viterbi_k, self.viterbi_polys)
            
        return data

    def decode(self, bits: np.ndarray) -> dict:
        data = bits
        inner_success = True
        outer_success = True
        inner_res = {}
        outer_res = {}
        
        if self.inner_fec == 'viterbi':
            try:
                data = self.viterbi.decode(data)
                inner_res['path_metric'] = getattr(self.viterbi, 'last_path_metric', 0)
            except Exception as e:
                inner_success = False
                inner_res['error'] = str(e)
                
        if inner_success and self.interleaver == 'block':
            rows = self.int_rows if self.int_rows else 32
            cols = self.int_cols if self.int_cols else len(data) // rows
            try:
                data = block_deinterleave(data, rows, cols)
            except Exception as e:
                inner_success = False
                inner_res['error'] = f"Deinterleave failed: {e}"

        if inner_success and self.outer_fec == 'rs':
            try:
                data, rs_success, rs_errs = self.rs.decode_bits(data), True, 0
                outer_success = rs_success
                outer_res['errors_corrected'] = rs_errs
            except Exception as e:
                outer_success = False
                outer_res['error'] = str(e)
                
        return {
            'decoded_bits': data,
            'inner_result': inner_res,
            'outer_result': outer_res,
            'success': inner_success and outer_success
        }
