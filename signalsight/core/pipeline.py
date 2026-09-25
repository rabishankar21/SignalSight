"""
SignalSight End-to-End Analysis Pipeline.
Structured pipeline that runs all analysis stages and returns structured results.
"""
import numpy as np
from typing import Optional


def run_pipeline(samples: np.ndarray, sample_rate: float, config: dict = None) -> dict:
    """
    Run the full SignalSight analysis pipeline.
    
    Config options:
        modulation: 'auto' or specific type (BPSK, QPSK, 8PSK, 2FSK, 16QAM, 64QAM)
        fec: 'auto', 'none', 'viterbi', 'rs', 'concatenated', 'ldpc'
        interleaver: 'auto', 'none', 'block', 'convolutional', 'diagonal', 'pseudo_random'
        symbol_rate: float or None (auto-estimate)
        rolloff: float (default 0.35)
        interleaver_params: dict (rows, cols, branches, delay, seed, block_size)
        fec_params: dict (nsym, etc.)
    
    Returns dict with structured results for each stage.
    """
    if config is None:
        config = {}
    
    mod_type = config.get('modulation', 'auto')
    fec_type = config.get('fec', 'none')
    interleaver_type = config.get('interleaver', 'none')
    symbol_rate = config.get('symbol_rate', None)
    rolloff = config.get('rolloff', 0.35)
    int_params = config.get('interleaver_params', {})
    fec_params = config.get('fec_params', {})
    
    results = {
        'input': {
            'sample_rate': sample_rate,
            'num_samples': len(samples),
            'duration': len(samples) / sample_rate
        },
        'stages_completed': []
    }
    
    # Stage 1: Preprocessing
    try:
        from signalsight.core.preprocessor import preprocess
        processed = preprocess(samples, sample_rate)
        results['stages_completed'].append('preprocessing')
    except Exception as e:
        results['preprocessing_error'] = str(e)
        processed = samples
    
    # Stage 2: Spectral Analysis
    try:
        from signalsight.analysis.spectral import compute_psd
        freqs, psd_db = compute_psd(processed, sample_rate)
        results['spectral'] = {'frequencies_shape': freqs.shape, 'psd_shape': psd_db.shape}
        results['stages_completed'].append('spectral')
    except Exception as e:
        results['spectral_error'] = str(e)
        freqs, psd_db = None, None
    
    # Stage 3: Parameter Estimation
    try:
        from signalsight.analysis.estimator import estimate_bandwidth, estimate_snr, estimate_symbol_rate
        
        bw, lower, upper = 0.0, 0.0, 0.0
        snr = 0.0
        est_symrate = 0.0
        
        if freqs is not None and psd_db is not None:
            bw, lower, upper = estimate_bandwidth(freqs, psd_db)
            snr = estimate_snr(processed, sample_rate, bw)
        
        est_symrate, sr_conf = estimate_symbol_rate(processed, sample_rate)
        
        if symbol_rate is None:
            symbol_rate = est_symrate if est_symrate > 0 else sample_rate / 4
        
        results['parameters'] = {
            'snr_db': float(snr),
            'bandwidth_hz': float(bw),
            'symbol_rate_hz': float(est_symrate),
            'symbol_rate_used': float(symbol_rate),
            'symbol_rate_source': 'estimated' if config.get('symbol_rate') is None else 'configured'
        }
        results['stages_completed'].append('parameter_estimation')
    except Exception as e:
        results['parameter_error'] = str(e)
        if symbol_rate is None:
            symbol_rate = sample_rate / 4
    
    # Stage 4: Modulation Classification
    try:
        from signalsight.analysis.modulation import classify_modulation
        candidates = classify_modulation(processed, sample_rate, symbol_rate)
        
        if mod_type == 'auto':
            if candidates and candidates[0]['confidence'] > 0.3:
                detected_mod = candidates[0]['type']
            else:
                detected_mod = 'Unknown'
        else:
            detected_mod = mod_type.upper()
        
        results['classification'] = {
            'modulation': detected_mod,
            'confidence': candidates[0]['confidence'] if candidates else 0.0,
            'family': candidates[0].get('family', 'Unknown') if candidates else 'Unknown',
            'candidates': candidates[:3] if candidates else []
        }
        results['stages_completed'].append('classification')
    except Exception as e:
        results['classification_error'] = str(e)
        detected_mod = mod_type.upper() if mod_type != 'auto' else 'BPSK'
    
    # Stage 5: Demodulation
    bits = None
    symbols = None
    try:
        from signalsight.core.preprocessor import preprocess
        demod_samples = preprocess(samples, sample_rate)
        
        if detected_mod == 'BPSK':
            from signalsight.demod.bpsk import demodulate_bpsk
            demod_result = demodulate_bpsk(demod_samples, sample_rate, symbol_rate, rolloff)
        elif detected_mod == 'QPSK':
            from signalsight.demod.qpsk import demodulate_qpsk
            demod_result = demodulate_qpsk(demod_samples, sample_rate, symbol_rate, rolloff)
        elif detected_mod == '8PSK':
            from signalsight.demod.psk8 import demodulate_8psk
            demod_result = demodulate_8psk(demod_samples, sample_rate, symbol_rate, rolloff)
        elif detected_mod in ('2FSK', '4FSK'):
            from signalsight.demod.fsk import demodulate_fsk
            num_tones = 4 if detected_mod == '4FSK' else 2
            demod_result = demodulate_fsk(demod_samples, sample_rate, symbol_rate, num_tones)
        elif detected_mod in ('16QAM', '64QAM'):
            from signalsight.demod.qam import demodulate_qam
            order = 64 if detected_mod == '64QAM' else 16
            demod_result = demodulate_qam(demod_samples, sample_rate, symbol_rate, order, rolloff)
        else:
            demod_result = None
        
        if demod_result:
            bits = demod_result['bits']
            symbols = demod_result.get('symbols', None)
            results['demodulation'] = {
                'modulation': detected_mod,
                'num_bits': len(bits),
                'num_symbols': demod_result.get('num_symbols', 0),
                'carrier_freq_offset': demod_result.get('carrier_freq_offset', 0.0),
            }
            results['stages_completed'].append('demodulation')
    except Exception as e:
        results['demodulation_error'] = str(e)
    
    # Stage 6: Interleaver Detection (if auto)
    if bits is not None and interleaver_type == 'auto':
        try:
            from signalsight.analysis.interleaver_detector import detect_interleaver
            int_candidates = detect_interleaver(bits, fec_type=fec_type)
            if int_candidates:
                results['interleaver_detection'] = int_candidates[0]
                results['stages_completed'].append('interleaver_detection')
        except Exception as e:
            results['interleaver_detection_error'] = str(e)
    
    # Stage 7: De-interleaving
    deint_bits = bits
    if bits is not None and interleaver_type != 'none':
        try:
            if interleaver_type == 'block':
                from signalsight.interleave.block import block_deinterleave
                rows = int_params.get('rows', 32)
                cols = int_params.get('cols', 33)
                deint_bits = block_deinterleave(bits, rows, cols)
            elif interleaver_type == 'convolutional':
                from signalsight.interleave.convolutional import convolutional_deinterleave
                branches = int_params.get('branches', 12)
                delay = int_params.get('delay', 17)
                deint_bits = convolutional_deinterleave(bits, branches, delay)
            elif interleaver_type == 'diagonal':
                from signalsight.interleave.diagonal import diagonal_deinterleave
                rows = int_params.get('rows', 16)
                cols = int_params.get('cols', 16)
                deint_bits = diagonal_deinterleave(bits, rows, cols)
            elif interleaver_type == 'pseudo_random':
                from signalsight.interleave.pseudo_random import pseudo_random_deinterleave
                block_size = int_params.get('block_size', 256)
                seed = int_params.get('seed', 42)
                deint_bits = pseudo_random_deinterleave(bits, block_size, seed)
            
            results['deinterleaving'] = {
                'method': interleaver_type,
                'params': int_params,
                'input_bits': len(bits),
                'output_bits': len(deint_bits)
            }
            results['stages_completed'].append('deinterleaving')
        except Exception as e:
            results['deinterleaving_error'] = str(e)
            deint_bits = bits
    
    # Stage 8: FEC Detection (if auto)
    if deint_bits is not None and fec_type == 'auto':
        try:
            from signalsight.analysis.fec_detector import detect_fec
            fec_candidates = detect_fec(deint_bits)
            if fec_candidates:
                results['fec_detection'] = fec_candidates[0]
                results['stages_completed'].append('fec_detection')
        except Exception as e:
            results['fec_detection_error'] = str(e)
    
    # Stage 9: FEC Decode
    decoded_bits = deint_bits
    if deint_bits is not None and fec_type != 'none':
        try:
            if fec_type == 'viterbi':
                from signalsight.demod.viterbi import ViterbiDecoder
                vd = ViterbiDecoder()
                decoded_bits, phase = vd.decode_auto_phase(deint_bits)
                results['fec_decode'] = {
                    'method': 'Viterbi R=1/2 K=7',
                    'input_bits': len(deint_bits),
                    'output_bits': len(decoded_bits),
                    'phase': phase,
                    'success': True
                }
            elif fec_type == 'rs':
                from signalsight.fec.reed_solomon import ReedSolomonFEC
                nsym = fec_params.get('nsym', 32)
                rs = ReedSolomonFEC(nsym)
                decoded_bits = rs.decode_bits(deint_bits)
                success = len(decoded_bits) > 0
                results['fec_decode'] = {
                    'method': f'Reed-Solomon nsym={nsym}',
                    'input_bits': len(deint_bits),
                    'output_bits': len(decoded_bits),
                    'success': success
                }
            elif fec_type == 'concatenated':
                from signalsight.fec.concatenated import ConcatenatedFEC
                nsym = fec_params.get('nsym', 32)
                rows = int_params.get('rows', 32)
                cols = int_params.get('cols', 33)
                cfec = ConcatenatedFEC(rs_nsym=nsym, int_rows=rows, int_cols=cols)
                dec_result = cfec.decode(deint_bits)
                decoded_bits = dec_result.get('decoded_bits', deint_bits)
                results['fec_decode'] = {
                    'method': 'Concatenated Viterbi+RS',
                    'success': dec_result.get('success', False),
                    'input_bits': len(deint_bits),
                    'output_bits': len(decoded_bits)
                }
            elif fec_type == 'ldpc':
                from signalsight.fec.ldpc import LDPCCodec
                ldpc = LDPCCodec()
                decoded_bits = ldpc.decode_bits(deint_bits)
                results['fec_decode'] = {
                    'method': 'LDPC (256,128)',
                    'input_bits': len(deint_bits),
                    'output_bits': len(decoded_bits),
                    'success': len(decoded_bits) > 0
                }
            
            results['stages_completed'].append('fec_decode')
        except Exception as e:
            results['fec_decode_error'] = str(e)
            decoded_bits = deint_bits
    
    # Stage 10: Bit Correlation
    if decoded_bits is not None and len(decoded_bits) > 0:
        try:
            from signalsight.bitstream.correlator import detect_repeated_pattern
            patterns = detect_repeated_pattern(decoded_bits, min_period=8, max_period=min(4096, len(decoded_bits) // 2))
            results['correlation'] = {
                'patterns_found': len(patterns),
                'top_patterns': patterns[:3] if patterns else [],
                'total_bits': len(decoded_bits)
            }
            results['stages_completed'].append('correlation')
        except Exception as e:
            results['correlation_error'] = str(e)
    
    # Final output
    results['output'] = {
        'recovered_bits': len(decoded_bits) if decoded_bits is not None else 0,
        'bits': decoded_bits,
        'pipeline_stages': len(results['stages_completed']),
        'stages': results['stages_completed']
    }
    
    return results
