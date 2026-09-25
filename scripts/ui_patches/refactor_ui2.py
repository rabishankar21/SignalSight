import os

# Read bitstream_widget.py
with open("signalsight/gui/bitstream_widget.py", "r") as f:
    bw_content = f.read()

bw_new = """import numpy as np
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QPlainTextEdit, QApplication, QFrame
from PySide6.QtGui import QFont

class BitstreamWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(12)
        
        # Header container
        header = QFrame()
        header.setObjectName("bitstream_header")
        header.setStyleSheet("background-color: #1a1c29; border-radius: 8px; padding: 4px;")
        h_layout = QHBoxLayout(header)
        h_layout.setContentsMargins(12, 8, 12, 8)
        
        self.lbl_title = QLabel("Recovered Bit Stream")
        self.lbl_title.setStyleSheet("font-weight: 600; color: #e2e4f0;")
        
        self.lbl_count = QLabel("0 bits")
        self.lbl_count.setStyleSheet("color: #8c92b3;")
        
        self.btn_hex = QPushButton("HEX")
        self.btn_bin = QPushButton("Binary")
        self.btn_hex.setCheckable(True)
        self.btn_bin.setCheckable(True)
        self.btn_bin.setChecked(True)
        
        self.btn_copy = QPushButton("Copy")
        
        # Make toggle buttons look like a segment control
        toggle_style = \"\"\"
        QPushButton {
            background-color: transparent; border: none; color: #8c92b3; padding: 4px 12px;
        }
        QPushButton:checked {
            background-color: #2a2d40; color: #e2e4f0; border-radius: 4px; font-weight: 600;
        }
        \"\"\"
        self.btn_hex.setStyleSheet(toggle_style)
        self.btn_bin.setStyleSheet(toggle_style)
        
        self.btn_hex.clicked.connect(self.show_hex)
        self.btn_bin.clicked.connect(self.show_bin)
        self.btn_copy.clicked.connect(self.copy_to_clipboard)
        
        h_layout.addWidget(self.lbl_title)
        h_layout.addSpacing(16)
        h_layout.addWidget(self.lbl_count)
        h_layout.addStretch()
        h_layout.addWidget(self.btn_bin)
        h_layout.addWidget(self.btn_hex)
        h_layout.addSpacing(16)
        h_layout.addWidget(self.btn_copy)
        
        self.layout.addWidget(header)
        
        self.text_edit = QPlainTextEdit()
        self.text_edit.setReadOnly(True)
        self.text_edit.setStyleSheet(\"\"\"
            QPlainTextEdit {
                background-color: #1a1c29;
                color: #e2e4f0;
                border: 1px solid #2a2d40;
                border-radius: 8px;
                padding: 16px;
                line-height: 1.5;
            }
        \"\"\")
        font = QFont("Consolas", 11)
        font.setStyleHint(QFont.Monospace)
        self.text_edit.setFont(font)
        self.layout.addWidget(self.text_edit)
        
        self.bits = np.array([])
        
    def update_data(self, bits: np.ndarray):
        self.bits = bits
        self.lbl_count.setText(f"{len(bits)} bits")
        if self.btn_hex.isChecked():
            self.show_hex()
        else:
            self.show_bin()

    def clear_data(self):
        self.bits = np.array([])
        self.lbl_count.setText("0 bits")
        self.text_edit.clear()

    def show_hex(self):
        self.btn_hex.setChecked(True)
        self.btn_bin.setChecked(False)
        if len(self.bits) == 0:
            self.text_edit.clear()
            return
            
        pad_len = (8 - len(self.bits) % 8) % 8
        padded_bits = np.pad(self.bits, (0, pad_len), 'constant')
        byte_vals = np.packbits(padded_bits)
        
        lines = []
        for i in range(0, len(byte_vals), 16):
            chunk = byte_vals[i:i+16]
            offset = f"{i:08X}"
            hex_str = " ".join([f"{b:02X}" for b in chunk])
            hex_str = hex_str.ljust(47)
            
            ascii_str = "".join([chr(b) if 32 <= b <= 126 else "." for b in chunk])
            lines.append(f"{offset}  {hex_str}  {ascii_str}")
            
        self.text_edit.setPlainText("\\n".join(lines))

    def show_bin(self):
        self.btn_bin.setChecked(True)
        self.btn_hex.setChecked(False)
        if len(self.bits) == 0:
            self.text_edit.clear()
            return
            
        bits_str = "".join(map(str, self.bits))
        grouped = " ".join([bits_str[i:i+8] for i in range(0, len(bits_str), 8)])
        self.text_edit.setPlainText(grouped)

    def copy_to_clipboard(self):
        clipboard = QApplication.clipboard()
        clipboard.setText(self.text_edit.toPlainText())
"""

with open("signalsight/gui/bitstream_widget.py", "w") as f:
    f.write(bw_new)

print("Refactored bitstream_widget.py")
