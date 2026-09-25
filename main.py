import sys
from PySide6.QtWidgets import QApplication
from signalsight.gui.main_window import MainWindow
from signalsight.gui.styles import apply_theme

def main():
    app = QApplication(sys.argv)
    app.setApplicationName('SignalSight')
    app.setOrganizationName('CodeHexa')
    apply_theme(app)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == '__main__':
    main()
