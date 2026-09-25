import re

with open("signalsight/gui/styles.py", "r") as f:
    content = f.read()

# Replace metric_card CSS
old_metric_card = """    QFrame.metric_card {
        background-color: {BG_CARD};
        border-radius: 8px;
        border: 1px solid {BORDER};
        min-height: 80px;
    }"""
    
new_metric_card = """    QFrame.metric_card {
        background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 {BG_CARD_HOVER}, stop:1 {BG_CARD});
        border-radius: 8px;
        border-top: 1px solid #3A4259;
        border-bottom: 2px solid {BG_APP};
        border-left: 1px solid {BORDER};
        border-right: 1px solid {BORDER};
        min-height: 80px;
    }"""
content = content.replace(old_metric_card, new_metric_card)

# Replace disabled styles for lineedits and combos
content = re.sub(
    r'    QLineEdit:disabled, QComboBox:disabled \{\s*color: \{TEXT_MUTED\};\s*background-color: \{BG_APP\};\s*border-color: \{BG_APP\};\s*\}',
    r'    QLineEdit:disabled, QComboBox:disabled {\n        color: {TEXT_MUTED};\n        background-color: {BG_SURFACE_SEC};\n        border-color: {BG_SURFACE_SEC};\n    }',
    content, flags=re.MULTILINE
)

# Replace disabled styles for checkboxes
content = re.sub(
    r'    QCheckBox::indicator:disabled \{\s*border: 1px solid \{BG_APP\};\s*background-color: \{BG_APP\};\s*\}',
    r'    QCheckBox::indicator:disabled {\n        border: 1px solid {TEXT_MUTED};\n        background-color: {BG_SURFACE_SEC};\n    }',
    content, flags=re.MULTILINE
)

with open("signalsight/gui/styles.py", "w") as f:
    f.write(content)
print("Updated styles.py")
