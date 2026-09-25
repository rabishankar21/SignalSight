import re

with open("signalsight/gui/main_window.py", "r") as f:
    mw = f.read()

# Replace QGroupBox with QFrame
mw = mw.replace('analysis_group = QGroupBox("")', 'analysis_group = QFrame()\n        analysis_group.setProperty("class", "group_card")')
mw = mw.replace('demod_group = QGroupBox("")', 'demod_group = QFrame()\n        demod_group.setProperty("class", "group_card")')
mw = mw.replace('fec_group = QGroupBox("")', 'fec_group = QFrame()\n        fec_group.setProperty("class", "group_card")')

with open("signalsight/gui/main_window.py", "w") as f:
    f.write(mw)

# Update styles.py
with open("signalsight/gui/styles.py", "r") as f:
    st = f.read()

st = re.sub(r'    /\* Group Boxes \*/.*?    /\* Buttons \*/', 
r'''    /* Group Cards */
    QFrame.group_card {
        background-color: {BG_SURFACE_SEC};
        border: 1px solid {BORDER};
        border-radius: 8px;
    }
    
    /* Buttons */''', st, flags=re.DOTALL)

with open("signalsight/gui/styles.py", "w") as f:
    f.write(st)

print("Swapped QGroupBox to QFrame!")
