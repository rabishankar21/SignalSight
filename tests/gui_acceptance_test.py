import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import numpy as np
import time
from unittest.mock import patch
from PySide6.QtWidgets import QApplication, QMessageBox
from PySide6.QtCore import QTimer

# Create QApplication before importing GUI components
app = QApplication.instance()
if app is None:
    app = QApplication(sys.argv)

from signalsight.gui.main_window import MainWindow
from signalsight.utils.signal_generator import generate_signal
from signalsight.demod.viterbi import encode
import pyqtgraph as pg

def wait_for_worker(window, timeout_sec=10):
    start = time.time()
    while window.worker is not None and window.worker.isRunning():
        app.processEvents()
        if time.time() - start > timeout_sec:
            raise TimeoutError("Worker did not finish in time")
        time.sleep(0.01)
    app.processEvents()

def run_tests():
    print("Starting GUI Acceptance Tests...")
    
    # Generate test files
    np.random.seed(42)
    # 1. Normal BPSK
    bpsk_samples, _, _ = generate_signal('BPSK', 10000, 400000, 1000, 20.0, seed=42)
    bpsk_samples = bpsk_samples.astype(np.complex64)
    with open('bpsk_test.iq', 'wb') as f:
        bpsk_samples.tofile(f)
        
    # 2. Normal QPSK
    qpsk_samples, _, _ = generate_signal('QPSK', 10000, 400000, 1000, 20.0, seed=42)
    qpsk_samples = qpsk_samples.astype(np.complex64)
    with open('qpsk_test.iq', 'wb') as f:
        qpsk_samples.tofile(f)
        
    # 3. Encoded BPSK
    info_bits = np.random.randint(0, 2, 500).astype(np.uint8)
    enc_bits = encode(info_bits)
    
    sps = 4
    symbols = np.where(enc_bits == 0, 1.0 + 0j, -1.0 + 0j)
    up_symbols = np.zeros(len(symbols) * sps, dtype=complex)
    up_symbols[::sps] = symbols
    from signalsight.demod.bpsk import design_rrc_filter
    h_rrc = design_rrc_filter(0.35, 10, sps)
    baseband = np.convolve(up_symbols, h_rrc, mode='same')
    encoded_samples = (baseband + 0.1 * (np.random.randn(len(baseband)) + 1j * np.random.randn(len(baseband)))).astype(np.complex64)
    with open('encoded_bpsk_test.iq', 'wb') as f:
        encoded_samples.tofile(f)
    
    # 4. Invalid file
    with open('invalid_test.iq', 'wb') as f:
        f.write(b"NOT A SIGNAL FILE! JUST SOME GARBAGE BYTES")

    # TEST 1: App startup
    print("TEST 1: App startup")
    try:
        window = MainWindow()
        window.show()
        app.processEvents()
        print("  - MainWindow instantiated and shown.")
    except Exception as e:
        print(f"FAIL: App startup threw exception: {e}")
        return

    # TEST 2: Real IQ/WAV input
    print("TEST 2: File loading")
    with patch('PySide6.QtWidgets.QFileDialog.getOpenFileName', return_value=('bpsk_test.iq', '')):
        with patch('PySide6.QtWidgets.QInputDialog.getDouble', return_value=(400000.0, True)):
            window.on_open_file()
            app.processEvents()
            # on_open_file triggers on_run_analysis which spawns a worker
            wait_for_worker(window)
            
    if window.current_samples is not None and len(window.current_samples) == len(bpsk_samples):
        print("  - File loaded successfully.")
    else:
        print("FAIL: File not loaded correctly.")
        
    # TEST 3: Visualization
    print("TEST 3: Visualization")
    # Check spectrum
    spec_item = window.tab_spectrum.plot_widget.plotItem.listDataItems()[0]
    spec_data = spec_item.getData()
    if spec_data[0] is not None and len(spec_data[0]) > 0:
        print("  - Spectrum has data.")
    else:
        print("FAIL: Spectrum has no data.")
        
    # Check waterfall
    wf_item = window.tab_waterfall.image_item
    if wf_item.image is not None and wf_item.image.size > 0:
        print("  - Waterfall has data.")
    else:
        print("FAIL: Waterfall has no data.")

    # TEST 4: Parameter estimation
    print("TEST 4: Parameter estimation")
    print(f"  - SNR Label: {window.lbl_snr.text()}")
    print(f"  - BW Label: {window.lbl_bw.text()}")
    print(f"  - SymRate Label: {window.lbl_symrate.text()}")
    if "dB" in window.lbl_snr.text() and "-" not in window.lbl_snr.text():
        print("  - Parameter estimation updated UI.")
    else:
        print("FAIL: Parameter estimation missing.")

    # TEST 5: Modulation classification
    print("TEST 5: Modulation classification")
    print(f"  - Mod Label: {window.lbl_mod.text()}")
    if "BPSK" in window.lbl_mod.text():
        print("  - Classification correct for BPSK.")
    else:
        print("FAIL: Classification incorrect.")

    # TEST 6: Demodulation (BPSK)
    print("TEST 6: Demodulation (BPSK)")
    window.combo_mod.setCurrentText("BPSK")
    window.chk_viterbi.setChecked(False)
    window.on_demodulate()
    wait_for_worker(window)
    
    # Check constellation
    const_item = window.tab_constellation.scatter
    const_data = const_item.getData()
    if const_data[0] is not None and len(const_data[0]) > 0:
        print("  - Constellation has data.")
    else:
        print("FAIL: Constellation has no data.")
        
    # Check bitstream
    bits_text = window.tab_bitstream.text_edit.toPlainText()
    print(f"  - Recovered BPSK bits length: {len(bits_text)}")
    if len(bits_text) > 500:
        print("  - BPSK demodulation successful.")
    else:
        print("FAIL: BPSK bits not shown.")
        
    # Demodulation (QPSK)
    print("TEST 6b: Demodulation (QPSK)")
    with patch('PySide6.QtWidgets.QFileDialog.getOpenFileName', return_value=('qpsk_test.iq', '')):
        with patch('PySide6.QtWidgets.QInputDialog.getDouble', return_value=(400000.0, True)):
            window.on_open_file()
            wait_for_worker(window)
            
    window.combo_mod.setCurrentText("QPSK")
    window.on_demodulate()
    wait_for_worker(window)
    
    bits_text_qpsk = window.tab_bitstream.text_edit.toPlainText()
    print(f"  - Recovered QPSK bits length: {len(bits_text_qpsk)}")
    if len(bits_text_qpsk) > 1000:
        print("  - QPSK demodulation successful.")
    else:
        print("FAIL: QPSK bits not shown.")
        
    # TEST 7: Viterbi GUI integration
    print("TEST 7: Viterbi GUI integration")
    with patch('PySide6.QtWidgets.QFileDialog.getOpenFileName', return_value=('encoded_bpsk_test.iq', '')):
        with patch('PySide6.QtWidgets.QInputDialog.getDouble', return_value=(400000.0, True)):
            window.on_open_file()
            wait_for_worker(window)
            
    # Disable Viterbi
    window.combo_mod.setCurrentText("BPSK")
    window.chk_viterbi.setChecked(False)
    window.on_demodulate()
    wait_for_worker(window)
    
    raw_bits_len = len(window.tab_bitstream.text_edit.toPlainText().replace(" ", ""))
    print(f"  - Raw bitstream length: {raw_bits_len}")
    
    # Enable Viterbi
    window.chk_viterbi.setChecked(True)
    window.on_demodulate()
    wait_for_worker(window)
    
    vit_bits_len = len(window.tab_bitstream.text_edit.toPlainText().replace(" ", ""))
    status_msg = window.status_bar.currentMessage()
    print(f"  - Viterbi bitstream length: {vit_bits_len}")
    print(f"  - Viterbi status msg: '{status_msg}'")
    
    if vit_bits_len > 0 and vit_bits_len < raw_bits_len * 0.6:
        if "Raw:" in status_msg and "FEC: Viterbi (Phase" in status_msg and "Recovered:" in status_msg:
            print("  - Viterbi GUI integration successful (Output length halved and status updated).")
        else:
            print(f"FAIL: Viterbi status message is wrong: '{status_msg}'")
    else:
        print("FAIL: Viterbi GUI integration failed (length incorrect).")

    # TEST 8: Invalid file handling
    print("TEST 8: Invalid input")
    with patch('PySide6.QtWidgets.QFileDialog.getOpenFileName', return_value=('non_existent_file.iq', '')):
        with patch('PySide6.QtWidgets.QInputDialog.getDouble', return_value=(400000.0, True)):
            with patch('signalsight.gui.main_window.QMessageBox.critical') as mock_critical:
                window.on_open_file()
                app.processEvents()
                if mock_critical.called:
                    print("  - Invalid file gracefully reported via QMessageBox.")
                else:
                    print("FAIL: Invalid file did not trigger QMessageBox.")
                    
    print("ALL TESTS COMPLETED.")

if __name__ == "__main__":
    run_tests()
