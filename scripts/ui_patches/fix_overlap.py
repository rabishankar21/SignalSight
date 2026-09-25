import re

with open("signalsight/gui/styles.py", "r") as f:
    content = f.read()

# Fix QGroupBox styles
old_groupbox = """    /* Group Boxes */
    QGroupBox {
        background-color: {BG_SURFACE_SEC};
        border: 1px solid {BORDER};
        border-radius: 8px;
        margin-top: 24px;
        padding: 16px;
    }
    QGroupBox::title {
        subcontrol-origin: margin;
        subcontrol-position: top left;
        color: {TEXT_SECONDARY};
        font-size: 11px;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 1px;
        left: 4px;
        top: 0px;
        background-color: transparent;
    }"""

new_groupbox = """    /* Group Boxes */
    QGroupBox {
        background-color: {BG_SURFACE_SEC};
        border: 1px solid {BORDER};
        border-radius: 8px;
        margin-top: 8px;
    }
    QGroupBox::title {
        subcontrol-origin: padding;
        subcontrol-position: top left;
        color: {TEXT_SECONDARY};
        font-size: 11px;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 1px;
        left: 16px;
        top: 14px;
        background-color: transparent;
    }"""
    
content = content.replace(old_groupbox, new_groupbox)

with open("signalsight/gui/styles.py", "w") as f:
    f.write(content)


# Update layout margins in main_window.py
with open("signalsight/gui/main_window.py", "r") as f:
    mw = f.read()

# Analysis layout
mw = mw.replace("""        analysis_group = QGroupBox("ANALYSIS")
        al_layout = QVBoxLayout(analysis_group)
        al_layout.setSpacing(12)""", """        analysis_group = QGroupBox("ANALYSIS")
        al_layout = QVBoxLayout(analysis_group)
        al_layout.setContentsMargins(16, 42, 16, 16)
        al_layout.setSpacing(12)""")

# Demodulation layout
mw = mw.replace("""        demod_group = QGroupBox("DEMODULATION")
        dl_layout = QVBoxLayout(demod_group)
        dl_layout.setSpacing(12)""", """        demod_group = QGroupBox("DEMODULATION")
        dl_layout = QVBoxLayout(demod_group)
        dl_layout.setContentsMargins(16, 42, 16, 16)
        dl_layout.setSpacing(12)""")

# FEC layout
mw = mw.replace("""        fec_group = QGroupBox("FEC / BIT PROCESSING")
        fec_layout = QVBoxLayout(fec_group)
        fec_layout.setSpacing(16)""", """        fec_group = QGroupBox("FEC / BIT PROCESSING")
        fec_layout = QVBoxLayout(fec_group)
        fec_layout.setContentsMargins(16, 42, 16, 16)
        fec_layout.setSpacing(16)""")

with open("signalsight/gui/main_window.py", "w") as f:
    f.write(mw)

print("Fixed border overlap and button spilling")
