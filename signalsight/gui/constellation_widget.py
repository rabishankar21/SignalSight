import numpy as np
from PySide6.QtWidgets import QWidget, QVBoxLayout
import pyqtgraph as pg

class ConstellationWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        
        self.plot_widget = pg.PlotWidget()
        self.layout.addWidget(self.plot_widget)
        
        self.plot_widget.setLabel('bottom', 'In-Phase (I)')
        self.plot_widget.setLabel('left', 'Quadrature (Q)')
        self.plot_widget.showGrid(x=True, y=True, alpha=0.15)
        self.plot_widget.setBackground('#0D0F16')
        self.plot_widget.setAspectLocked(True, ratio=1)
        
        # Unit circle (highly subtle)
        theta = np.linspace(0, 2*np.pi, 100)
        x_circle = np.cos(theta)
        y_circle = np.sin(theta)
        self.plot_widget.plot(x_circle, y_circle, pen=pg.mkPen(color=(41, 47, 64, 80), width=0.8, style=pg.QtCore.Qt.DashLine))
        
        # Crosshairs
        self.plot_widget.addItem(pg.InfiniteLine(angle=90, movable=False, pen=pg.mkPen(color=(41, 47, 64, 120), width=0.8)))
        self.plot_widget.addItem(pg.InfiniteLine(angle=0, movable=False, pen=pg.mkPen(color=(41, 47, 64, 120), width=0.8)))
        
        self.scatter = pg.ScatterPlotItem(size=4, pen=None, brush=pg.mkBrush(58, 134, 255, 160))
        self.plot_widget.addItem(self.scatter)

    def update_plot(self, symbols: np.ndarray):
        x = np.real(symbols)
        y = np.imag(symbols)
        self.scatter.setData(x, y)
        self.plot_widget.autoRange(padding=0.1)

    def clear_plot(self):
        self.scatter.setData([], [])
