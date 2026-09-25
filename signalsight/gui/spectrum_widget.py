import numpy as np
from PySide6.QtWidgets import QWidget, QVBoxLayout
import pyqtgraph as pg

class SpectrumWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        
        self.plot_widget = pg.PlotWidget()
        self.layout.addWidget(self.plot_widget)
        
        self.plot_widget.setLabel('bottom', 'Frequency', units='Hz')
        self.plot_widget.setLabel('left', 'Power', units='dBFS')
        self.plot_widget.showGrid(x=True, y=True, alpha=0.15)
        self.plot_widget.setBackground('#0D0F16')
        
        # Grid lines more subtle
        pen_grid = pg.mkPen(color='#292F40', width=1, style=pg.QtCore.Qt.DashLine)
        
        self.plot_curve = self.plot_widget.plot(pen=pg.mkPen('#3A86FF', width=1.5))
        
        self.v_line = pg.InfiniteLine(angle=90, movable=False, pen=pen_grid)
        self.h_line = pg.InfiniteLine(angle=0, movable=False, pen=pen_grid)
        self.plot_widget.addItem(self.v_line, ignoreBounds=True)
        self.plot_widget.addItem(self.h_line, ignoreBounds=True)
        
        self.proxy = pg.SignalProxy(self.plot_widget.scene().sigMouseMoved, rateLimit=60, slot=self.mouse_moved)
        self.current_x = np.array([])
        self.current_y = np.array([])

    def mouse_moved(self, evt):
        pos = evt[0]
        if self.plot_widget.sceneBoundingRect().contains(pos):
            mouse_point = self.plot_widget.plotItem.vb.mapSceneToView(pos)
            x_val = mouse_point.x()
            y_val = mouse_point.y()
            self.v_line.setPos(x_val)
            self.h_line.setPos(y_val)


    def update_plot(self, frequencies: np.ndarray, psd_db: np.ndarray):
        self.current_x = frequencies
        self.current_y = psd_db
        if len(frequencies) > 0 and max(frequencies) >= 1000:
            self.plot_widget.setLabel('bottom', 'Frequency', units='kHz')
            freqs = frequencies / 1000.0
        else:
            self.plot_widget.setLabel('bottom', 'Frequency', units='Hz')
            freqs = frequencies
        self.plot_curve.setData(freqs, psd_db)
        self.plot_widget.autoRange(padding=0.1)

    def clear_plot(self):
        self.plot_curve.setData([], [])
        self.current_x = np.array([])
        self.current_y = np.array([])
