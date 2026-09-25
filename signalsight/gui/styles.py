"""
SignalSight Theme System

A modern, premium, sophisticated dark theme inspired by professional scientific applications.
Provides a central source of truth for colors, metrics, and Qt stylesheets.
"""

# Color Palette
BG_APP = "#0D0F16"          # Application background
BG_SURFACE = "#131722"      # Primary surface (panels)
BG_SURFACE_SEC = "#191D2A"  # Secondary surface
BG_CARD = "#1D2232"         # Elevated card
BG_CARD_HOVER = "#242A3D"
BG_INPUT = "#0D0F16"        # Input fields (darker for contrast)

BORDER = "#292F40"          # Subtle borders
BORDER_FOCUS = "#3A86FF"    # Focused inputs

ACCENT = "#3A86FF"          # Primary accent
ACCENT_HOVER = "#2A6EDC"
SUCCESS = "#2E8C5A"         # Restrained green

TEXT_PRIMARY = "#F3F5FA"    # Main text
TEXT_SECONDARY = "#9AA5BA"  # Muted labels / context
TEXT_MUTED = "#69758C"      # Very muted

# Fonts
FONT_FAMILY = "'Segoe UI', 'Segoe UI Variable', -apple-system, BlinkMacSystemFont, Roboto, sans-serif"
FONT_MONO = "Consolas, 'Courier New', monospace"

def get_stylesheet():
    return f"""
    /* Global */
    QMainWindow, QWidget {{
        background-color: {BG_APP};
        color: {TEXT_PRIMARY};
        font-family: {FONT_FAMILY};
        font-size: 13px;
    }}

    /* Panels & Surfaces */
    QWidget#left_panel, QWidget#right_panel, QWidget#top_bar, QWidget#overview_page {{
        background-color: {BG_SURFACE};
    }}
    
    QSplitter::handle {{
        background-color: {BORDER};
        width: 1px;
    }}
    
    /* Typography Hierarchy */
    QLabel#app_title {{
        font-size: 18px;
        font-weight: 600;
        color: {TEXT_PRIMARY};
        padding: 10px 10px 10px 0;
        letter-spacing: 1px;
    }}
    QLabel#page_title {{
        font-size: 24px;
        font-weight: 600;
        color: {TEXT_PRIMARY};
    }}
    QLabel#page_subtitle {{
        font-size: 13px;
        color: {TEXT_SECONDARY};
    }}
    QLabel#section_title {{
        font-size: 14px;
        font-weight: 600;
        color: {TEXT_SECONDARY};
        text-transform: uppercase;
        letter-spacing: 1px;
        margin-top: 16px;
        margin-bottom: 8px;
    }}
    QLabel#sidebar_header {{
        font-size: 11px;
        font-weight: 700;
        color: {TEXT_MUTED};
        text-transform: uppercase;
        letter-spacing: 1px;
        padding-top: 16px;
        padding-bottom: 4px;
    }}
    
    /* Metrics Cards (WITH 3D EFFECTS) */
    QFrame.metric_card {{
        background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 {BG_CARD_HOVER}, stop:1 {BG_CARD});
        border-radius: 8px;
        border-top: 1px solid #3A4259;
        border-bottom: 2px solid {BG_APP};
        border-left: 1px solid {BORDER};
        border-right: 1px solid {BORDER};
        min-height: 90px;
    }}
    QLabel.metric_label {{
        color: {TEXT_SECONDARY};
        font-size: 11px;
        text-transform: uppercase;
        font-weight: 600;
        letter-spacing: 0.5px;
        background-color: transparent;
    }}
    QLabel.metric_value {{
        color: {TEXT_PRIMARY};
        font-size: 22px;
        font-weight: 400;
        padding-bottom: 4px;
        min-height: 28px;
        background-color: transparent;
    }}
    
    /* Group Cards */
    QFrame.group_card {{
        background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #1F2436, stop:1 {BG_SURFACE_SEC});
        border: 1px solid {BORDER};
        border-top: 1px solid #3A4259;
        border-bottom: 2px solid {BG_APP};
        border-radius: 8px;
    }}
    
    /* Buttons */
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
    
    /* Inputs */
    QLineEdit, QComboBox {{
        background-color: {BG_INPUT};
        color: {TEXT_PRIMARY};
        border: 1px solid {BORDER};
        border-radius: 6px;
        padding: 6px 10px;
        min-height: 24px;
        selection-background-color: {ACCENT};
    }}
    QLineEdit:focus, QComboBox:focus {{
        border: 1px solid {BORDER_FOCUS};
    }}
    QLineEdit:disabled, QComboBox:disabled {{
        color: {TEXT_MUTED};
        background-color: {BG_SURFACE_SEC};
        border-color: {BG_SURFACE_SEC};
    }}
    
    QComboBox::drop-down {{
        border: none;
        padding-right: 12px;
    }}
    QComboBox::down-arrow {{
        image: none;
        border-left: 4px solid transparent;
        border-right: 4px solid transparent;
        border-top: 4px solid {TEXT_SECONDARY};
        width: 0;
        height: 0;
        margin-right: 8px;
    }}

    /* Checkboxes */
    QCheckBox {{
        color: {TEXT_PRIMARY};
        spacing: 10px;
        background-color: transparent;
        font-weight: 500;
    }}
    QCheckBox::indicator {{
        width: 14px;
        height: 14px;
        border: 1px solid {BORDER};
        border-radius: 4px;
        background-color: {BG_INPUT};
    }}
    QCheckBox::indicator:checked {{
        background-color: {ACCENT};
        border: 1px solid {ACCENT};
    }}
    QCheckBox:disabled {{
        color: {TEXT_MUTED};
    }}
    QCheckBox::indicator:disabled {{
        border: 1px solid {TEXT_MUTED};
        background-color: {BG_SURFACE_SEC};
    }}
    
    /* Status Bar */
    QStatusBar {{
        background-color: {BG_SURFACE};
        color: {TEXT_SECONDARY};
        border-top: 1px solid {BORDER};
        min-height: 28px;
    }}
    QStatusBar::item {{
        border: none;
    }}
    
    /* Sidebar Navigation */
    QListWidget#nav_list {{
        background-color: transparent;
        border: none;
        outline: none;
    }}
    QListWidget#nav_list::item {{
        color: {TEXT_SECONDARY};
        padding: 8px 12px;
        border-radius: 6px;
        margin: 2px 0;
    }}
    QListWidget#nav_list::item:hover {{
        background-color: {BG_APP};
        color: {TEXT_PRIMARY};
    }}
    QListWidget#nav_list::item:selected {{
        background-color: {BG_CARD};
        color: {ACCENT};
        font-weight: 600;
        border-left: 3px solid {ACCENT};
    }}
    
    /* Scrollbars */
    QScrollBar:vertical {{
        background: {BG_APP};
        width: 10px;
        margin: 0px;
    }}
    QScrollBar::handle:vertical {{
        background: {BORDER};
        min-height: 20px;
        border-radius: 5px;
    }}
    QScrollBar::handle:vertical:hover {{
        background: {TEXT_MUTED};
    }}
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
        height: 0px;
    }}
    
    QLabel {{
        background-color: transparent;
    }}
    """

def apply_theme(app):
    app.setStyleSheet(get_stylesheet())
