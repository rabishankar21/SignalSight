import re

with open("signalsight/gui/main_window.py", "r") as f:
    mw = f.read()

# Fix Overview layout margins so cards don't touch the edge
mw = mw.replace("overview_layout.setContentsMargins(0, 16, 0, 0)", "overview_layout.setContentsMargins(32, 24, 32, 24)")

with open("signalsight/gui/main_window.py", "w") as f:
    f.write(mw)
    
print("Fixed overview margins")
