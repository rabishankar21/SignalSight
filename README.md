# SignalSight

## Automated IQ/WAV Signal Analysis and Bitstream Recovery Platform

SignalSight is a desktop-based signal analysis and processing platform developed for **Smart India Hackathon 2026 – NTRO Problem Statement SIH26147**.

The platform is designed to process recorded **IQ and WAV signals**, extract signal parameters, analyze signal characteristics, identify supported modulation schemes, demodulate signals, perform de-interleaving and FEC processing, correlate bitstreams, and recover the resulting data.

**Team:** CyberNova  
**Project:** SignalSight  
**Problem Statement:** SIH26147  
**Domain:** Digital Signal Processing / Software Defined Radio / Digital Communications

---

## Key Features

- IQ signal ingestion
- WAV signal ingestion
- Signal pre-processing
- Spectrum / PSD analysis
- Waterfall visualization
- Constellation visualization
- SNR estimation
- Bandwidth estimation
- Symbol-rate estimation
- Carrier-offset estimation
- Modulation analysis
- Digital signal demodulation
- Bitstream generation and recovery
- Bitstream correlation
- Frame-boundary detection
- Interleaver detection
- De-interleaving
- FEC detection and decoding
- Recovered bitstream analysis

---

## Supported Modulation

SignalSight currently implements and validates:

- BPSK
- QPSK
- 8PSK
- 2FSK / BFSK
- 16QAM
- 64QAM

The modulation processing is scoped to the supported configuration space.

---

## Supported FEC

The current implementation includes:

- Viterbi
- Reed-Solomon
- Concatenated Viterbi + Reed-Solomon
- LDPC

The LDPC implementation is scoped to the validated `(256,128)` regular-code configuration with min-sum belief-propagation decoding.

---

## Supported De-interleaving

SignalSight implements:

- Block de-interleaving
- Convolutional de-interleaving
- Diagonal de-interleaving
- Pseudo-random de-interleaving

---

## Signal Parameter Extraction

The system estimates and extracts important signal parameters including:

- Sample rate
- Signal-to-noise ratio
- Bandwidth
- Symbol rate
- Carrier-frequency offset

These parameters are used by the subsequent signal-processing stages.

---

## Signal Visualization

SignalSight provides an integrated visualization workspace containing:

### Spectrum / PSD

Frequency-domain representation of the input signal for spectral analysis.

### Waterfall

Time-frequency visualization for observing signal behavior over time.

### Constellation

Complex-symbol visualization for supported PSK and QAM modulation schemes.

### Bitstream

Recovered bits can be inspected after demodulation, correlation, de-interleaving and FEC processing.

---
# Application Screenshots

SignalSight provides an integrated desktop workbench for signal analysis, visualization, demodulation, de-interleaving, FEC processing and bitstream recovery.

## Signal Overview

The Overview workspace displays the detected modulation, estimated SNR, bandwidth, symbol rate, signal information and processing status in a single interface.

<img src="https://github.com/rabishankar21/SignalSight/blob/main/docs/screenshorts/bitstream.png" alt="SignalSight Overview">

---

## Power Spectral Density

The Spectrum workspace provides a frequency-domain representation of the input signal for analysing its spectral characteristics and occupied bandwidth.

<img src="https://raw.githubusercontent.com/rabishankar21/SignalSight/main/docs/screenshots/spectrum.png" alt="SignalSight Spectrum">

---

## Waterfall / Spectrogram

The Waterfall workspace provides a time-frequency representation of the signal for observing signal activity and frequency behaviour over time.

<img src="https://raw.githubusercontent.com/rabishankar21/SignalSight/main/docs/screenshots/waterfall.png" alt="SignalSight Waterfall">

---

## Constellation Analysis

The Constellation workspace visualizes the complex I/Q symbols in the signal, providing a graphical representation of supported digital modulation characteristics.

<img src="https://raw.githubusercontent.com/rabishankar21/SignalSight/main/docs/screenshots/constellation.png" alt="SignalSight Constellation">

---

## Recovered Bitstream

The Bit Stream workspace displays the recovered binary data after demodulation, bit correlation, de-interleaving and FEC processing. The recovered data can be viewed in binary or hexadecimal representation.

<img src="https://raw.githubusercontent.com/rabishankar21/SignalSight/main/docs/screenshots/bitstream.png" alt="SignalSight Bit Stream">

---

# Processing Pipeline

```text
IQ / WAV Input
      |
      v
Signal Parsing
      |
      v
Pre-processing
      |
      v
Spectral Analysis
      |
      v
Parameter Extraction
      |
      v
Modulation Analysis
      |
      v
Demodulation
      |
      v
Bitstream Generation
      |
      v
Bit Correlation / Frame Alignment
      |
      v
Interleaver Analysis
      |
      v
De-interleaving
      |
      v
FEC Processing
      |
      v
Recovered Bitstream
