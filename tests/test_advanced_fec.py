import unittest
import numpy as np

from signalsight.fec.reed_solomon import ReedSolomonFEC
from signalsight.interleave.block import block_interleave, block_deinterleave
from signalsight.utils.signal_generator import generate_signal
from signalsight.core.preprocessor import preprocess
from signalsight.demod.bpsk import demodulate_bpsk
from signalsight.demod.qpsk import demodulate_qpsk

class TestAdvancedFEC(unittest.TestCase):
    
    def test_rs_interleaved_bpsk_pipeline(self):
        # 1. Generate information bits
        np.random.seed(42)
        num_info_bytes = 100
        info_bytes = np.random.randint(0, 256, num_info_bytes, dtype=np.uint8)
        info_bits = np.unpackbits(info_bytes)
        
        # 2. RS Encode
        rs = ReedSolomonFEC(nsym=32)
        encoded_bytes = rs.encode_bytes(info_bytes)
        encoded_bits = np.unpackbits(encoded_bytes)
        
        # 3. Interleave
        # 132 bytes = 1056 bits
        rows, cols = 32, 33 # 1056 bits
        interleaved_bits = block_interleave(encoded_bits, rows, cols)
        
        # 4. Modulate & Channel (SNR = 6 dB BPSK to induce some errors)
        # We need a custom signal generator flow since generate_signal uses random bits
        sps = 4
        symbols = np.where(interleaved_bits == 0, 1.0 + 0j, -1.0 + 0j)
        up_symbols = np.zeros(len(symbols) * sps, dtype=complex)
        up_symbols[::sps] = symbols
        
        from signalsight.demod.bpsk import design_rrc_filter
        h_rrc = design_rrc_filter(0.35, 10, sps)
        baseband = np.convolve(up_symbols, h_rrc, mode='same')
        
        snr_db = 4.0
        pwr = np.mean(np.abs(baseband)**2)
        noise_pwr = pwr / (10 ** (snr_db / 10))
        noise = np.sqrt(noise_pwr / 2) * (np.random.randn(len(baseband)) + 1j * np.random.randn(len(baseband)))
        samples = (baseband + noise).astype(np.complex64)
        
        # 5. Demodulate
        processed = preprocess(samples, 400000, dc_remove=True, normalize=True)
        res = demodulate_bpsk(processed, 400000, 100000)
        raw_bits = res['bits']
        
        # Because of filter span delay, we must align the raw_bits to the expected interleaved_bits
        # BPSK demod drops ~10 bits at start/end
        # Find best alignment
        best_err = len(interleaved_bits)
        best_offset = 0
        best_phase = 0
        for offset in range(-20, 20):
            if offset < 0:
                o = interleaved_bits[-offset:]
                r = raw_bits[:len(o)]
            else:
                o = interleaved_bits
                r = raw_bits[offset:offset+len(o)]
                
            m = min(len(o), len(r))
            if m < len(interleaved_bits) - 20: continue
            
            # Phase 0
            err0 = np.sum(o[:m] != r[:m])
            # Phase 180
            r_inv = 1 - r[:m]
            err1 = np.sum(o[:m] != r_inv)
            
            if err0 < best_err:
                best_err = err0
                best_offset = offset
                best_phase = 0
                
            if err1 < best_err:
                best_err = err1
                best_offset = offset
                best_phase = 1
                
        # Extract the exact block of interleaved bits
        if best_offset < 0:
            pad_front = np.zeros(-best_offset, dtype=np.uint8)
            take_len = min(len(raw_bits), len(interleaved_bits) + best_offset)
            aligned_raw = np.concatenate([pad_front, raw_bits[:take_len]])
        else:
            aligned_raw = raw_bits[best_offset:best_offset+len(interleaved_bits)].copy()
            
        if best_phase == 1:
            aligned_raw = 1 - aligned_raw
            
        # Pad at end if short
        if len(aligned_raw) < len(interleaved_bits):
            aligned_raw = np.pad(aligned_raw, (0, len(interleaved_bits) - len(aligned_raw)), 'constant')
            
        # 6. De-interleave
        deinterleaved_bits = block_deinterleave(aligned_raw, rows, cols)
        
        print(f"\\nBest alignment -> err: {best_err}/{len(interleaved_bits)}, offset: {best_offset}, phase: {best_phase}")
        
        # Raw BER before RS
        raw_ber = np.sum(deinterleaved_bits != encoded_bits) / len(encoded_bits)
        print(f"Raw BER before RS: {raw_ber:.4f}")
        self.assertGreater(raw_ber, 0.0) # Ensure we actually have errors to fix
        
        # 7. RS Decode
        recovered_bits = rs.decode_bits(deinterleaved_bits, original_bit_len=len(info_bits))
        
        # 8. Check exact recovery
        self.assertEqual(len(recovered_bits), len(info_bits))
        rs_ber = np.sum(recovered_bits != info_bits) / len(info_bits)
        print(f"RS decoded BER: {rs_ber:.4f}")
        self.assertEqual(rs_ber, 0.0)

if __name__ == '__main__':
    unittest.main()
