import re

with open("signalsight/gui/main_window.py", "r") as f:
    mw = f.read()

# Increase spacing in Demodulation layout to stretch it down
old_demod = """        row5 = QHBoxLayout()
        row5.addWidget(QLabel("Rolloff"))
        self.edit_rolloff = QLineEdit("0.35")
        row5.addWidget(self.edit_rolloff)
        dl_layout.addLayout(row5)
        
        btn_demod = QPushButton("Demodulate")
        btn_demod.setObjectName("primary_btn")
        btn_demod.clicked.connect(self.on_demodulate)
        dl_layout.addSpacing(8)
        dl_layout.addWidget(btn_demod)"""

new_demod = """        row5 = QHBoxLayout()
        row5.addWidget(QLabel("Rolloff"))
        self.edit_rolloff = QLineEdit("0.35")
        row5.addWidget(self.edit_rolloff)
        dl_layout.addLayout(row5)
        
        btn_demod = QPushButton("Demodulate")
        btn_demod.setObjectName("primary_btn")
        btn_demod.clicked.connect(self.on_demodulate)
        dl_layout.addSpacing(24)  # Increased spacing to stretch the card downwards
        dl_layout.addWidget(btn_demod)"""

mw = mw.replace(old_demod, new_demod)

# Increase spacing in Analysis layout slightly for balance
old_analysis = """        btn_analyze = QPushButton("Run Analysis")
        btn_analyze.setObjectName("primary_btn")
        btn_analyze.clicked.connect(self.on_run_analysis)
        al_layout.addSpacing(8)
        al_layout.addWidget(btn_analyze)"""
        
new_analysis = """        btn_analyze = QPushButton("Run Analysis")
        btn_analyze.setObjectName("primary_btn")
        btn_analyze.clicked.connect(self.on_run_analysis)
        al_layout.addSpacing(16)  # Increased spacing for balance
        al_layout.addWidget(btn_analyze)"""

mw = mw.replace(old_analysis, new_analysis)

# Also let's set a minimum height for the demod group to ensure it gets taller
mw = mw.replace('demod_group = QGroupBox("DEMODULATION")', 'demod_group = QGroupBox("DEMODULATION")\n        demod_group.setMinimumHeight(220)')

with open("signalsight/gui/main_window.py", "w") as f:
    f.write(mw)
    
print("Updated card sizing")
