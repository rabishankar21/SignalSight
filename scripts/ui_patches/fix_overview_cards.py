import re

with open("signalsight/gui/main_window.py", "r") as f:
    mw = f.read()

# Change Signal Info card to group_card
mw = mw.replace('self.ov_info_container.setProperty("class", "metric_card")', 'self.ov_info_container.setProperty("class", "group_card")')

# Wrap Processing Status labels in a group_card
old_status = """        self.lbl_ov_status_analysis = QLabel("Analysis: Pending")
        self.lbl_ov_status_demod = QLabel("Demodulation: Pending")
        self.lbl_ov_status_fec = QLabel("FEC: Pending")
        
        for lbl in [self.lbl_ov_status_analysis, self.lbl_ov_status_demod, self.lbl_ov_status_fec]:
            lbl.setStyleSheet("color: #9AA5BA; font-size: 13px;")
            overview_layout.addWidget(lbl)
            
        overview_layout.addStretch()"""
        
new_status = """        self.ov_status_container = QFrame()
        self.ov_status_container.setProperty("class", "group_card")
        ov_status_layout = QVBoxLayout(self.ov_status_container)
        ov_status_layout.setContentsMargins(20, 20, 20, 20)
        ov_status_layout.setSpacing(12)
        
        self.lbl_ov_status_analysis = QLabel("Analysis: Pending")
        self.lbl_ov_status_demod = QLabel("Demodulation: Pending")
        self.lbl_ov_status_fec = QLabel("FEC: Pending")
        
        for lbl in [self.lbl_ov_status_analysis, self.lbl_ov_status_demod, self.lbl_ov_status_fec]:
            lbl.setStyleSheet("color: #9AA5BA; font-size: 13px;")
            ov_status_layout.addWidget(lbl)
            
        overview_layout.addWidget(self.ov_status_container)
        overview_layout.addStretch()"""

mw = mw.replace(old_status, new_status)

# To fix the alignment of text in the SIGNAL INFO grid, let's add a horizontal stretch to the grid layout
old_grid = """        for i, (k, v) in enumerate(zip(keys, vals)):
            k_lbl = QLabel(k)
            k_lbl.setStyleSheet("color: #9AA5BA; font-size: 13px; min-width: 140px;")
            v.setStyleSheet("color: #F3F5FA; font-size: 13px; font-weight: 500;")
            ov_info_layout.addWidget(k_lbl, i, 0)
            ov_info_layout.addWidget(v, i, 1)"""
            
new_grid = """        for i, (k, v) in enumerate(zip(keys, vals)):
            k_lbl = QLabel(k)
            k_lbl.setStyleSheet("color: #9AA5BA; font-size: 13px; min-width: 140px;")
            v.setStyleSheet("color: #F3F5FA; font-size: 13px; font-weight: 500;")
            ov_info_layout.addWidget(k_lbl, i, 0)
            ov_info_layout.addWidget(v, i, 1)
        ov_info_layout.setColumnStretch(2, 1)"""

mw = mw.replace(old_grid, new_grid)

with open("signalsight/gui/main_window.py", "w") as f:
    f.write(mw)
    
print("Fixed Overview cards and alignment")
