import numpy as np
from PySide6.QtWidgets import QWidget, QVBoxLayout
import pyqtgraph as pg

class WaterfallWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        
        self.plot_widget = pg.PlotWidget()
        self.layout.addWidget(self.plot_widget)
        
        self.image_item = pg.ImageItem()
        self.plot_widget.addItem(self.image_item)
        
        self.plot_widget.setLabel('bottom', 'Time', units='s')
        self.plot_widget.setLabel('left', 'Frequency', units='kHz')
        self.plot_widget.setBackground('#0D0F16')
        
        # Professional RF Waterfall Colormap
        pos = np.array([0.0, 0.25, 0.5, 0.75, 1.0])
        color = np.array([
            [13, 15, 22, 255],     # Near black / background
            [26, 35, 60, 255],     # Deep navy
            [32, 70, 160, 255],    # Blue
            [58, 134, 255, 255],   # Cyan accent
            [220, 240, 255, 255]   # Light cyan/white peak
        ], dtype=np.ubyte)
        colormap = pg.ColorMap(pos, color)
        
        self.image_item.setLookupTable(colormap.getLookupTable())
        
    def update_plot(self, times: np.ndarray, frequencies: np.ndarray, power_db: np.ndarray):
        if len(times) == 0 or len(frequencies) == 0:
            return
            
        freqs_khz = frequencies / 1000.0
        
        if power_db.shape[0] == len(frequencies):
            power_db = power_db.T
            
        self.image_item.setImage(power_db, autoLevels=True)
        
        time_span = times[-1] - times[0] if len(times) > 1 else 1.0
        freq_span = freqs_khz[-1] - freqs_khz[0] if len(freqs_khz) > 1 else 1.0
        
        self.image_item.setRect(pg.QtCore.QRectF(times[0], freqs_khz[0], time_span, freq_span))
        self.plot_widget.autoRange()

    def clear_plot(self):
        self.image_item.clear()
