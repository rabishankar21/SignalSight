import re

with open("signalsight/gui/main_window.py", "r") as f:
    mw = f.read()

# Remove the hardcoded minimum heights that are causing layout engine conflicts (overlap)
mw = mw.replace("demod_group.setMinimumHeight(240)\n        ", "")
mw = mw.replace("demod_group.setMinimumHeight(220)\n        ", "")

# We can also reduce the extra spacing slightly so it doesn't push too hard
mw = mw.replace("dl_layout.addSpacing(24)  # Increased spacing to stretch the card downwards", "dl_layout.addStretch(1)")
mw = mw.replace("al_layout.addSpacing(16)  # Increased spacing for balance", "al_layout.addStretch(1)")

with open("signalsight/gui/main_window.py", "w") as f:
    f.write(mw)
    
print("Removed hardcoded heights and replaced fixed spacing with dynamic stretch")
