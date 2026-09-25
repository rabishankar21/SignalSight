import re

with open("signalsight/gui/main_window.py", "r") as f:
    mw = f.read()

# Replace QGroupBox initializations with empty strings and add explicit QLabel titles inside the layout
# Analysis
old_al = """        analysis_group = QGroupBox("ANALYSIS")
        al_layout = QVBoxLayout(analysis_group)
        al_layout.setContentsMargins(16, 42, 16, 16)
        al_layout.setSpacing(12)"""

new_al = """        analysis_group = QGroupBox("")
        al_layout = QVBoxLayout(analysis_group)
        al_layout.setContentsMargins(16, 16, 16, 16)
        al_layout.setSpacing(12)
        
        lbl_al_title = QLabel("ANALYSIS")
        lbl_al_title.setStyleSheet("color: #9AA5BA; font-size: 11px; font-weight: 700; letter-spacing: 1px;")
        al_layout.addWidget(lbl_al_title)
        al_layout.addSpacing(8)"""

mw = mw.replace(old_al, new_al)

# Demodulation
old_dl = """        demod_group = QGroupBox("DEMODULATION")
        demod_group.setMinimumHeight(220)
        dl_layout = QVBoxLayout(demod_group)
        dl_layout.setContentsMargins(16, 42, 16, 16)
        dl_layout.setSpacing(12)"""

new_dl = """        demod_group = QGroupBox("")
        demod_group.setMinimumHeight(240)
        dl_layout = QVBoxLayout(demod_group)
        dl_layout.setContentsMargins(16, 16, 16, 16)
        dl_layout.setSpacing(12)
        
        lbl_dl_title = QLabel("DEMODULATION")
        lbl_dl_title.setStyleSheet("color: #9AA5BA; font-size: 11px; font-weight: 700; letter-spacing: 1px;")
        dl_layout.addWidget(lbl_dl_title)
        dl_layout.addSpacing(8)"""

mw = mw.replace(old_dl, new_dl)

# FEC
old_fec = """        fec_group = QGroupBox("FEC / BIT PROCESSING")
        fec_layout = QVBoxLayout(fec_group)
        fec_layout.setContentsMargins(16, 42, 16, 16)
        fec_layout.setSpacing(16)"""
        
new_fec = """        fec_group = QGroupBox("")
        fec_layout = QVBoxLayout(fec_group)
        fec_layout.setContentsMargins(16, 16, 16, 16)
        fec_layout.setSpacing(16)
        
        lbl_fec_title = QLabel("FEC / BIT PROCESSING")
        lbl_fec_title.setStyleSheet("color: #9AA5BA; font-size: 11px; font-weight: 700; letter-spacing: 1px;")
        fec_layout.addWidget(lbl_fec_title)
        fec_layout.addSpacing(4)"""

mw = mw.replace(old_fec, new_fec)

with open("signalsight/gui/main_window.py", "w") as f:
    f.write(mw)

# Also let's clean up styles.py to remove the weird margins on QGroupBox since we now use empty titles
with open("signalsight/gui/styles.py", "r") as f:
    st = f.read()

st = re.sub(r'    /\* Group Boxes \*/.*?    /\* Buttons \*/', 
r'''    /* Group Boxes */
    QGroupBox {
        background-color: {BG_SURFACE_SEC};
        border: 1px solid {BORDER};
        border-radius: 8px;
        margin-top: 0px;
    }
    
    /* Buttons */''', st, flags=re.DOTALL)

with open("signalsight/gui/styles.py", "w") as f:
    f.write(st)

print("Fixed title by moving it to an explicit label inside the box!")
