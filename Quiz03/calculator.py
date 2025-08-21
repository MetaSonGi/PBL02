# calculator.py
# iPhone 계산기 레이아웃을 본뜬 PyQt6 UI (동일 배치/출력 형태, 색상/모양은 유사하게만)
# 이번 과제 요구: 버튼 클릭 시 표시창에 입력만 되도록, 실제 계산 기능은 구현하지 않음.

from PyQt6.QtWidgets import (
    QApplication, QWidget, QGridLayout, QPushButton, QLineEdit, QSizePolicy
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
import sys

class CalculatorUI(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Calculator (iPhone-like Layout)")
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
        self.display.setMaxLength(32)
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
        grid.addWidget(self.display, 0, 0, 1, 4)

        # iPhone Calculator button layout (labels only; behavior = input to display)
        # Row 1: AC  ±  %   ÷
        # Row 2: 7   8  9   ×
        # Row 3: 4   5  6   −
        # Row 4: 1   2  3   +
        # Row 5: 0 (span 2)  .   =
        layout_labels = [
            ["AC", "±", "%", "÷"],
            ["7", "8", "9", "×"],
            ["4", "5", "6", "−"],
            ["1", "2", "3", "+"],
            ["0", ".", "="],  # 0은 두 칸(span 2)
        ]

        # Helper to create a button
        def make_btn(text, role="digit"):
            btn = QPushButton(text)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setMinimumHeight(56)
            btn.setFont(QFont("Segoe UI", 16))

            # Style by role (roughly mimicking iPhone palette)
            if role == "op":
                btn.setStyleSheet("""
                    QPushButton {
                        background: #f39c12; color: white; border: none; border-radius: 12px;
                    } QPushButton:pressed { filter: brightness(85%); }
                """)
            elif role == "func":
                btn.setStyleSheet("""
                    QPushButton {
                        background: #a5a5a5; color: black; border: none; border-radius: 12px;
                    } QPushButton:pressed { filter: brightness(90%); }
                """)
            else:  # digit
                btn.setStyleSheet("""
                    QPushButton {
                        background: #333; color: white; border: none; border-radius: 12px;
                    } QPushButton:pressed { filter: brightness(85%); }
                """)
            btn.clicked.connect(lambda _, t=text: self.on_button(t))
            return btn

        # Place buttons in grid
        # First functional row
        r = 1
        for c, label in enumerate(layout_labels[0]):
            role = "func" if label in ("AC", "±", "%") else "op"
            grid.addWidget(make_btn(label, role), r, c)

        # Next rows (digits + ops)
        for idx, row in enumerate(layout_labels[1:], start=2):
            if idx < 5:
                # rows 2~4: three digits + right-side operator
                for c, label in enumerate(row):
                    if c < 3:
                        grid.addWidget(make_btn(label, "digit"), idx, c)
                    else:
                        grid.addWidget(make_btn(label, "op"), idx, 3)
            else:
                # last row: 0 (span 2), ., =
                # columns: 0-1 span -> "0", col 2 -> ".", col 3 -> "="
                zero_btn = make_btn("0", "digit")
                grid.addWidget(zero_btn, idx, 0, 1, 2)
                grid.addWidget(make_btn(".", "digit"), idx, 2)
                grid.addWidget(make_btn("=", "op"), idx, 3)

        self.setStyleSheet("background: #000;")
        self.setFixedWidth(360)

    def on_button(self, label: str):
        # Only input behavior (no real calculation)
        if label == "AC":
            self.display.setText("0")
            return

        current = self.display.text()

        if label.isdigit():
            # Append digits
            if current == "0":
                self.display.setText(label)
            else:
                self.display.setText(current + label)
            return

        if label == ".":
            # Insert decimal point only if last token doesn't already contain a dot
            # Simple heuristic: check last number segment
            last = current.split()[-1] if current else ""
            if "." not in last:
                self.display.setText(current + ("" if current.endswith(".") else ".") if last and last.replace(".", "").isdigit() else (current + "." if current and current[-1].isdigit() else (current + "0." if current else "0.")))
            return

        if label in ("+", "−", "×", "÷", "%"):
            # Append operator with spaces for readability (no validation)
            if current and not current.endswith(" "):
                self.display.setText(current + f" {label} ")
            elif current.endswith(" "):
                # replace the trailing operator (optional UX nicety)
                parts = current.rstrip().split(" ")
                if parts:
                    parts[-1] = label
                    self.display.setText(" ".join(parts) + " ")
                else:
                    self.display.setText(current + f"{label} ")
            else:
                # starting with operator -> prepend 0
                self.display.setText(f"0 {label} ")
            return

        if label == "±":
            # Toggle sign of the last number token (display-only)
            tokens = self.display.text().split(" ")
            if tokens:
                # find last numeric token
                for i in range(len(tokens)-1, -1, -1):
                    t = tokens[i]
                    # crude check for number
                    try:
                        float(t)
                        if t.startswith("-"):
                            tokens[i] = t[1:]
                        else:
                            tokens[i] = "-" + t
                        break
                    except ValueError:
                        continue
                self.display.setText(" ".join(tokens))
            return

        if label == "=":
            # Do nothing (no calculation per assignment)
            return


def main():
    app = QApplication(sys.argv)
    w = CalculatorUI()
    w.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
