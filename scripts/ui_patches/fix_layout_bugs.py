import re

# 1. Update styles.py for QGroupBox
with open("signalsight/gui/styles.py", "r") as f:
    content = f.read()

old_groupbox = """    /* Group Boxes */
    QGroupBox {
        background-color: {BG_SURFACE_SEC};
        border: 1px solid {BORDER};
        border-radius: 8px;
        margin-top: 12px;
        padding-top: 16px;
    }
    QGroupBox::title {
        subcontrol-origin: margin;
        subcontrol-position: top left;
        color: {TEXT_SECONDARY};
        font-size: 11px;
        font-weight: 700;
        text-transform: uppercase;
        padding-bottom: 4px;
        left: 12px;
        top: 8px;
    }"""

new_groupbox = """    /* Group Boxes */
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
    
content = content.replace(old_groupbox, new_groupbox)

with open("signalsight/gui/styles.py", "w") as f:
    f.write(content)


# 2. Update main_window.py to remove the QWidget containers in FEC that cause black boxes
with open("signalsight/gui/main_window.py", "r") as f:
    mw_content = f.read()

# Replace di_cont QWidget with just a layout
old_di = """        # Block De-interleave
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
        fec_layout.addWidget(di_cont)"""

new_di = """        # Block De-interleave
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
        fec_layout.addLayout(di_lay)"""
mw_content = mw_content.replace(old_di, new_di)

# Replace rs_cont QWidget with just a layout
old_rs = """        # RS
        rs_cont = QWidget()
        rs_lay = QVBoxLayout(rs_cont)
        rs_lay.setContentsMargins(0, 0, 0, 0)
        rs_lay.setSpacing(8)
        self.chk_rs = QCheckBox("Reed-Solomon")
        rs_lay.addWidget(self.chk_rs)
        
        self.edit_rs_nsym = QLineEdit()
        self.edit_rs_nsym.setPlaceholderText("nsym")
        rs_lay.addWidget(self.edit_rs_nsym)
        fec_layout.addWidget(rs_cont)"""
        
new_rs = """        # RS
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
        fec_layout.addLayout(rs_lay)"""
mw_content = mw_content.replace(old_rs, new_rs)

with open("signalsight/gui/main_window.py", "w") as f:
    f.write(mw_content)

print("Fixed layout bugs")
