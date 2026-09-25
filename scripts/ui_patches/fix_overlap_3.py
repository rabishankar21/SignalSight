import re

with open("signalsight/gui/main_window.py", "r") as f:
    mw = f.read()

mw = mw.replace("dl_layout.addStretch(1)", "dl_layout.addSpacing(16)")
mw = mw.replace("al_layout.addStretch(1)", "al_layout.addSpacing(16)")

with open("signalsight/gui/main_window.py", "w") as f:
    f.write(mw)
    
print("Reverted to addSpacing")
