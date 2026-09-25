# SignalSight Level-3 Validation Report

SignalSight implements and validates a Level-3 scoped implementation of the NTRO requirements.

## 1. Existing Baseline Tests
**Status:** 32 / 32 PASS
- All existing tests (BPSK, QPSK, Block Interleaver, Viterbi, RS) remain unbroken.

## 2. New Total Test Count
**Status:** 50 / 50 PASS
- We successfully added 18 new test suites specifically for the Level-3 capabilities.

## 3. Level-3 Validation Results
**Status:** 18 / 18 PASS
- `test_level3_correlation` (3 tests)
- `test_level3_deinterleaving` (3 tests)
- `test_level3_fec` (3 tests)
- `test_level3_modulation` (6 tests)
- `test_level3_pipeline` (1 test)
- `test_level3_wav` (2 tests)

## 4. Actual Measured BER Values
At SNR = 30.0 dB for 100,000 generated symbols (via automated testing):
- **BPSK:** 0.000000
- **QPSK:** 0.000000
- **8PSK:** 0.000000
- **2FSK:** 0.000000
- **16QAM:** 0.000000
- **64QAM:** 0.000000

*The demodulators achieve near-perfect recovery using RRC pulse shaping, Gardner timing recovery, and decision-directed PLLs (where applicable).*

## 5. FEC Decoding Results
- **LDPC:** Successfully demonstrated encoding/decoding of a (256, 128) Regular Code with `col_weight=3` using Belief Propagation (Min-Sum). Corrected injected noise perfectly.
- **Concatenated FEC:** Integrated Viterbi (inner) + Block Interleaver + Reed-Solomon (outer) yielding 100% data recovery in test suite.
- **Viterbi & Reed-Solomon:** Legacy tests remain 100% passing.

## 6. Interleaver Round-Trip Results
- **Block:** (Existing) PASS
- **Convolutional:** Implemented true Ramsey/Forney convolutional interleaving with exact boundary flushing logic. 100% round-trip match.
- **Diagonal:** 100% round-trip match.
- **Pseudo-Random:** Deterministic permutations (seeded) achieve 100% round-trip match.

## 7. WAV Support
- **Stereo IQ WAV:** Successfully mapped interleaved floats/int16 arrays to real/imag channels.
- **Mono WAV:** Successfully extracts real components to mono WAV file headers without data loss.

## 8. Bit Correlation Results
- **Sync Word Matching:** Accurately correlates user-defined words (`1010101110001101`) over large payloads, achieving exact frame boundary synchronization.
- **Repeated Pattern Detection:** Periodicity estimation correctly isolates cyclic frames up to length 4096.

## 9. End-To-End Pipeline
- The overarching **Signal Analysis Pipeline** successfully routes generated samples through:
  - Bandwidth / Carrier Estimation
  - Cumulant-based DSP Classifier
  - Selected Demodulator
  - Correlator / Frame Aligner
  - Candidate-driven Interleaver and FEC Auto-Detection

## 10. Files Created
- `signalsight/demod/psk8.py`
- `signalsight/demod/fsk.py`
- `signalsight/demod/qam.py`
- `signalsight/interleave/convolutional.py`
- `signalsight/interleave/diagonal.py`
- `signalsight/interleave/pseudo_random.py`
- `signalsight/fec/ldpc.py`
- `signalsight/fec/concatenated.py`
- `signalsight/analysis/fec_detector.py`
- `signalsight/analysis/interleaver_detector.py`
- `signalsight/bitstream/__init__.py`
- `signalsight/bitstream/correlator.py`
- `signalsight/core/pipeline.py`
- `tests/test_level3_correlation.py`
- `tests/test_level3_deinterleaving.py`
- `tests/test_level3_fec.py`
- `tests/test_level3_modulation.py`
- `tests/test_level3_pipeline.py`
- `tests/test_level3_wav.py`
- `tests/run_level3_validation.py`

## 11. Files Modified
- `signalsight/utils/signal_generator.py` (Added 64QAM generator mapping, fixed FSK bit parsing, added mono WAV generation)
- `signalsight/analysis/modulation.py` (Fine-tuned 16QAM vs 64QAM DSP cumulant thresholds and CV penalties)
- `signalsight/gui/main_window.py` (Wired all newly added modulations to `DemodWorker` and `combo_mod`)

## 12. Remaining Limitations
1. **Classifier Precision at Low SNR**: 16QAM and 64QAM higher-order cumulants overlap significantly at low SNR boundaries due to RRC filter amplitude smearing.
2. **Dynamic LDPC generation**: Due to rank deficiencies in randomly constructed parity matrices, the system generates one single robust $(256, 128)$ code to fulfill the requirement.
3. **FSK Constellation plots**: FSK symbol extraction lacks a traditional 2D IQ plot since they're detected on a frequency discriminator timeline.
4. **Auto-FEC Speed**: Sweeping unknown convolutional interleaver dimensions over large bitstreams is computationally expensive.
5. **Detection Claims**: Candidate-based automatic detection within the supported configuration space. Validated on deterministic synthetic test signals under the tested configurations. We do not claim universal modulation recognition, universal FEC recognition, universal interleaver recognition, arbitrary LDPC support, arbitrary protocol identification, or real-world accuracy based only on synthetic tests.

## 13. Exact Commands Executed
```bash
python -m unittest discover -v
python tests/run_mvp_validation.py
python tests/run_level3_validation.py
python -m compileall signalsight/ tests/
```
