import os
import re

# 1. Update main_window.py
with open("signalsight/gui/main_window.py", "r") as f:
    content = f.read()

# Fix 1: Navigation height
content = content.replace("self.nav_list.setFixedHeight(180)", "self.nav_list.setMinimumHeight(240)")

# Fix 2: Overview Signal Information Layout
old_info_container = """        self.ov_info_container = QWidget()
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
            ov_info_layout.addWidget(lbl)"""

new_info_container = """        from PySide6.QtWidgets import QGridLayout
        self.ov_info_container = QFrame()
        self.ov_info_container.setProperty("class", "metric_card")
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
            
        ov_info_layout.setColumnStretch(1, 1)"""
        
content = content.replace(old_info_container, new_info_container)

# Update on_open_file for new labels
old_open_update = """            self.lbl_ov_file.setText(f"File: {meta.get('filename', '-')}")
            self.lbl_ov_format.setText(f"Format: {meta.get('format', '-')}")
            self.lbl_ov_srate.setText(f"Sample Rate: {sr:,.0f} Hz")
            self.lbl_ov_samples.setText(f"Samples: {meta.get('num_samples', 0):,}")
            self.lbl_ov_duration.setText(f"Duration: {meta.get('duration_sec', 0):.4f} s")
            self.lbl_ov_carrier.setText(f"Carrier Offset: -")"""
            
new_open_update = """            self.lbl_ov_file.setText(f"{meta.get('filename', '-')}")
            self.lbl_ov_format.setText(f"{meta.get('format', '-')}")
            self.lbl_ov_srate.setText(f"{sr:,.0f} Hz")
            self.lbl_ov_samples.setText(f"{meta.get('num_samples', 0):,}")
            self.lbl_ov_duration.setText(f"{meta.get('duration_sec', 0):.4f} s")
            self.lbl_ov_carrier.setText(f"-")"""
            
content = content.replace(old_open_update, new_open_update)

# Update on_clear for new labels
old_clear_update = """        self.lbl_ov_file.setText("File: -")
        self.lbl_ov_format.setText("Format: -")
        self.lbl_ov_srate.setText("Sample Rate: -")
        self.lbl_ov_samples.setText("Samples: -")
        self.lbl_ov_duration.setText("Duration: -")
        self.lbl_ov_carrier.setText("Carrier Offset: -")"""
        
new_clear_update = """        self.lbl_ov_file.setText("-")
        self.lbl_ov_format.setText("-")
        self.lbl_ov_srate.setText("-")
        self.lbl_ov_samples.setText("-")
        self.lbl_ov_duration.setText("-")
        self.lbl_ov_carrier.setText("-")"""
        
content = content.replace(old_clear_update, new_clear_update)

# Update demod for new labels
old_demod_update = """self.lbl_ov_carrier.setText(f"Carrier Offset: {f_off:.1f} Hz")"""
new_demod_update = """self.lbl_ov_carrier.setText(f"{f_off:.1f} Hz")"""
content = content.replace(old_demod_update, new_demod_update)

# Fix 4: Visualization Titles
old_wrap_plot = """        def wrap_plot(title, subtitle, widget):
            container = QWidget()
            lay = QVBoxLayout(container)
            lay.setContentsMargins(0, 0, 0, 0)
            
            card = QFrame()
            card.setStyleSheet("background-color: #131722; border: 1px solid transparent; border-radius: 8px;")
            card_lay = QVBoxLayout(card)
            card_lay.setContentsMargins(0, 0, 0, 0)
            card_lay.addWidget(widget)
            lay.addWidget(card)
            return container"""
            
new_wrap_plot = """        def wrap_plot(title, subtitle, widget):
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
            return container"""
            
content = content.replace(old_wrap_plot, new_wrap_plot)

# Fix titles to exact requested
content = content.replace('wrap_plot("Power Spectral Density", "Frequency domain", self.tab_spectrum)', 'wrap_plot("POWER SPECTRAL DENSITY", "", self.tab_spectrum)')
content = content.replace('wrap_plot("Waterfall", "Time-frequency", self.tab_waterfall)', 'wrap_plot("WATERFALL / SPECTROGRAM", "", self.tab_waterfall)')
content = content.replace('wrap_plot("Constellation", "Phase map", self.tab_constellation)', 'wrap_plot("CONSTELLATION DIAGRAM", "", self.tab_constellation)')

# Add QGridLayout to imports if not there
if "QGridLayout" not in content:
    content = content.replace("from PySide6.QtWidgets import (QStackedWidget", "from PySide6.QtWidgets import (QStackedWidget, QGridLayout")

with open("signalsight/gui/main_window.py", "w") as f:
    f.write(content)

# 2. Update styles.py for disabled inputs
with open("signalsight/gui/styles.py", "r") as f:
    styles_content = f.read()
    
styles_content = styles_content.replace("""    QLineEdit:disabled, QComboBox:disabled {
        color: {TEXT_MUTED};
        background-color: {BG_APP};
        border-color: {BG_APP};
    }""", """    QLineEdit:disabled, QComboBox:disabled {
        color: {TEXT_MUTED};
        background-color: {BG_SURFACE_SEC};
        border-color: {BG_SURFACE_SEC};
    }""")

styles_content = styles_content.replace("""    QCheckBox::indicator:disabled {
        border: 1px solid {BG_APP};
        background-color: {BG_APP};
    }""", """    QCheckBox::indicator:disabled {
        border: 1px solid {TEXT_MUTED};
        background-color: {BG_SURFACE_SEC};
    }""")

with open("signalsight/gui/styles.py", "w") as f:
    f.write(styles_content)

# 3. Update spectrum_widget.py
with open("signalsight/gui/spectrum_widget.py", "r") as f:
    spec_content = f.read()

# Remove the label and its update in mouse_moved
spec_content = spec_content.replace("""        self.label = pg.TextItem(anchor=(0, 1), color='#9AA5BA')
        self.plot_widget.addItem(self.label)
        
""", "")

spec_content = spec_content.replace("""            self.label.setText(f"Freq: {x_val/1000:.2f} kHz, Power: {y_val:.2f} dBFS")
            self.label.setPos(x_val, y_val)""", "")

with open("signalsight/gui/spectrum_widget.py", "w") as f:
    f.write(spec_content)

# 4. Update constellation_widget.py
with open("signalsight/gui/constellation_widget.py", "r") as f:
    const_content = f.read()

const_content = const_content.replace("pen=pg.mkPen('#292F40', width=1, style=pg.QtCore.Qt.DashLine)", "pen=pg.mkPen(color=(41, 47, 64, 80), width=0.8, style=pg.QtCore.Qt.DashLine)")
# Also make crosshairs a bit more subtle
const_content = const_content.replace("pen=pg.mkPen('#292F40', width=1)", "pen=pg.mkPen(color=(41, 47, 64, 120), width=0.8)")

with open("signalsight/gui/constellation_widget.py", "w") as f:
    f.write(const_content)

print("Applied precision fixes.")
