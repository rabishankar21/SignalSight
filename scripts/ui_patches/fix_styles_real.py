import re

with open("signalsight/gui/styles.py", "r") as f:
    content = f.read()

# Replace QGroupBox completely using regex so we don't mess up brackets
content = re.sub(
    r'    /\* Group Boxes \*/\s+QGroupBox \{\{.*?\}\}\s+QGroupBox::title \{\{.*?\}\}',
    r'''    /* Group Boxes */
    QGroupBox {{
        background-color: {BG_SURFACE_SEC};
        border: 1px solid {BORDER};
        border-radius: 8px;
        margin-top: 8px;
    }}
    QGroupBox::title {{
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
    }}''',
    content, flags=re.DOTALL
)

with open("signalsight/gui/styles.py", "w") as f:
    f.write(content)
print("Updated styles")
