# FINAL VALIDATION REPORT

## 1. Executive Summary
The MVP implementation of SignalSight has been frozen and fully validated. The pipeline demonstrates robust parameter estimation, modulation recognition for BPSK/QPSK, deterministic phase-ambiguity resolution, Viterbi (K=7, Rate 1/2), Block De-interleaving, and Reed-Solomon processing. Automatic blind detection of FEC schemes and interleavers is explicitly excluded from this baseline.

## 2. Tested Pipeline
- **Preprocessing:** DC removal, RMS normalization, configurable bandpass filter, rational resampling.
- **Demodulation:** Costas Loop and Gardner timing recovery for BPSK and QPSK.
- **Codeword/Frame Alignment:** RS-assisted frame/bit alignment using bounded phase and offset search (checks -10 to +10 offsets and 0°/180° phases against the first de-interleaved RS block).
- **FEC Decoder:** Reed-Solomon (using manually configured nsym).

## 3. Unit Test Results
- **Command:** `python -m unittest discover -v`
- **Result:** 32 / 32 PASS
- **Execution Time:** ~3.41s
- **Coverage:** Verified parser robustness, interleaver matrix bounds, RRC channel bounds, and FEC pipelines.

## 4. MVP Validation Results
- **Command:** `python tests/run_mvp_validation.py`
- **QPSK Phase Ambiguity (20 dB SNR):** 
  - $0^{\circ}, 90^{\circ}, 180^{\circ}, 270^{\circ}$ injected rotational offsets tested.
  - 19996 bits compared per offset.
  - Result: 0 errors (0.000000 BER) in all quadrants.
- **QPSK SNR Sweep (0° Injected Phase):**
  - 20 dB: 0.000000 BER
  - 15 dB: 0.000000 BER
  - 10 dB: 0.000000 BER
  - 5 dB: 0.000050 BER (1 error)
  - 3 dB: 0.002601 BER (52 errors)
  - 0 dB: 0.024805 BER (496 errors)

## 5. GUI Acceptance Results
- **Command:** `python gui_acceptance_test.py`
- **Result:** ALL TESTS COMPLETED.
- Verified successful file loading, visualization widget rendering, parameter estimation update propagation, and Viterbi status parsing. Invalid file input correctly triggers a non-crashing `QMessageBox` alert.

## 6. FEC Validation Results (Manual GUI Check)
**Test File:** `data/test_signals/rs_interleaved_bpsk_test.iq`
**Ground-Truth Parameters:** BPSK, 400kHz Sample Rate, 100ksps, 132-byte (1056 bit) interleaved payload (32 rows x 33 cols), Reed-Solomon (32 nsym), 4.0 dB SNR.

| Case | Configuration | Mod | Est. SNR | Est. BW | Sym Rate | Raw Bits | Recov. Bits | Final Status |
|---|---|---|---|---|---|---|---|---|
| A | `viterbi_bpsk_test.iq`, Base | BPSK | 9.5 dB | 118.75 kHz | 100.00 ksps | 3998 | 3998 | Carrier offset: 0.0 Hz |
| B | `qpsk_ground_truth.iq`, Base | QPSK | 9.4 dB | 116.50 kHz | 100.00 ksps | 3996 | 3996 | Carrier offset: 0.0 Hz |
| C | `test.wav` | BPSK | - | - | - | - | - | Successful load or Graceful Alert |
| D | Viterbi OFF | BPSK | 9.5 dB | 118.75 kHz | 100.00 ksps | 3998 | 3998 | Carrier offset: 0.0 Hz |
| E | Viterbi ON | BPSK | 9.5 dB | 118.75 kHz | 100.00 ksps | 3998 | 1998 | FEC: Viterbi (Phase 1) |
| F | RS OFF + De-int OFF (RS File) | BPSK | 3.1 dB | 107.91 kHz | 100.00 ksps | 1054 | 1054 | Carrier offset: 0.0 Hz |
| G | RS ON + De-int ON (RS File) | BPSK | 3.1 dB | 107.91 kHz | 100.00 ksps | 1054 | 800 | FEC: Deinterleaved (32x33) \| RS decoded (Phase 0, Offset -1) |
| H | Invalid Rows/Cols | BPSK | - | - | - | - | - | MessageBox: "Invalid Parameters" |
| I | Invalid nsym | BPSK | - | - | - | - | - | MessageBox: "Invalid Parameters" |
| J | Unsupported/Missing file | - | - | - | - | - | - | MessageBox: "Load Error" |

## 7. Ground-Truth BER Results
- **Case E (Viterbi ON):** 1998 recovered bits matched ground truth perfectly (**BER 0.000000**).
- **Case G (RS + De-int ON):** The GUI worker cleanly resolved a $-1$ boundary timing offset and a $0^{\circ}$ phase ambiguity via bounded phase and offset search, matching exactly the 800-bit expected original payload (**BER 0.000000**).

## 8. Known Limitations
- Modulations such as 8PSK, 16QAM, 64QAM, FSK, and OFDM are **not supported**.
- Automatic/blind protocol identification (e.g. automatically detecting if a signal is Viterbi or Reed-Solomon without user configuration) is **not supported**.
- LDPC is **not supported**.
- The bounded RS phase/offset search operates over a narrow window (`[-10, +10]`), assuming near convergence of the demodulator's Gardner loop prior to decoding. It is not an arbitrary generic blind frame synchronizer.
- This platform does not claim real-world production readiness for arbitrary, unknown, or corrupted radio protocols outside the explicitly constrained testing bounds.

## 9. Reproducibility Commands
To verify the exact pipeline on the current code state, execute:
```bash
python -m unittest discover -v
python tests/run_mvp_validation.py
python gui_acceptance_test.py
python main.py
```

## 10. Final Supported-Scope Table
| Feature | Supported Status | Note |
|---|---|---|
| BPSK / QPSK | **Yes** | Fully deterministic demodulation |
| 8PSK / 16QAM / 64QAM / OFDM | No | Out of scope |
| Bandwidth / SNR / SymRate | **Yes** | -10dB relative bound, AWGN fractional density |
| Viterbi Rate-1/2 K=7 | **Yes** | Bounded auto-phase resolving |
| Block De-interleaving | **Yes** | Requires manual Rows/Cols |
| Reed-Solomon | **Yes** | Requires manual nsym |
| RS Frame Synchronization | **Yes** | Bounded search (-10 to +10 offsets, 0/180 phases) |
| Blind Interleaver/FEC detection | No | Out of scope |
| LDPC | No | Out of scope |
