import os
import re

# Read main_window.py
with open("signalsight/gui/main_window.py", "r") as f:
    mw_content = f.read()

# We want to replace the MainWindow class from `class MainWindow(QMainWindow):` down to the end of `setup_ui()`
# but keep the event handlers `on_open_file`, etc.

mw_new_setup = """class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('SignalSight - Signal Analysis Platform')
        self.resize(1280, 720)
        self.setMinimumSize(900, 600)

        # State
        self.current_samples = None
        self.sample_rate = 0.0
        self.metadata = {}
        self.analysis_results = {}
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
        left_sidebar.setFixedWidth(220)
        left_layout = QVBoxLayout(left_sidebar)
        left_layout.setContentsMargins(16, 24, 16, 24)
        left_layout.setSpacing(16)
        
        # Logo / Title
        app_title = QLabel("SignalSight")
        app_title.setObjectName("app_title")
        left_layout.addWidget(app_title)
        
        # Navigation
        self.nav_list = QListWidget()
        self.nav_list.setObjectName("nav_list")
        self.nav_list.addItems(["Overview", "Spectrum", "Waterfall", "Constellation", "Bit Stream"])
        self.nav_list.setCurrentRow(0)
        self.nav_list.currentRowChanged.connect(self.on_nav_changed)
        # We don't want it to take huge space
        self.nav_list.setFixedHeight(220)
        left_layout.addWidget(self.nav_list)
        
        left_layout.addStretch()
        
        # File info (Bottom left)
        file_info_group = QGroupBox("File Info")
        fi_layout = QVBoxLayout(file_info_group)
        self.lbl_name = QLabel("Name: -")
        self.lbl_format = QLabel("Format: -")
        self.lbl_srate = QLabel("Sample Rate: -")
        self.lbl_samples = QLabel("Samples: -")
        self.lbl_duration = QLabel("Duration: -")
        
        for lbl in [self.lbl_name, self.lbl_format, self.lbl_srate, self.lbl_samples, self.lbl_duration]:
            lbl.setStyleSheet("color: #8c92b3; font-size: 11px;")
            fi_layout.addWidget(lbl)
        
        left_layout.addWidget(file_info_group)
        
        main_layout.addWidget(left_sidebar)

        # --- CENTRAL AREA ---
        center_widget = QWidget()
        center_layout = QVBoxLayout(center_widget)
        center_layout.setContentsMargins(24, 24, 24, 0)
        center_layout.setSpacing(24)
        
        # Top Bar
        top_bar = QWidget()
        top_bar_layout = QHBoxLayout(top_bar)
        top_bar_layout.setContentsMargins(0, 0, 0, 0)
        
        title_layout = QVBoxLayout()
        self.lbl_page_title = QLabel("Overview")
        self.lbl_page_title.setObjectName("page_title")
        self.lbl_page_subtitle = QLabel("No file loaded")
        self.lbl_page_subtitle.setObjectName("page_subtitle")
        title_layout.addWidget(self.lbl_page_title)
        title_layout.addWidget(self.lbl_page_subtitle)
        
        top_bar_layout.addLayout(title_layout)
        top_bar_layout.addStretch()
        
        # Toolbar actions
        btn_open = QPushButton("Open File")
        btn_clear = QPushButton("Clear")
        btn_open.clicked.connect(self.on_open_file)
        btn_clear.clicked.connect(self.on_clear)
        top_bar_layout.addWidget(btn_clear)
        top_bar_layout.addWidget(btn_open)
        
        center_layout.addWidget(top_bar)
        
        # Metrics Cards
        metrics_layout = QHBoxLayout()
        metrics_layout.setSpacing(12)
        
        self.lbl_mod = QLabel("-")
        self.lbl_snr = QLabel("-")
        self.lbl_bw = QLabel("-")
        self.lbl_symrate = QLabel("-")
        self.lbl_conf = QLabel("-")
        
        def create_metric_card(title, lbl_val):
            card = QFrame()
            card.setProperty("class", "metric_card")
            card_lay = QVBoxLayout(card)
            card_lay.setContentsMargins(16, 12, 16, 12)
            t = QLabel(title)
            t.setProperty("class", "metric_label")
            lbl_val.setProperty("class", "metric_value")
            card_lay.addWidget(t)
            card_lay.addWidget(lbl_val)
            return card
            
        metrics_layout.addWidget(create_metric_card("Modulation", self.lbl_mod))
        metrics_layout.addWidget(create_metric_card("SNR", self.lbl_snr))
        metrics_layout.addWidget(create_metric_card("Bandwidth", self.lbl_bw))
        metrics_layout.addWidget(create_metric_card("Symbol Rate", self.lbl_symrate))
        
        center_layout.addLayout(metrics_layout)
        
        # Stacked Widget for Visualizations
        self.stacked_vis = QStackedWidget()
        
        # 0: Overview (Empty/Summary)
        overview_widget = QWidget()
        overview_layout = QVBoxLayout(overview_widget)
        overview_lbl = QLabel("Load a file and run analysis to view signal details.")
        overview_lbl.setStyleSheet("color: #8c92b3;")
        overview_lbl.setAlignment(Qt.AlignCenter)
        overview_layout.addWidget(overview_lbl)
        
        self.tab_spectrum = SpectrumWidget()
        self.tab_waterfall = WaterfallWidget()
        self.tab_constellation = ConstellationWidget()
        self.tab_bitstream = BitstreamWidget()
        
        self.stacked_vis.addWidget(overview_widget)      # 0
        self.stacked_vis.addWidget(self.tab_spectrum)    # 1
        self.stacked_vis.addWidget(self.tab_waterfall)   # 2
        self.stacked_vis.addWidget(self.tab_constellation) # 3
        self.stacked_vis.addWidget(self.tab_bitstream)   # 4
        
        center_layout.addWidget(self.stacked_vis, 1)
        
        # Status Bar Footer
        self.status_bar = QStatusBar()
        self.status_bar.showMessage("Ready")
        center_layout.addWidget(self.status_bar)
        
        main_layout.addWidget(center_widget, 1)

        # --- RIGHT PANEL ---
        right_panel = QWidget()
        right_panel.setObjectName("right_panel")
        right_panel.setFixedWidth(300)
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(20, 24, 20, 24)
        
        lbl_proc = QLabel("Processing")
        lbl_proc.setStyleSheet("font-size: 16px; font-weight: 600; margin-bottom: 8px;")
        right_layout.addWidget(lbl_proc)
        
        # Analysis Controls
        analysis_group = QGroupBox("Analysis")
        al_layout = QVBoxLayout(analysis_group)
        al_layout.addWidget(QLabel("FFT Size:"))
        self.combo_fft = QComboBox()
        self.combo_fft.addItems(["512", "1024", "2048", "4096", "8192"])
        self.combo_fft.setCurrentText("4096")
        al_layout.addWidget(self.combo_fft)
        
        al_layout.addWidget(QLabel("Sample Rate (Hz):"))
        self.edit_srate = QLineEdit()
        self.edit_srate.setPlaceholderText("Auto")
        al_layout.addWidget(self.edit_srate)
        
        btn_analyze = QPushButton("Run Analysis")
        btn_analyze.setObjectName("primary_btn")
        btn_analyze.clicked.connect(self.on_run_analysis)
        al_layout.addWidget(btn_analyze)
        right_layout.addWidget(analysis_group)
        
        # Demodulation Controls
        demod_group = QGroupBox("Demodulation")
        dl_layout = QVBoxLayout(demod_group)
        
        dl_layout.addWidget(QLabel("Mod Type:"))
        self.combo_mod = QComboBox()
        self.combo_mod.addItems(["Auto", "BPSK", "QPSK"])
        dl_layout.addWidget(self.combo_mod)
        
        dl_layout.addWidget(QLabel("Symbol Rate (sps):"))
        self.edit_symrate = QLineEdit()
        self.edit_symrate.setPlaceholderText("Auto")
        dl_layout.addWidget(self.edit_symrate)
        
        dl_layout.addWidget(QLabel("Rolloff:"))
        self.edit_rolloff = QLineEdit("0.35")
        dl_layout.addWidget(self.edit_rolloff)
        
        btn_demod = QPushButton("Demodulate")
        btn_demod.setObjectName("primary_btn")
        btn_demod.clicked.connect(self.on_demodulate)
        dl_layout.addWidget(btn_demod)
        right_layout.addWidget(demod_group)
        
        # FEC Controls
        fec_group = QGroupBox("FEC / Bit Processing")
        fec_layout = QVBoxLayout(fec_group)
        
        self.chk_viterbi = QCheckBox("Viterbi FEC (Rate 1/2, K=7)")
        fec_layout.addWidget(self.chk_viterbi)
        
        # Block De-interleave
        self.chk_interleave = QCheckBox("Block De-interleave")
        fec_layout.addWidget(self.chk_interleave)
        
        int_grid = QHBoxLayout()
        self.edit_int_rows = QLineEdit()
        self.edit_int_rows.setPlaceholderText("Rows")
        self.edit_int_cols = QLineEdit()
        self.edit_int_cols.setPlaceholderText("Cols")
        int_grid.addWidget(self.edit_int_rows)
        int_grid.addWidget(self.edit_int_cols)
        fec_layout.addLayout(int_grid)
        
        # RS
        self.chk_rs = QCheckBox("Reed-Solomon")
        fec_layout.addWidget(self.chk_rs)
        
        self.edit_rs_nsym = QLineEdit()
        self.edit_rs_nsym.setPlaceholderText("nsym")
        fec_layout.addWidget(self.edit_rs_nsym)
        
        right_layout.addWidget(fec_group)
        
        # State toggle bindings
        self.chk_interleave.toggled.connect(self.edit_int_rows.setEnabled)
        self.chk_interleave.toggled.connect(self.edit_int_cols.setEnabled)
        self.chk_rs.toggled.connect(self.edit_rs_nsym.setEnabled)
        
        # Init state
        self.edit_int_rows.setEnabled(False)
        self.edit_int_cols.setEnabled(False)
        self.edit_rs_nsym.setEnabled(False)
        
        right_layout.addStretch()
        main_layout.addWidget(right_panel)

    def on_nav_changed(self, index):
        self.stacked_vis.setCurrentIndex(index)
        self.lbl_page_title.setText(self.nav_list.item(index).text())

    # ---- Handlers ----
"""

start_idx = mw_content.find("class MainWindow(QMainWindow):")
end_idx = mw_content.find("    # ---- Handlers ----")

new_content = mw_content[:start_idx] + mw_new_setup + mw_content[end_idx + 24:]

# Update the handlers to fix `self.tabs` references!
# We don't have `self.tabs` anymore, we use `self.nav_list` to change active page.
# `self.tabs.setCurrentIndex(0)` -> `self.nav_list.setCurrentRow(1)` (Spectrum)
# `self.tabs.setCurrentIndex(2)` -> `self.nav_list.setCurrentRow(3)` (Constellation)
new_content = new_content.replace("self.tabs.setCurrentIndex(0)", "self.nav_list.setCurrentRow(1)")
new_content = new_content.replace("self.tabs.setCurrentIndex(2)", "self.nav_list.setCurrentRow(3)")

# Also in `on_clear`, we need to reset the page subtitle
new_content = new_content.replace('self.lbl_name.setText(f"Name: {meta.get(\'filename\', \'-\')}")', 
                                  'self.lbl_name.setText(f"Name: {meta.get(\'filename\', \'-\')}"); self.lbl_page_subtitle.setText(f"{meta.get(\'filename\', \'-\')}")')

# The `on_clear` method has labels that don't match the new UI exactly because the tags changed?
# Wait! In `on_clear`:
'''
        for lbl in [self.lbl_name, self.lbl_format, self.lbl_srate,
                     self.lbl_samples, self.lbl_duration, self.lbl_bw,
                     self.lbl_snr, self.lbl_symrate, self.lbl_mod, self.lbl_conf]:
            tag = lbl.text().split(":")[0]
            lbl.setText(f"{tag}: -")
'''
# But the metric cards don't have tags!
# `self.lbl_mod.setText("-")` not `Modulation: -`.
# I'll fix `on_clear` entirely.
clear_method = """    def on_clear(self):
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

        self.edit_srate.clear()
        self.edit_symrate.clear()
        self.status_bar.showMessage("Ready")
"""
new_content = re.sub(r'    def on_clear\(self\):.*?    # ---- Result handlers ----', clear_method + '\n    # ---- Result handlers ----', new_content, flags=re.DOTALL)

# Update `handle_analysis_results` metrics formatting to not include the label tag
new_content = new_content.replace('self.lbl_bw.setText(f"Bandwidth: {bw/1000:.2f} kHz")', 'self.lbl_bw.setText(f"{bw/1000:.2f} kHz")')
new_content = new_content.replace('self.lbl_bw.setText(f"Bandwidth: {bw:.1f} Hz")', 'self.lbl_bw.setText(f"{bw:.1f} Hz")')
new_content = new_content.replace('self.lbl_snr.setText(f"SNR: {results[\'snr\']:.1f} dB")', 'self.lbl_snr.setText(f"{results[\'snr\']:.1f} dB")')
new_content = new_content.replace('self.lbl_symrate.setText(f"Symbol Rate: {sr/1000:.2f} ksps")', 'self.lbl_symrate.setText(f"{sr/1000:.2f} ksps")')
new_content = new_content.replace('self.lbl_symrate.setText(f"Symbol Rate: {sr:.1f} sps")', 'self.lbl_symrate.setText(f"{sr:.1f} sps")')
new_content = new_content.replace('self.lbl_mod.setText(f"Modulation: {top[\'type\']}")', 'self.lbl_mod.setText(f"{top[\'type\']}")')
new_content = new_content.replace('self.lbl_conf.setText(f"Confidence: {top[\'confidence\']:.2f}")', 'self.lbl_conf.setText(f"{top[\'confidence\']:.2f}")')

# Need to add `QStackedWidget` to imports in main_window.py
new_content = new_content.replace("from PySide6.QtWidgets import (", "from PySide6.QtWidgets import (QStackedWidget, QListWidget, QFrame, ")

with open("signalsight/gui/main_window.py", "w") as f:
    f.write(new_content)

print("Refactored main_window.py")
