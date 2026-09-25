import os
import numpy as np
from PySide6.QtWidgets import (QStackedWidget, QListWidget, QFrame, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                               QSplitter, QGroupBox, QLabel, QComboBox,
                               QLineEdit, QPushButton, QFileDialog, QInputDialog,
                               QToolBar, QStatusBar, QTabWidget, QMessageBox, QCheckBox)
from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QPixmap

from signalsight.core.file_parser import load_file
from signalsight.core.preprocessor import preprocess
from signalsight.analysis.spectral import compute_psd, compute_spectrogram
from signalsight.analysis.estimator import estimate_bandwidth, estimate_snr, estimate_symbol_rate
from signalsight.analysis.modulation import classify_modulation
from signalsight.demod import demodulate_bpsk, demodulate_qpsk

from signalsight.gui.spectrum_widget import SpectrumWidget
from signalsight.gui.waterfall_widget import WaterfallWidget
from signalsight.gui.constellation_widget import ConstellationWidget
from signalsight.gui.bitstream_widget import BitstreamWidget


class AnalysisWorker(QThread):
    """Worker thread for signal analysis pipeline."""
    finished = Signal(dict)
    error = Signal(str)

    def __init__(self, samples, sample_rate, fft_size=4096):
        super().__init__()
        self.samples = samples
        self.sample_rate = sample_rate
        self.fft_size = fft_size

    def run(self):
        try:
            results = {}

            # Preprocessing
            processed = preprocess(self.samples, self.sample_rate,
                                   dc_remove=True, normalize=True)
            results['processed'] = processed

            # Spectral analysis
            freqs, psd_db = compute_psd(processed, self.sample_rate,
                                        fft_size=self.fft_size)
            results['psd_freqs'] = freqs
            results['psd_db'] = psd_db

            # Spectrogram / waterfall
            spec_fft = min(1024, self.fft_size)
            times, spec_freqs, power_db = compute_spectrogram(
                processed, self.sample_rate, fft_size=spec_fft)
            results['spec_times'] = times
            results['spec_freqs'] = spec_freqs
            results['spec_power'] = power_db

            # Parameter estimation
            bw, f_low, f_high = estimate_bandwidth(freqs, psd_db)
            results['bandwidth'] = bw
            results['freq_low'] = f_low
            results['freq_high'] = f_high

            if bw > 0:
                snr = estimate_snr(processed, self.sample_rate, bw)
            else:
                snr = 0.0
            results['snr'] = snr

            sym_rate, sym_conf = estimate_symbol_rate(processed, self.sample_rate)
            results['symbol_rate'] = sym_rate
            results['symbol_rate_conf'] = sym_conf

            # Modulation classification
            mod_candidates = classify_modulation(processed, self.sample_rate, sym_rate)
            results['modulation'] = mod_candidates

            self.finished.emit(results)
        except Exception as e:
            self.error.emit(str(e))


from signalsight.demod import demodulate_bpsk, demodulate_qpsk, demodulate_8psk, demodulate_fsk, demodulate_qam, ViterbiDecoder
from signalsight.interleave.block import block_deinterleave
from signalsight.fec.reed_solomon import ReedSolomonFEC

class DemodWorker(QThread):
    """Worker thread for demodulation."""
    finished = Signal(dict)
    error = Signal(str)

    def __init__(self, samples, sample_rate, mod_type, symbol_rate, rolloff=0.35, 
                 apply_viterbi=False, apply_deinterleave=False, int_rows=0, int_cols=0,
                 apply_rs=False, rs_nsym=0):
        super().__init__()
        self.samples = samples
        self.sample_rate = sample_rate
        self.mod_type = mod_type
        self.symbol_rate = symbol_rate
        self.rolloff = rolloff
        self.apply_viterbi = apply_viterbi
        self.apply_deinterleave = apply_deinterleave
        self.int_rows = int_rows
        self.int_cols = int_cols
        self.apply_rs = apply_rs
        self.rs_nsym = rs_nsym

    def run(self):
        try:
            processed = preprocess(self.samples, self.sample_rate,
                                   dc_remove=True, normalize=True)

            if self.mod_type == 'BPSK':
                result = demodulate_bpsk(processed, self.sample_rate,
                                         self.symbol_rate, self.rolloff)
            elif self.mod_type == 'QPSK':
                result = demodulate_qpsk(processed, self.sample_rate,
                                          self.symbol_rate, self.rolloff)
            elif self.mod_type == '8PSK':
                result = demodulate_8psk(processed, self.sample_rate,
                                          self.symbol_rate, self.rolloff)
            elif self.mod_type == '2FSK':
                result = demodulate_fsk(processed, self.sample_rate,
                                         self.symbol_rate, num_tones=2, rolloff=self.rolloff)
            elif self.mod_type == '16QAM':
                result = demodulate_qam(processed, self.sample_rate,
                                         self.symbol_rate, order=16, rolloff=self.rolloff)
            elif self.mod_type == '64QAM':
                result = demodulate_qam(processed, self.sample_rate,
                                         self.symbol_rate, order=64, rolloff=self.rolloff)
            else:
                self.error.emit(f"Unsupported modulation type: {self.mod_type}")
                return
                
            if 'bits' not in result:
                self.finished.emit(result)
                return

            bits = result['bits']
            result['raw_num_bits'] = len(bits)
            
            fec_status = []

            # Pipeline logic
            if self.apply_viterbi:
                decoder = ViterbiDecoder(k=7, polys=(0o171, 0o133))
                bits, phase = decoder.decode_auto_phase(bits)
                fec_status.append(f"Viterbi (Phase {phase})")
                result['viterbi_phase'] = phase
                
            if self.apply_rs or self.apply_deinterleave:
                # Blind alignment via RS success or brute force if no RS
                # We expect the delay to be around 5-10 bits due to filter span
                # For QPSK it might be different, so we search a small window
                block_sz = 1
                if self.apply_deinterleave:
                    block_sz = self.int_rows * self.int_cols
                
                best_bits = []
                best_status = []
                found = False
                
                # If RS is enabled, we use it as a checksum to find alignment
                search_offsets = range(-10, 10) if self.apply_rs else [0]
                search_phases = [0, 1] if self.apply_rs else [0]
                
                for phase in search_phases:
                    phase_bits = bits if phase == 0 else 1 - bits
                    for offset in search_offsets:
                        if offset < 0:
                            pad = np.zeros(-offset, dtype=np.uint8)
                            test_bits = np.concatenate([pad, phase_bits])
                        else:
                            test_bits = phase_bits[offset:]
                            
                        # Take exactly one block for alignment verification to avoid decoding noise/tail bits
                        if len(test_bits) > block_sz:
                            test_bits = test_bits[:block_sz]
                        elif len(test_bits) < block_sz:
                            test_bits = np.pad(test_bits, (0, block_sz - len(test_bits)), 'constant')
                            
                        rem = len(test_bits) % block_sz
                        if rem != 0:
                            test_bits = test_bits[:-rem]
                            
                        temp_status = []
                        if self.apply_deinterleave:
                            test_bits = block_deinterleave(test_bits, self.int_rows, self.int_cols)
                            temp_status.append(f"Deinterleaved ({self.int_rows}x{self.int_cols})")
                            
                        if self.apply_rs:
                            rs = ReedSolomonFEC(nsym=self.rs_nsym)
                            decoded_bits = rs.decode_bits(test_bits)
                            if len(decoded_bits) > 0:
                                # Success!
                                test_bits = decoded_bits
                                temp_status.append(f"RS decoded (Phase {phase}, Offset {offset})")
                                best_bits = test_bits
                                best_status = temp_status
                                found = True
                                break
                        else:
                            best_bits = test_bits
                            best_status = temp_status
                            found = True
                            break
                            
                    if found:
                        break
                        
                if self.apply_rs and not found:
                    self.error.emit("Reed-Solomon decoding failed (too many errors or no alignment found).")
                    return
                    
                bits = best_bits
                fec_status.extend(best_status)

            result['bits'] = bits
            result['num_bits'] = len(bits)
            result['fec_status'] = " | ".join(fec_status) if fec_status else None

            self.finished.emit(result)
        except Exception as e:
            self.error.emit(str(e))



class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('SignalSight - Professional Signal Analysis Workbench')
        self.resize(1440, 900)
        self.setMinimumSize(1200, 720)

        # State
        self.current_samples = None
        self.sample_rate = 0.0
        self.metadata = {}
        self.analysis_results = {}
        self.carrier_offset = 0.0
        self.worker = None

        self.setup_ui()

    def setup_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # --- LEFT SIDEBAR ---
        left_sidebar = QWidget()
        left_sidebar.setObjectName("left_panel")
        left_sidebar.setFixedWidth(240)
        left_layout = QVBoxLayout(left_sidebar)
        left_layout.setContentsMargins(24, 32, 24, 32)
        left_layout.setSpacing(16)
        
        # Logo / Title
        app_title = QLabel()
        app_title.setObjectName("app_title")
        logo_pixmap = QPixmap(r"C:\Users\RABI SHANKAR SINGH\Downloads\SIH-26147\SignalSight\logo\logo1.png")
        if not logo_pixmap.isNull():
            app_title.setPixmap(logo_pixmap.scaledToWidth(180, Qt.SmoothTransformation))
        else:
            app_title.setText("SIGNALSIGHT")
        left_layout.addWidget(app_title)
        left_layout.addSpacing(16)
        
        # Navigation
        lbl_ws = QLabel("WORKSPACE")
        lbl_ws.setObjectName("sidebar_header")
        left_layout.addWidget(lbl_ws)
        
        self.nav_list = QListWidget()
        self.nav_list.setObjectName("nav_list")
        self.nav_list.addItems(["Overview", "Spectrum", "Waterfall", "Constellation", "Bit Stream"])
        self.nav_list.setCurrentRow(0)
        self.nav_list.currentRowChanged.connect(self.on_nav_changed)
        self.nav_list.setMinimumHeight(240)
        left_layout.addWidget(self.nav_list)
        
        left_layout.addStretch()
        
        # File info (Bottom left)
        lbl_file = QLabel("FILE")
        lbl_file.setObjectName("sidebar_header")
        left_layout.addWidget(lbl_file)
        
        fi_layout = QVBoxLayout()
        fi_layout.setSpacing(8)
        self.lbl_name = QLabel("Name: -")
        self.lbl_format = QLabel("Format: -")
        self.lbl_srate = QLabel("Sample Rate: -")
        self.lbl_samples = QLabel("Samples: -")
        self.lbl_duration = QLabel("Duration: -")
        
        for lbl in [self.lbl_name, self.lbl_format, self.lbl_srate, self.lbl_samples, self.lbl_duration]:
            lbl.setStyleSheet("color: #9AA5BA; font-size: 12px;")
            fi_layout.addWidget(lbl)
            
        left_layout.addLayout(fi_layout)
        
        main_layout.addWidget(left_sidebar)
        
        # Splitter for center/right
        self.splitter = QSplitter(Qt.Horizontal)
        self.splitter.setHandleWidth(1)
        main_layout.addWidget(self.splitter, 1)

        # --- CENTRAL AREA ---
        center_widget = QWidget()
        center_widget.setObjectName("center_panel")
        center_layout = QVBoxLayout(center_widget)
        center_layout.setContentsMargins(32, 32, 32, 0)
        center_layout.setSpacing(24)
        
        # Top Bar
        top_bar_layout = QHBoxLayout()
        top_bar_layout.setContentsMargins(0, 0, 0, 0)
        
        title_layout = QVBoxLayout()
        title_layout.setSpacing(4)
        self.lbl_page_title = QLabel("Overview")
        self.lbl_page_title.setObjectName("page_title")
        self.lbl_page_subtitle = QLabel("No file loaded")
        self.lbl_page_subtitle.setObjectName("page_subtitle")
        title_layout.addWidget(self.lbl_page_title)
        title_layout.addWidget(self.lbl_page_subtitle)
        
        top_bar_layout.addLayout(title_layout)
        top_bar_layout.addStretch()
        
        # Toolbar actions
        btn_clear = QPushButton("Clear")
        btn_open = QPushButton("Open File")
        btn_open.setMinimumWidth(120)
        btn_open.clicked.connect(self.on_open_file)
        btn_clear.clicked.connect(self.on_clear)
        top_bar_layout.addWidget(btn_clear)
        top_bar_layout.addSpacing(12)
        top_bar_layout.addWidget(btn_open)
        
        center_layout.addLayout(top_bar_layout)
        
        # Stacked Widget for Visualizations
        self.stacked_vis = QStackedWidget()
        
        # 0: Overview
        overview_widget = QWidget()
        overview_widget.setObjectName("overview_page")
        overview_layout = QVBoxLayout(overview_widget)
        overview_layout.setContentsMargins(32, 24, 32, 24)
        overview_layout.setSpacing(32)
        
        # Metrics Cards inside Overview
        metrics_layout = QHBoxLayout()
        metrics_layout.setSpacing(16)
        
        self.lbl_mod = QLabel("-")
        self.lbl_snr = QLabel("-")
        self.lbl_bw = QLabel("-")
        self.lbl_symrate = QLabel("-")
        self.lbl_conf = QLabel("-")
        
        def create_metric_card(title, lbl_val):
            card = QFrame()
            card.setProperty("class", "metric_card")
            card_lay = QVBoxLayout(card)
            card_lay.setContentsMargins(16, 16, 16, 16)
            t = QLabel(title)
            t.setProperty("class", "metric_label")
            lbl_val.setProperty("class", "metric_value")
            
            # Center alignments
            t.setAlignment(Qt.AlignCenter)
            lbl_val.setAlignment(Qt.AlignCenter)
            card_lay.setAlignment(Qt.AlignCenter)
            
            card_lay.addWidget(t)
            card_lay.addSpacing(8)
            card_lay.addWidget(lbl_val)
            return card
            
        metrics_layout.addWidget(create_metric_card("Modulation", self.lbl_mod))
        metrics_layout.addWidget(create_metric_card("SNR", self.lbl_snr))
        metrics_layout.addWidget(create_metric_card("Bandwidth", self.lbl_bw))
        metrics_layout.addWidget(create_metric_card("Symbol Rate", self.lbl_symrate))
        
        overview_layout.addLayout(metrics_layout)
        
        # Signal Info Area inside Overview
        sig_info_lbl = QLabel("SIGNAL INFORMATION")
        sig_info_lbl.setObjectName("section_title")
        overview_layout.addWidget(sig_info_lbl)
        
        from PySide6.QtWidgets import QGridLayout
        self.ov_info_container = QFrame()
        self.ov_info_container.setProperty("class", "group_card")
        ov_info_layout = QGridLayout(self.ov_info_container)
        ov_info_layout.setContentsMargins(20, 20, 20, 20)
        ov_info_layout.setSpacing(12)
        
        self.lbl_ov_file = QLabel("-")
        self.lbl_ov_format = QLabel("-")
        self.lbl_ov_srate = QLabel("-")
        self.lbl_ov_samples = QLabel("-")
        self.lbl_ov_duration = QLabel("-")
        self.lbl_ov_carrier = QLabel("-")
        
        keys = ["File", "Format", "Sample Rate", "Samples", "Duration", "Carrier Offset"]
        vals = [self.lbl_ov_file, self.lbl_ov_format, self.lbl_ov_srate, self.lbl_ov_samples, self.lbl_ov_duration, self.lbl_ov_carrier]
        
        for i, (k, v) in enumerate(zip(keys, vals)):
            k_lbl = QLabel(k)
            k_lbl.setStyleSheet("color: #9AA5BA; font-size: 13px; min-width: 140px;")
            v.setStyleSheet("color: #F3F5FA; font-size: 13px; font-weight: 500;")
            ov_info_layout.addWidget(k_lbl, i, 0)
            ov_info_layout.addWidget(v, i, 1)
        ov_info_layout.setColumnStretch(2, 1)
            
        ov_info_layout.setColumnStretch(1, 1)
            
        overview_layout.addWidget(self.ov_info_container)
        
        # Processing Status
        sig_status_lbl = QLabel("PROCESSING STATUS")
        sig_status_lbl.setObjectName("section_title")
        overview_layout.addWidget(sig_status_lbl)
        
        self.lbl_ov_status_analysis = QLabel("Analysis: Pending")
        self.lbl_ov_status_demod = QLabel("Demodulation: Pending")
        self.lbl_ov_status_fec = QLabel("FEC: Pending")
        
        for lbl in [self.lbl_ov_status_analysis, self.lbl_ov_status_demod, self.lbl_ov_status_fec]:
            lbl.setStyleSheet("color: #9AA5BA; font-size: 14px;")
            overview_layout.addWidget(lbl)
            
        overview_layout.addStretch()
        
        self.tab_spectrum = SpectrumWidget()
        self.tab_waterfall = WaterfallWidget()
        self.tab_constellation = ConstellationWidget()
        self.tab_bitstream = BitstreamWidget()
        
        def wrap_plot(title, subtitle, widget):
            container = QWidget()
            lay = QVBoxLayout(container)
            lay.setContentsMargins(0, 0, 0, 0)
            
            t = QLabel(title.upper())
            t.setStyleSheet("font-size: 11px; font-weight: 700; color: #9AA5BA; letter-spacing: 1px; margin-bottom: 8px;")
            lay.addWidget(t)
            
            card = QFrame()
            card.setStyleSheet("background-color: #131722; border: 1px solid transparent; border-radius: 8px;")
            card_lay = QVBoxLayout(card)
            card_lay.setContentsMargins(0, 0, 0, 0)
            card_lay.addWidget(widget)
            lay.addWidget(card)
            return container
            
        self.stacked_vis.addWidget(overview_widget)      # 0
        self.stacked_vis.addWidget(wrap_plot("POWER SPECTRAL DENSITY", "", self.tab_spectrum))
        self.stacked_vis.addWidget(wrap_plot("WATERFALL / SPECTROGRAM", "", self.tab_waterfall))
        self.stacked_vis.addWidget(wrap_plot("CONSTELLATION DIAGRAM", "", self.tab_constellation))
        self.stacked_vis.addWidget(wrap_plot("Bit Stream", "Recovered data", self.tab_bitstream))
        
        center_layout.addWidget(self.stacked_vis, 1)
        
        # Status Bar Footer
        self.status_bar = QStatusBar()
        self.status_bar.showMessage("Ready")
        center_layout.addWidget(self.status_bar)
        
        self.splitter.addWidget(center_widget)

        # --- RIGHT PANEL ---
        right_panel = QWidget()
        right_panel.setObjectName("right_panel")
        right_panel.setMinimumWidth(340)
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(24, 24, 24, 24)
        right_layout.setSpacing(16)
        
        lbl_proc = QLabel("PROCESSING")
        lbl_proc.setObjectName("sidebar_header")
        right_layout.addWidget(lbl_proc)
        
        # Analysis Controls
        analysis_group = QFrame()
        analysis_group.setProperty("class", "group_card")
        al_layout = QVBoxLayout(analysis_group)
        al_layout.setContentsMargins(16, 12, 16, 12)
        al_layout.setSpacing(12)
        
        lbl_al_title = QLabel("ANALYSIS")
        lbl_al_title.setStyleSheet("color: #9AA5BA; font-size: 11px; font-weight: 700; letter-spacing: 1px;")
        al_layout.addWidget(lbl_al_title)
        al_layout.addSpacing(4)
        
        row1 = QHBoxLayout()
        row1.addWidget(QLabel("FFT Size"))
        self.combo_fft = QComboBox()
        self.combo_fft.addItems(["512", "1024", "2048", "4096", "8192"])
        self.combo_fft.setCurrentText("4096")
        row1.addWidget(self.combo_fft)
        al_layout.addLayout(row1)
        
        row2 = QHBoxLayout()
        row2.addWidget(QLabel("Sample Rate"))
        self.edit_srate = QLineEdit()
        self.edit_srate.setPlaceholderText("Hz")
        row2.addWidget(self.edit_srate)
        al_layout.addLayout(row2)
        
        btn_analyze = QPushButton("Run Analysis")
        btn_analyze.setObjectName("primary_btn")
        btn_analyze.clicked.connect(self.on_run_analysis)
        al_layout.addWidget(btn_analyze)
        right_layout.addWidget(analysis_group)
        
        # Demodulation Controls
        demod_group = QFrame()
        demod_group.setProperty("class", "group_card")
        dl_layout = QVBoxLayout(demod_group)
        dl_layout.setContentsMargins(16, 12, 16, 12)
        dl_layout.setSpacing(12)
        
        lbl_dl_title = QLabel("DEMODULATION")
        lbl_dl_title.setStyleSheet("color: #9AA5BA; font-size: 11px; font-weight: 700; letter-spacing: 1px;")
        dl_layout.addWidget(lbl_dl_title)
        dl_layout.addSpacing(4)
        
        row3 = QHBoxLayout()
        row3.addWidget(QLabel("Mod Type"))
        self.combo_mod = QComboBox()
        self.combo_mod.addItems(["Auto", "BPSK", "QPSK", "8PSK", "2FSK", "16QAM", "64QAM"])
        row3.addWidget(self.combo_mod)
        dl_layout.addLayout(row3)
        
        row4 = QHBoxLayout()
        row4.addWidget(QLabel("Symbol Rate"))
        self.edit_symrate = QLineEdit()
        self.edit_symrate.setPlaceholderText("sps")
        row4.addWidget(self.edit_symrate)
        dl_layout.addLayout(row4)
        
        row5 = QHBoxLayout()
        row5.addWidget(QLabel("Rolloff"))
        self.edit_rolloff = QLineEdit("0.35")
        row5.addWidget(self.edit_rolloff)
        dl_layout.addLayout(row5)
        
        btn_demod = QPushButton("Demodulate")
        btn_demod.setObjectName("primary_btn")
        btn_demod.clicked.connect(self.on_demodulate)
        dl_layout.addWidget(btn_demod)
        right_layout.addWidget(demod_group)
        
        # FEC Controls
        fec_group = QFrame()
        fec_group.setProperty("class", "group_card")
        fec_layout = QVBoxLayout(fec_group)
        fec_layout.setContentsMargins(16, 12, 16, 12)
        fec_layout.setSpacing(16)
        
        lbl_fec_title = QLabel("FEC / BIT PROCESSING")
        lbl_fec_title.setStyleSheet("color: #9AA5BA; font-size: 11px; font-weight: 700; letter-spacing: 1px;")
        fec_layout.addWidget(lbl_fec_title)
        fec_layout.addSpacing(2)
        
        self.chk_viterbi = QCheckBox("Viterbi FEC (Rate 1/2, K=7)")
        fec_layout.addWidget(self.chk_viterbi)
        
        # Block De-interleave
        di_lay = QVBoxLayout()
        di_lay.setSpacing(8)
        self.chk_interleave = QCheckBox("Block De-interleave")
        di_lay.addWidget(self.chk_interleave)
        
        int_grid = QHBoxLayout()
        int_grid.setContentsMargins(24, 0, 0, 0) # Indent the inputs under the checkbox
        self.edit_int_rows = QLineEdit()
        self.edit_int_rows.setPlaceholderText("Rows")
        self.edit_int_cols = QLineEdit()
        self.edit_int_cols.setPlaceholderText("Cols")
        int_grid.addWidget(self.edit_int_rows)
        int_grid.addWidget(self.edit_int_cols)
        di_lay.addLayout(int_grid)
        fec_layout.addLayout(di_lay)
        
        # RS
        rs_lay = QVBoxLayout()
        rs_lay.setSpacing(8)
        self.chk_rs = QCheckBox("Reed-Solomon")
        rs_lay.addWidget(self.chk_rs)
        
        rs_input_lay = QHBoxLayout()
        rs_input_lay.setContentsMargins(24, 0, 0, 0)
        self.edit_rs_nsym = QLineEdit()
        self.edit_rs_nsym.setPlaceholderText("nsym")
        rs_input_lay.addWidget(self.edit_rs_nsym)
        rs_lay.addLayout(rs_input_lay)
        fec_layout.addLayout(rs_lay)
        
        right_layout.addWidget(fec_group)
        
        # State toggle bindings
        self.chk_interleave.toggled.connect(self.edit_int_rows.setEnabled)
        self.chk_interleave.toggled.connect(self.edit_int_cols.setEnabled)
        self.chk_rs.toggled.connect(self.edit_rs_nsym.setEnabled)
        
        self.edit_int_rows.setEnabled(False)
        self.edit_int_cols.setEnabled(False)
        self.edit_rs_nsym.setEnabled(False)
        
        right_layout.addStretch()
        self.splitter.addWidget(right_panel)
        
        self.splitter.setStretchFactor(0, 1)
        self.splitter.setStretchFactor(1, 0)

    def on_nav_changed(self, index):
        self.stacked_vis.setCurrentIndex(index)
        self.lbl_page_title.setText(self.nav_list.item(index).text())

    # ---- Handlers ----



    def on_open_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Open Signal File", "",
            "Signal Files (*.iq *.wav *.bin *.raw);;All Files (*)")
        if not file_path:
            return

        # For IQ files, ask for sample rate
        ext = os.path.splitext(file_path)[1].lower()
        sr_input = None
        if ext in ['.iq', '.bin', '.raw']:
            srate, ok = QInputDialog.getDouble(
                self, "Sample Rate",
                "Enter sample rate (Hz):",
                400000, 1, 1e9, 0)
            if not ok:
                return
            sr_input = srate

        self.status_bar.showMessage(f"Loading {os.path.basename(file_path)}...")
        try:
            samples, sr, meta = load_file(file_path, sample_rate=sr_input)
            self.current_samples = samples
            self.sample_rate = sr
            self.metadata = meta

            # Update file info labels

            self.lbl_name.setText(f"Name: {meta.get('filename', '-')}")
            self.lbl_format.setText(f"Format: {meta.get('format', '-')}")
            self.lbl_srate.setText(f"Sample Rate: {sr:,.0f} Hz")
            self.lbl_samples.setText(f"Samples: {meta.get('num_samples', 0):,}")
            self.lbl_duration.setText(f"Duration: {meta.get('duration_sec', 0):.4f} s")
            
            self.lbl_page_subtitle.setText(f"{meta.get('filename', '-')}")
            self.lbl_ov_file.setText(f"{meta.get('filename', '-')}")
            self.lbl_ov_format.setText(f"{meta.get('format', '-')}")
            self.lbl_ov_srate.setText(f"{sr:,.0f} Hz")
            self.lbl_ov_samples.setText(f"{meta.get('num_samples', 0):,}")
            self.lbl_ov_duration.setText(f"{meta.get('duration_sec', 0):.4f} s")
            self.lbl_ov_carrier.setText(f"-")
            
            self.lbl_ov_status_analysis.setText("Analysis: Pending")
            self.lbl_ov_status_demod.setText("Demodulation: Pending")
            self.lbl_ov_status_fec.setText("FEC: Pending")

            self.edit_srate.setText(str(int(sr)))

            self.status_bar.showMessage(
                f"Loaded {meta.get('filename', '')} - {meta.get('num_samples', 0):,} samples. Running analysis...")

            # Automatically run analysis
            self.on_run_analysis()

        except Exception as e:
            QMessageBox.critical(self, "Load Error", str(e))
            self.status_bar.showMessage("Load failed.")

    def on_run_analysis(self):
        if self.current_samples is None:
            self.status_bar.showMessage("No signal loaded.")
            return

        # Read user-configurable sample rate
        try:
            sr_text = self.edit_srate.text().strip()
            if sr_text:
                self.sample_rate = float(sr_text)
        except ValueError:
            pass

        fft_size = int(self.combo_fft.currentText())
        self.status_bar.showMessage("Running analysis pipeline...")

        self.worker = AnalysisWorker(self.current_samples, self.sample_rate, fft_size)
        self.worker.finished.connect(self.handle_analysis_results)
        self.worker.error.connect(self.handle_error)
        self.worker.start()

    def on_demodulate(self):
        if self.current_samples is None:
            self.status_bar.showMessage("No signal loaded.")
            return

        # Determine modulation type
        mod_type = self.combo_mod.currentText()
        if mod_type == "Auto":
            if self.analysis_results and 'modulation' in self.analysis_results:
                candidates = self.analysis_results['modulation']
                if candidates:
                    mod_type = candidates[0]['type']
                else:
                    mod_type = 'BPSK'
            else:
                self.status_bar.showMessage("Run analysis first or select modulation manually.")
                return

        if mod_type not in ('BPSK', 'QPSK'):
            QMessageBox.warning(self, "Unsupported",
                                f"Demodulation for {mod_type} is not implemented in MVP.\n"
                                "Only BPSK and QPSK are supported.")
            return

        # Get symbol rate
        sym_rate = 0.0
        try:
            sr_text = self.edit_symrate.text().strip()
            if sr_text:
                sym_rate = float(sr_text)
        except ValueError:
            pass

        if sym_rate <= 0:
            if self.analysis_results and 'symbol_rate' in self.analysis_results:
                sym_rate = self.analysis_results['symbol_rate']
            if sym_rate <= 0:
                QMessageBox.warning(self, "Symbol Rate",
                                    "Could not determine symbol rate.\n"
                                    "Please enter it manually.")
                return

        # Get rolloff
        try:
            rolloff = float(self.edit_rolloff.text().strip())
        except ValueError:
            rolloff = 0.35

        self.status_bar.showMessage(f"Demodulating {mod_type} at {sym_rate:.0f} sps...")
        
        apply_viterbi = self.chk_viterbi.isChecked()
        apply_deinterleave = self.chk_interleave.isChecked()
        apply_rs = self.chk_rs.isChecked()
        
        int_rows = 0
        int_cols = 0
        if apply_deinterleave:
            try:
                int_rows = int(self.edit_int_rows.text().strip())
                int_cols = int(self.edit_int_cols.text().strip())
                if int_rows <= 0 or int_cols <= 0:
                    raise ValueError
            except ValueError:
                QMessageBox.warning(self, "Invalid Parameters", "Block De-interleave requires valid positive integer Rows and Cols.")
                return
                
        rs_nsym = 0
        if apply_rs:
            try:
                rs_nsym = int(self.edit_rs_nsym.text().strip())
                if rs_nsym <= 0:
                    raise ValueError
            except ValueError:
                QMessageBox.warning(self, "Invalid Parameters", "Reed-Solomon requires a valid positive integer nsym.")
                return

        self.worker = DemodWorker(self.current_samples, self.sample_rate,
                                  mod_type, sym_rate, rolloff, apply_viterbi,
                                  apply_deinterleave, int_rows, int_cols,
                                  apply_rs, rs_nsym)
        self.worker.finished.connect(self.handle_demod_results)
        self.worker.error.connect(self.handle_error)
        self.worker.start()


    def on_clear(self):
        self.tab_spectrum.clear_plot()
        self.tab_waterfall.clear_plot()
        self.tab_constellation.clear_plot()
        self.tab_bitstream.clear_data()

        self.current_samples = None
        self.sample_rate = 0.0
        self.metadata = {}
        self.analysis_results = {}

        self.lbl_name.setText("Name: -")
        self.lbl_format.setText("Format: -")
        self.lbl_srate.setText("Sample Rate: -")
        self.lbl_samples.setText("Samples: -")
        self.lbl_duration.setText("Duration: -")
        
        self.lbl_bw.setText("-")
        self.lbl_snr.setText("-")
        self.lbl_symrate.setText("-")
        self.lbl_mod.setText("-")
        self.lbl_conf.setText("-")
        
        self.lbl_page_subtitle.setText("No file loaded")
        
        self.lbl_ov_file.setText("-")
        self.lbl_ov_format.setText("-")
        self.lbl_ov_srate.setText("-")
        self.lbl_ov_samples.setText("-")
        self.lbl_ov_duration.setText("-")
        self.lbl_ov_carrier.setText("-")
        
        self.lbl_ov_status_analysis.setText("Analysis: Pending")
        self.lbl_ov_status_demod.setText("Demodulation: Pending")
        self.lbl_ov_status_fec.setText("FEC: Pending")

        self.edit_srate.clear()
        self.edit_symrate.clear()
        self.status_bar.showMessage("Ready")

    # ---- Result handlers ----

    def handle_analysis_results(self, results):
        self.analysis_results = results

        # Update spectrum plot
        if 'psd_freqs' in results and 'psd_db' in results:
            self.tab_spectrum.update_plot(results['psd_freqs'], results['psd_db'])

        # Update waterfall
        if 'spec_times' in results and 'spec_freqs' in results and 'spec_power' in results:
            self.tab_waterfall.update_plot(
                results['spec_times'], results['spec_freqs'], results['spec_power'])

        # Update detected parameters
        if 'bandwidth' in results:
            bw = results['bandwidth']
            if bw >= 1000:
                self.lbl_bw.setText(f"{bw/1000:.2f} kHz")
            else:
                self.lbl_bw.setText(f"{bw:.1f} Hz")

        if 'snr' in results:
            self.lbl_snr.setText(f"{results['snr']:.1f} dB")

        if 'symbol_rate' in results:
            sr = results['symbol_rate']
            if sr >= 1000:
                self.lbl_symrate.setText(f"{sr/1000:.2f} ksps")
            else:
                self.lbl_symrate.setText(f"{sr:.1f} sps")
            self.edit_symrate.setText(f"{sr:.0f}")

        if 'modulation' in results and results['modulation']:
            top = results['modulation'][0]
            self.lbl_mod.setText(f"{top['type']}")
            self.lbl_conf.setText(f"{top['confidence']:.2f}")


        self.nav_list.setCurrentRow(1)  # Switch to spectrum tab
        self.status_bar.showMessage("Analysis complete.")
        self.lbl_ov_status_analysis.setText("Analysis: Complete (PSD & Parameters extracted)")


    def handle_demod_results(self, results):
        # Update constellation
        if 'constellation' in results:
            self.tab_constellation.update_plot(results['constellation'])

        # Update bit stream
        if 'bits' in results:
            self.tab_bitstream.update_data(results['bits'])

        num_syms = results.get('num_symbols', 0)
        num_bits = results.get('num_bits', 0)
        f_off = results.get('carrier_freq_offset', 0)


        self.nav_list.setCurrentRow(3)  # Switch to constellation tab
        
        fec_status = results.get('fec_status', None)
        raw_bits = results.get('raw_num_bits', num_bits)

        if fec_status:
            msg = (f"Demod complete. Raw: {raw_bits} bits | "
                   f"FEC: {fec_status} | Recovered: {num_bits} bits")
            self.lbl_ov_status_fec.setText(f"FEC: {fec_status}")
        else:
            msg = (f"Demod complete. {num_syms} symbols, {num_bits} raw bits recovered. "
                   f"Carrier offset: {f_off:.1f} Hz")
            self.lbl_ov_status_fec.setText(f"FEC: OFF")
                   
        self.status_bar.showMessage(msg)
        self.lbl_ov_carrier.setText(f"{f_off:.1f} Hz")
        self.lbl_ov_status_demod.setText(f"Demodulation: Complete ({num_bits} bits recovered)")


    def handle_error(self, error_msg):
        QMessageBox.critical(self, "Processing Error", error_msg)
        self.status_bar.showMessage(f"Error: {error_msg}")

