import os
import re

with open("signalsight/gui/main_window.py", "r") as f:
    mw_content = f.read()

mw_new_setup = """class MainWindow(QMainWindow):
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
        app_title = QLabel("SIGNALSIGHT")
        app_title.setObjectName("app_title")
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
        self.nav_list.setFixedHeight(180)
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
        overview_layout.setContentsMargins(0, 16, 0, 0)
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
            card_lay.setContentsMargins(20, 20, 20, 20)
            t = QLabel(title)
            t.setProperty("class", "metric_label")
            lbl_val.setProperty("class", "metric_value")
            card_lay.addWidget(t)
            card_lay.addSpacing(4)
            card_lay.addWidget(lbl_val)
            card_lay.addStretch()
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
        
        self.ov_info_container = QWidget()
        ov_info_layout = QVBoxLayout(self.ov_info_container)
        ov_info_layout.setContentsMargins(0, 0, 0, 0)
        ov_info_layout.setSpacing(12)
        
        self.lbl_ov_file = QLabel("File: -")
        self.lbl_ov_format = QLabel("Format: -")
        self.lbl_ov_srate = QLabel("Sample Rate: -")
        self.lbl_ov_samples = QLabel("Samples: -")
        self.lbl_ov_duration = QLabel("Duration: -")
        self.lbl_ov_carrier = QLabel("Carrier Offset: -")
        
        for lbl in [self.lbl_ov_file, self.lbl_ov_format, self.lbl_ov_srate, self.lbl_ov_samples, self.lbl_ov_duration, self.lbl_ov_carrier]:
            lbl.setStyleSheet("color: #F3F5FA; font-size: 14px;")
            ov_info_layout.addWidget(lbl)
            
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
            
            card = QFrame()
            card.setStyleSheet("background-color: #131722; border: 1px solid transparent; border-radius: 8px;")
            card_lay = QVBoxLayout(card)
            card_lay.setContentsMargins(0, 0, 0, 0)
            card_lay.addWidget(widget)
            lay.addWidget(card)
            return container
            
        self.stacked_vis.addWidget(overview_widget)      # 0
        self.stacked_vis.addWidget(wrap_plot("Power Spectral Density", "Frequency domain", self.tab_spectrum))
        self.stacked_vis.addWidget(wrap_plot("Waterfall", "Time-frequency", self.tab_waterfall))
        self.stacked_vis.addWidget(wrap_plot("Constellation", "Phase map", self.tab_constellation))
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
        right_layout.setContentsMargins(24, 32, 24, 32)
        right_layout.setSpacing(24)
        
        lbl_proc = QLabel("PROCESSING")
        lbl_proc.setObjectName("sidebar_header")
        right_layout.addWidget(lbl_proc)
        
        # Analysis Controls
        analysis_group = QGroupBox("ANALYSIS")
        al_layout = QVBoxLayout(analysis_group)
        al_layout.setSpacing(12)
        
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
        al_layout.addSpacing(8)
        al_layout.addWidget(btn_analyze)
        right_layout.addWidget(analysis_group)
        
        # Demodulation Controls
        demod_group = QGroupBox("DEMODULATION")
        dl_layout = QVBoxLayout(demod_group)
        dl_layout.setSpacing(12)
        
        row3 = QHBoxLayout()
        row3.addWidget(QLabel("Mod Type"))
        self.combo_mod = QComboBox()
        self.combo_mod.addItems(["Auto", "BPSK", "QPSK"])
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
        dl_layout.addSpacing(8)
        dl_layout.addWidget(btn_demod)
        right_layout.addWidget(demod_group)
        
        # FEC Controls
        fec_group = QGroupBox("FEC / BIT PROCESSING")
        fec_layout = QVBoxLayout(fec_group)
        fec_layout.setSpacing(16)
        
        self.chk_viterbi = QCheckBox("Viterbi FEC (Rate 1/2, K=7)")
        fec_layout.addWidget(self.chk_viterbi)
        
        # Block De-interleave
        di_cont = QWidget()
        di_lay = QVBoxLayout(di_cont)
        di_lay.setContentsMargins(0, 0, 0, 0)
        di_lay.setSpacing(8)
        self.chk_interleave = QCheckBox("Block De-interleave")
        di_lay.addWidget(self.chk_interleave)
        
        int_grid = QHBoxLayout()
        self.edit_int_rows = QLineEdit()
        self.edit_int_rows.setPlaceholderText("Rows")
        self.edit_int_cols = QLineEdit()
        self.edit_int_cols.setPlaceholderText("Cols")
        int_grid.addWidget(self.edit_int_rows)
        int_grid.addWidget(self.edit_int_cols)
        di_lay.addLayout(int_grid)
        fec_layout.addWidget(di_cont)
        
        # RS
        rs_cont = QWidget()
        rs_lay = QVBoxLayout(rs_cont)
        rs_lay.setContentsMargins(0, 0, 0, 0)
        rs_lay.setSpacing(8)
        self.chk_rs = QCheckBox("Reed-Solomon")
        rs_lay.addWidget(self.chk_rs)
        
        self.edit_rs_nsym = QLineEdit()
        self.edit_rs_nsym.setPlaceholderText("nsym")
        rs_lay.addWidget(self.edit_rs_nsym)
        fec_layout.addWidget(rs_cont)
        
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

"""

start_idx = mw_content.find("class MainWindow(QMainWindow):")
end_idx = mw_content.find("    # ---- Handlers ----")

new_content = mw_content[:start_idx] + mw_new_setup + mw_content[end_idx:]

# Update the handlers to populate the new labels!

# In `on_open_file` (after line 428):
open_file_replace = """
            self.lbl_name.setText(f"Name: {meta.get('filename', '-')}")
            self.lbl_format.setText(f"Format: {meta.get('format', '-')}")
            self.lbl_srate.setText(f"Sample Rate: {sr:,.0f} Hz")
            self.lbl_samples.setText(f"Samples: {meta.get('num_samples', 0):,}")
            self.lbl_duration.setText(f"Duration: {meta.get('duration_sec', 0):.4f} s")
            
            self.lbl_page_subtitle.setText(f"{meta.get('filename', '-')}")
            self.lbl_ov_file.setText(f"File: {meta.get('filename', '-')}")
            self.lbl_ov_format.setText(f"Format: {meta.get('format', '-')}")
            self.lbl_ov_srate.setText(f"Sample Rate: {sr:,.0f} Hz")
            self.lbl_ov_samples.setText(f"Samples: {meta.get('num_samples', 0):,}")
            self.lbl_ov_duration.setText(f"Duration: {meta.get('duration_sec', 0):.4f} s")
            self.lbl_ov_carrier.setText(f"Carrier Offset: -")
            
            self.lbl_ov_status_analysis.setText("Analysis: Pending")
            self.lbl_ov_status_demod.setText("Demodulation: Pending")
            self.lbl_ov_status_fec.setText("FEC: Pending")
"""
new_content = re.sub(r'            self.lbl_name.setText.*?self.lbl_duration.setText.*?s"\)', open_file_replace, new_content, flags=re.DOTALL)

# In `on_clear`:
clear_replace = """
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
        
        self.lbl_ov_file.setText("File: -")
        self.lbl_ov_format.setText("Format: -")
        self.lbl_ov_srate.setText("Sample Rate: -")
        self.lbl_ov_samples.setText("Samples: -")
        self.lbl_ov_duration.setText("Duration: -")
        self.lbl_ov_carrier.setText("Carrier Offset: -")
        
        self.lbl_ov_status_analysis.setText("Analysis: Pending")
        self.lbl_ov_status_demod.setText("Demodulation: Pending")
        self.lbl_ov_status_fec.setText("FEC: Pending")

        self.edit_srate.clear()
        self.edit_symrate.clear()
        self.status_bar.showMessage("Ready")
"""
new_content = re.sub(r'    def on_clear\(self\):.*?    # ---- Result handlers ----', clear_replace + '\n    # ---- Result handlers ----', new_content, flags=re.DOTALL)

# In `handle_analysis_results`:
ha_replace = """
        self.nav_list.setCurrentRow(1)  # Switch to spectrum tab
        self.status_bar.showMessage("Analysis complete.")
        self.lbl_ov_status_analysis.setText("Analysis: Complete (PSD & Parameters extracted)")
"""
new_content = re.sub(r'        self.nav_list.setCurrentRow\(1\).*?Analysis complete."\)', ha_replace, new_content, flags=re.DOTALL)

# In `handle_demod_results`:
hd_replace = """
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
        self.lbl_ov_carrier.setText(f"Carrier Offset: {f_off:.1f} Hz")
        self.lbl_ov_status_demod.setText(f"Demodulation: Complete ({num_bits} bits recovered)")
"""
new_content = re.sub(r'        self.nav_list.setCurrentRow\(3\).*?self.status_bar.showMessage\(msg\)', hd_replace, new_content, flags=re.DOTALL)

with open("signalsight/gui/main_window.py", "w") as f:
    f.write(new_content)

print("Refactored main_window.py with Overview status updates")
