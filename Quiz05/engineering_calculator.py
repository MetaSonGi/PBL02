# engineering_calculator.py
# PyQt6 UI: iPhone 가로(공학용) 계산기 레이아웃을 본뜬 배치
# - 색상/모양은 유사하게만, 배치/출력 형태는 동일 컨셉
# - 버튼 클릭 시 표시창에 입력만 반영 (실제 계산 기능 없음)

from PyQt6.QtWidgets import QApplication, QWidget, QGridLayout, QPushButton, QLineEdit, QSizePolicy
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
import sys

class EngineeringCalculatorUI(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Engineering Calculator (iPhone-like Landscape)")
        self.build_ui()

    def build_ui(self):
        grid = QGridLayout(self)
        grid.setSpacing(6)
        grid.setContentsMargins(12, 12, 12, 12)

        # Display
        self.display = QLineEdit("0")
        self.display.setReadOnly(True)
        self.display.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self.display.setFont(QFont("Segoe UI", 28))
        self.display.setMaxLength(64)
        self.display.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self.display.setStyleSheet("""
            QLineEdit {
                padding: 12px;
                border: none;
                background: #111;
                color: white;
                border-radius: 8px;
            }
        """)
        grid.addWidget(self.display, 0, 0, 1, 10)  # span 10 columns

        # Approximate iPhone landscape scientific layout (10 columns)
        rows = [
            ["(", ")", "mc", "m+", "m-", "mr", "AC", "±", "%", "÷"],
            ["2nd", "x²", "x³", "x^y", "e^x", "10^x", "7", "8", "9", "×"],
            ["1/x", "²√x", "³√x", "y√x", "ln", "log₁₀", "4", "5", "6", "−"],
            ["x!", "sin", "cos", "tan", "sinh", "cosh", "1", "2", "3", "+"],
            ["Rand", "e", "EE", "Rad", "Deg", "π", "0", "0span2", ".", "="],  # "0span2" placeholder
        ]

        def make_btn(text, role="digit"):
            btn = QPushButton(text)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setMinimumHeight(52)
            btn.setFont(QFont("Segoe UI", 14))
            if role == "op":
                btn.setStyleSheet("QPushButton { background: #f39c12; color: white; border: none; border-radius: 10px; }")
            elif role == "func":
                btn.setStyleSheet("QPushButton { background: #a5a5a5; color: black; border: none; border-radius: 10px; }")
            else:
                btn.setStyleSheet("QPushButton { background: #333; color: white; border: none; border-radius: 10px; }")
            btn.clicked.connect(lambda _, t=text: self.on_button(t))
            return btn

        # Row 1 (memory + control + op)
        r = 1
        for c, label in enumerate(rows[0]):
            role = "func" if label in ("(", ")", "mc", "m+", "m-", "mr", "AC", "±", "%") else "op"
            grid.addWidget(make_btn(label, role if role!="func" else ("op" if label in ("%","÷") else "func")), r, c)

        # Row 2~4
        for ridx in range(1, 4):
            r = ridx + 1
            for c, label in enumerate(rows[ridx]):
                role = "digit"  # default
                if label in ("×","−","+","÷"):
                    role = "op"
                elif not label.isdigit():
                    role = "func"
                grid.addWidget(make_btn(label, role), r, c)

        # Row 5: handle 0 spanning two columns
        r = 5
        for c, label in enumerate(rows[4]):
            if label == "0span2":
                # skip: handled by span with the previous "0"
                continue
            if label == "0":
                zero_btn = make_btn("0", "digit")
                grid.addWidget(zero_btn, r, c, 1, 2)  # span 2 columns
            else:
                role = "digit" if label.isdigit() or label == "." else ("op" if label in ("=",) else "func")
                grid.addWidget(make_btn(label, role), r, c)

        self.setStyleSheet("background: #000;")
        self.setFixedWidth(820)  # wider for landscape

    def on_button(self, label: str):
        # Behavior: numeric input accumulation, dot only once in current number,
        # AC clears, ± toggles sign of last number token.
        if label == "AC":
            self.display.setText("0")
            return

        if label == "±":
            tokens = self.display.text().split(" ")
            # try to toggle the last numeric-looking token
            for i in range(len(tokens)-1, -1, -1):
                t = tokens[i]
                try:
                    float(t)
                    tokens[i] = t[1:] if t.startswith("-") else ("-" + t if t != "0" else t)
                    break
                except ValueError:
                    continue
            self.display.setText(" ".join(tokens))
            return

        if label == ".":
            # only allow one dot in the last number segment
            current = self.display.text()
            # find last contiguous number segment (split by spaces and operators)
            last = current.split(" ")
            last_token = last[-1] if last else ""
            if "." not in last_token:
                if not last_token or not all(ch.isdigit() or ch == "-" for ch in last_token):
                    # start a new 0.
                    self.display.setText((current + (" " if current and not current.endswith(" ") else "")) + "0.")
                else:
                    self.display.setText(current + ".")
            return

        if label.isdigit():
            current = self.display.text()
            if current == "0":
                self.display.setText(label)
            else:
                self.display.setText(current + label)
            return

        if label in ("+", "−", "×", "÷", "%", "=", "(", ")"):
            current = self.display.text()
            sep = "" if (not current or current.endswith(" ")) else " "
            self.display.setText(current + sep + label + " ")
            return

        # function-like tokens: append with trailing "(" when appropriate (visual only)
        func_with_paren = {"sin","cos","tan","sinh","cosh","ln","log₁₀","x²","x³","x^y","e^x","10^x",
                           "1/x","²√x","³√x","y√x","x!","EE","π","e","Rand","Rad","Deg","2nd","mc","m+","m-","mr"}
        current = self.display.text()
        token = label + "(" if label in {"sin","cos","tan","sinh","cosh","ln"} else label
        sep = "" if (not current or current.endswith(" ")) else " "
        self.display.setText(current + sep + token + (" " if token.endswith("(") else " "))

def main():
    app = QApplication(sys.argv)
    w = EngineeringCalculatorUI()
    w.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
