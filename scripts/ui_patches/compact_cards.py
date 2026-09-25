import re

with open("signalsight/gui/main_window.py", "r") as f:
    mw = f.read()

# 1. Remove extra spacing before buttons
mw = mw.replace("al_layout.addSpacing(16)\n        al_layout.addWidget(btn_analyze)", "al_layout.addWidget(btn_analyze)")
mw = mw.replace("dl_layout.addSpacing(16)\n        dl_layout.addWidget(btn_demod)", "dl_layout.addWidget(btn_demod)")

# 2. Reduce margins inside the group_cards to save vertical space
mw = mw.replace("al_layout.setContentsMargins(16, 16, 16, 16)", "al_layout.setContentsMargins(16, 12, 16, 12)")
mw = mw.replace("dl_layout.setContentsMargins(16, 16, 16, 16)", "dl_layout.setContentsMargins(16, 12, 16, 12)")
mw = mw.replace("fec_layout.setContentsMargins(16, 16, 16, 16)", "fec_layout.setContentsMargins(16, 12, 16, 12)")

# 3. Reduce spacing after titles to save vertical space
mw = mw.replace("al_layout.addSpacing(8)", "al_layout.addSpacing(4)")
mw = mw.replace("dl_layout.addSpacing(8)", "dl_layout.addSpacing(4)")
mw = mw.replace("fec_layout.addSpacing(4)", "fec_layout.addSpacing(2)")

# 4. Reduce right panel global padding to give more room
mw = mw.replace("right_layout.setContentsMargins(24, 32, 24, 32)", "right_layout.setContentsMargins(24, 24, 24, 24)")
mw = mw.replace("right_layout.setSpacing(24)", "right_layout.setSpacing(16)")

with open("signalsight/gui/main_window.py", "w") as f:
    f.write(mw)
    
print("Compacted cards to prevent layout squishing")
