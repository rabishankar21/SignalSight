import re

with open("signalsight/gui/styles.py", "r") as f:
    st = f.read()

# 1. Update Group Cards
st = re.sub(r'    /\* Group Cards \*/.*?    /\* Buttons \*/', 
r'''    /* Group Cards */
    QFrame.group_card {{
        background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #1F2436, stop:1 {BG_SURFACE_SEC});
        border: 1px solid {BORDER};
        border-top: 1px solid #3A4259;
        border-bottom: 2px solid {BG_APP};
        border-radius: 8px;
    }}
    
    /* Buttons */''', st, flags=re.DOTALL)

# 2. Update Primary and Secondary Buttons
st = re.sub(r'    /\* Buttons \*/.*?    /\* Inputs \*/',
r'''    /* Buttons */
    QPushButton {{
        background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 {BG_CARD_HOVER}, stop:1 {BG_CARD});
        color: {TEXT_PRIMARY};
        border: 1px solid {BORDER};
        border-top: 1px solid #3A4259;
        border-bottom: 2px solid {BG_APP};
        border-radius: 6px;
        padding: 6px 16px;
        font-weight: 500;
        min-height: 24px;
    }}
    QPushButton:hover {{
        background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #2E364F, stop:1 {BG_CARD_HOVER});
        border-color: {TEXT_MUTED};
    }}
    QPushButton:pressed {{
        background-color: {BG_INPUT};
        border-top: 2px solid {BG_APP};
        border-bottom: 1px solid {BORDER};
    }}
    QPushButton#primary_btn {{
        background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #4A90FF, stop:1 {ACCENT});
        color: #ffffff;
        border: 1px solid #1A4099;
        border-top: 1px solid #7AA8FF;
        border-bottom: 2px solid #102A66;
        border-radius: 6px;
        padding: 8px 16px;
        font-weight: 600;
    }}
    QPushButton#primary_btn:hover {{
        background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #5A9FFF, stop:1 #4A90FF);
    }}
    QPushButton#primary_btn:pressed {{
        background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 {ACCENT}, stop:1 #4A90FF);
        border-top: 1px solid #1A4099;
        border-bottom: 1px solid #7AA8FF;
    }}
    
    /* Inputs */''', st, flags=re.DOTALL)

with open("signalsight/gui/styles.py", "w") as f:
    f.write(st)

print("Applied 3D effects")
