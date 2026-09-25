import numpy as np

def detect_fec(bits: np.ndarray, max_candidates=5) -> list[dict]:
    results = []
    
    # 1. None
    results.append({
        "fec": "None",
        "confidence": 1.0,
        "validation": "Raw bits",
        "decoded_bits": bits
    })
    
    # 2. Viterbi R=1/2 K=7
    try:
        from signalsight.demod.viterbi import ViterbiDecoder
        v_dec = ViterbiDecoder(k=7, polys=(0o171, 0o133))
        dec0_input = bits[:2*(len(bits)//2)]
        dec0 = v_dec.decode(dec0_input)
        pm0 = getattr(v_dec, 'last_path_metric', 1000)
        if len(bits) > 1:
            dec1_input = bits[1:1 + 2*((len(bits)-1)//2)]
            dec1 = v_dec.decode(dec1_input)
        else:
            dec1 = dec0
        pm1 = getattr(v_dec, 'last_path_metric', 1000)
        
        best_pm = min(pm0, pm1)
        best_dec = dec0 if pm0 < pm1 else dec1
        
        conf = 0.9 if best_pm < 100 else 0.4
        results.append({
            "fec": "Viterbi R=1/2 K=7",
            "confidence": conf,
            "validation": f"Low path metric" if best_pm < 100 else f"Path metric: {best_pm}",
            "decoded_bits": best_dec
        })
    except ImportError:
        pass
        
    # 3. Reed-Solomon (nsym=32)
    try:
        from signalsight.fec.reed_solomon import ReedSolomonFEC
        rs = ReedSolomonFEC(nsym=32)
        dec = rs.decode_bits(bits)
        success = len(dec) > 0
        conf = 0.95 if success else 0.1
        results.append({
            "fec": "Reed-Solomon (nsym=32)",
            "confidence": conf,
            "validation": "RS decode success" if success else "RS decode failed",
            "decoded_bits": dec
        })
    except ImportError:
        pass
        
    # 4. Concatenated Viterbi+RS
    try:
        from signalsight.fec.concatenated import ConcatenatedFEC
        cat_fec = ConcatenatedFEC(inner_fec='viterbi', outer_fec='rs', viterbi_k=7, rs_nsym=32)
        res = cat_fec.decode(bits)
        success = res.get('success', False)
        conf = 0.95 if success else 0.1
        results.append({
            "fec": "Concatenated Viterbi+RS",
            "confidence": conf,
            "validation": "Decode success" if success else "Decode failed",
            "decoded_bits": res.get('decoded_bits', bits)
        })
    except ImportError:
        pass
        
    # 5. LDPC (256,128)
    try:
        from signalsight.fec.ldpc import LDPCCodec
        ldpc = LDPCCodec(n=256, m=128)
        if len(bits) >= 256:
            block = bits[:256]
            dec_block, conv, iters = ldpc.decode(block)
            conf = 0.9 if conv else 0.2
            dec_all = ldpc.decode_bits(bits)
            results.append({
                "fec": "LDPC (256,128)",
                "confidence": conf,
                "validation": f"Syndrome check: {'Pass' if conv else 'Fail'} in {iters} iters",
                "decoded_bits": dec_all
            })
    except ImportError:
        pass
        
    # Sort by confidence
    results.sort(key=lambda x: x['confidence'], reverse=True)
    return results[:max_candidates]
