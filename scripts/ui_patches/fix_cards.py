import re

with open("signalsight/gui/main_window.py", "r") as f:
    content = f.read()

# Fix metric cards layout
old_metric = """        def create_metric_card(title, lbl_val):
            card = QFrame()
            card.setProperty("class", "metric_card")
            card_lay = QVBoxLayout(card)
            card_lay.setContentsMargins(20, 20, 20, 20)
            t = QLabel(title)
            t.setProperty("class", "metric_label")
            lbl_val.setProperty("class", "metric_value")
            card_lay.addWidget(t)
            card_lay.addSpacing(4)
            card_lay.addWidget(lbl_val)
            card_lay.addStretch()
            return card"""
            
new_metric = """        def create_metric_card(title, lbl_val):
            card = QFrame()
            card.setProperty("class", "metric_card")
            card_lay = QVBoxLayout(card)
            card_lay.setContentsMargins(20, 20, 20, 20)
            t = QLabel(title)
            t.setProperty("class", "metric_label")
            lbl_val.setProperty("class", "metric_value")
            
            # Center alignments
            t.setAlignment(Qt.AlignCenter)
            lbl_val.setAlignment(Qt.AlignCenter)
            card_lay.setAlignment(Qt.AlignCenter)
            
            card_lay.addWidget(t)
            card_lay.addSpacing(8)
            card_lay.addWidget(lbl_val)
            return card"""
            
content = content.replace(old_metric, new_metric)

with open("signalsight/gui/main_window.py", "w") as f:
    f.write(content)

print("Fixed main window cards")
