"""
Bit-stream correlation and frame detection module.
Provides autocorrelation, sync-word search, repeated-pattern detection,
and frame boundary candidate detection.
"""
import numpy as np
from typing import Optional


def autocorrelate(bits: np.ndarray, max_lag: int = None) -> np.ndarray:
    """
    Compute normalized autocorrelation of bit sequence.
    Converts bits (0/1) to bipolar (+1/-1), computes correlation, normalizes by length.
    
    Returns correlation values for lags 0 to max_lag.
    """
    if len(bits) == 0:
        return np.array([])
    
    # Convert to bipolar
    bipolar = 2.0 * bits.astype(np.float64) - 1.0
    n = len(bipolar)
    
    if max_lag is None:
        max_lag = min(n - 1, 4096)
    max_lag = min(max_lag, n - 1)
    
    result = np.zeros(max_lag + 1)
    result[0] = 1.0  # Autocorrelation at lag 0 is always 1.0 (normalized)
    
    for lag in range(1, max_lag + 1):
        corr = np.sum(bipolar[:n - lag] * bipolar[lag:])
        result[lag] = corr / (n - lag)
    
    return result


def find_sync_word(bits: np.ndarray, pattern: np.ndarray, threshold: float = 0.8) -> list:
    """
    Search for a known sync word/pattern in the bit stream.
    Uses sliding normalized cross-correlation.
    
    Args:
        bits: Input bit stream (0/1)
        pattern: Sync word pattern to search for (0/1)
        threshold: Minimum normalized correlation score (0 to 1)
    
    Returns:
        List of {'offset': int, 'score': float} where score > threshold.
    """
    if len(bits) == 0 or len(pattern) == 0 or len(pattern) > len(bits):
        return []
    
    # Convert to bipolar
    bits_bp = 2.0 * bits.astype(np.float64) - 1.0
    pat_bp = 2.0 * pattern.astype(np.float64) - 1.0
    pat_len = len(pat_bp)
    
    results = []
    for offset in range(len(bits_bp) - pat_len + 1):
        segment = bits_bp[offset:offset + pat_len]
        score = np.sum(segment * pat_bp) / pat_len
        if score >= threshold:
            results.append({'offset': int(offset), 'score': float(score)})
    
    # Sort by score descending
    results.sort(key=lambda x: x['score'], reverse=True)
    return results


def detect_repeated_pattern(bits: np.ndarray, min_period: int = 8, max_period: int = 4096) -> list:
    """
    Detect repeated patterns using autocorrelation peaks.
    
    Args:
        bits: Input bit stream
        min_period: Minimum period to search
        max_period: Maximum period to search
    
    Returns:
        List of {'period': int, 'score': float} for detected periodicities,
        sorted by score descending.
    """
    if len(bits) < min_period * 2:
        return []
    
    max_period = min(max_period, len(bits) // 2)
    if max_period < min_period:
        return []
    
    acorr = autocorrelate(bits, max_lag=max_period)
    
    # Find peaks in autocorrelation (excluding lag 0)
    results = []
    for lag in range(min_period, len(acorr)):
        score = acorr[lag]
        # Check if it's a local maximum
        if lag > 0 and lag < len(acorr) - 1:
            if score > acorr[lag - 1] and score > acorr[lag + 1] and score > 0.3:
                results.append({'period': int(lag), 'score': float(score)})
        elif lag == len(acorr) - 1 and score > acorr[lag - 1] and score > 0.3:
            results.append({'period': int(lag), 'score': float(score)})
    
    results.sort(key=lambda x: x['score'], reverse=True)
    return results


def detect_frame_boundaries(bits: np.ndarray, sync_pattern: np.ndarray = None,
                            min_frame_len: int = 64, max_frame_len: int = 8192) -> dict:
    """
    Detect candidate frame boundaries.
    
    If sync_pattern is provided, uses sync word positions to determine frame length.
    Otherwise, uses autocorrelation-based period detection.
    
    Returns:
        {
            'frame_length': int or None,
            'boundaries': list[int],
            'confidence': float,
            'method': str
        }
    """
    if len(bits) == 0:
        return {'frame_length': None, 'boundaries': [], 'confidence': 0.0, 'method': 'none'}
    
    if sync_pattern is not None and len(sync_pattern) > 0:
        # Use sync word search
        matches = find_sync_word(bits, sync_pattern, threshold=0.9)
        if len(matches) < 2:
            return {'frame_length': None, 'boundaries': [m['offset'] for m in matches],
                    'confidence': 0.0, 'method': 'sync_word'}
        
        # Calculate frame length from sync word spacings
        offsets = sorted([m['offset'] for m in matches])
        spacings = np.diff(offsets)
        
        if len(spacings) == 0:
            return {'frame_length': None, 'boundaries': offsets,
                    'confidence': 0.0, 'method': 'sync_word'}
        
        # Most common spacing is the frame length
        from collections import Counter
        spacing_counts = Counter(spacings.tolist())
        most_common_spacing = spacing_counts.most_common(1)[0][0]
        count = spacing_counts.most_common(1)[0][1]
        confidence = count / len(spacings)
        
        return {
            'frame_length': int(most_common_spacing),
            'boundaries': offsets,
            'confidence': float(confidence),
            'method': 'sync_word'
        }
    else:
        # Use autocorrelation-based detection
        patterns = detect_repeated_pattern(bits, min_period=min_frame_len, max_period=max_frame_len)
        
        if not patterns:
            return {'frame_length': None, 'boundaries': [],
                    'confidence': 0.0, 'method': 'autocorrelation'}
        
        best = patterns[0]
        frame_len = best['period']
        boundaries = list(range(0, len(bits) - frame_len + 1, frame_len))
        
        return {
            'frame_length': frame_len,
            'boundaries': boundaries,
            'confidence': float(best['score']),
            'method': 'autocorrelation'
        }


def correlate_patterns(bits: np.ndarray, pattern: np.ndarray) -> dict:
    """
    Correlate bit stream against a known pattern.
    Finds the best match position and score.
    
    Returns:
        {
            'pattern_found': bool,
            'offset': int,
            'score': float,
            'num_matches': int  (number of positions with score > 0.8)
        }
    """
    if len(bits) == 0 or len(pattern) == 0 or len(pattern) > len(bits):
        return {'pattern_found': False, 'offset': -1, 'score': 0.0, 'num_matches': 0}
    
    matches = find_sync_word(bits, pattern, threshold=0.8)
    
    if not matches:
        # Find best even if below threshold
        bits_bp = 2.0 * bits.astype(np.float64) - 1.0
        pat_bp = 2.0 * pattern.astype(np.float64) - 1.0
        pat_len = len(pat_bp)
        
        best_score = -1.0
        best_offset = 0
        for offset in range(len(bits_bp) - pat_len + 1):
            segment = bits_bp[offset:offset + pat_len]
            score = np.sum(segment * pat_bp) / pat_len
            if score > best_score:
                best_score = score
                best_offset = offset
        
        return {
            'pattern_found': False,
            'offset': int(best_offset),
            'score': float(best_score),
            'num_matches': 0
        }
    
    return {
        'pattern_found': True,
        'offset': matches[0]['offset'],
        'score': matches[0]['score'],
        'num_matches': len(matches)
    }
