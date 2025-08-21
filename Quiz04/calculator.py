# calculator.py
# PyQt6 iPhone-like calculator with working logic.
# - Layout matches iPhone (placement/output). Colors/styles approximate.
# - Implements: add, subtract, multiply, divide, reset, negative_positive, percent, equal
# - Digits accumulate, single decimal point handled.

from PyQt6.QtWidgets import QApplication, QWidget, QGridLayout, QPushButton, QLineEdit, QSizePolicy
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
import sys

class Calculator:
    """
    Core calculation engine/state.
    Methods required:
      - add(), subtract(), multiply(), divide()
      - reset(), negative_positive(), percent(), equal()
    """
    def __init__(self, update_display_callback):
        self.update_display = update_display_callback  # function(str) -> None
        self.reset()

    def reset(self):
        self.acc = 0.0            # accumulator
        self.current = "0"        # current input as string
        self.pending_op = None    # one of ('+', '-', '×', '÷')
        self.just_evaluated = False
        self.update_display(self.current)

    # Helper conversions
    def _current_value(self):
        try:
            return float(self.current)
        except ValueError:
            return 0.0

    def _set_current_from_value(self, val: float):
        # Trim trailing .0
        text = f"{val:.12g}"  # avoid scientific notation for typical range
        self.current = text
        self.update_display(self.current)

    # Number & dot inputs
    def input_digit(self, d: str):
        if self.just_evaluated and self.pending_op is None:
            # Start new entry after equals
            self.current = "0"
            self.just_evaluated = False

        if self.current == "0":
            self.current = d
        else:
            self.current += d
        self.update_display(self.current)

    def input_dot(self):
        if self.just_evaluated and self.pending_op is None:
            self.current = "0"
            self.just_evaluated = False

        if "." not in self.current:
            self.current += "." if self.current else "0."
            self.update_display(self.current)

    # Sign toggle
    def negative_positive(self):
        if self.current.startswith("-"):
            self.current = self.current[1:] or "0"
        else:
            if self.current != "0":
                self.current = "-" + self.current
        self.update_display(self.current)

    # Percent behavior similar to iOS:
    # - If there is a pending operator and a current number, interpret as (acc * current/100)
    # - Else, simply current = current/100
    def percent(self):
        cur = self._current_value()
        if self.pending_op is not None:
            base = self.acc
            cur = base * (cur / 100.0)
        else:
            cur = cur / 100.0
        self._set_current_from_value(cur)

    # Operator handling
    def _apply_pending(self):
        if self.pending_op is None:
            return
        a = self.acc
        b = self._current_value()
        try:
            if self.pending_op == "+":
                res = a + b
            elif self.pending_op == "−":
                res = a - b
            elif self.pending_op == "×":
                res = a * b
            elif self.pending_op == "÷":
                if b == 0.0:
                    raise ZeroDivisionError
                res = a / b
            else:
                return
        except ZeroDivisionError:
            self.current = "Error"
            self.acc = 0.0
            self.pending_op = None
            self.just_evaluated = True
            self.update_display(self.current)
            return "error"

        self.acc = res
        self._set_current_from_value(res)

    def _press_operator(self, op_symbol: str):
        if self.current == "Error":
            self.reset()
            return

        if self.pending_op is None:
            # First operator: move current to accumulator
            self.acc = self._current_value()
            self.pending_op = op_symbol
            self.just_evaluated = False
            self.current = "0"
        else:
            # Chain: apply pending op with current, then set new op
            status = self._apply_pending()
            if status == "error":
                return
            self.pending_op = op_symbol
            self.current = "0"
            self.just_evaluated = False

    def add(self): self._press_operator("+")
    def subtract(self): self._press_operator("−")
    def multiply(self): self._press_operator("×")
    def divide(self): self._press_operator("÷")

    # Equals
    def equal(self):
        if self.current == "Error":
            self.reset()
            return
        if self.pending_op is None:
            # Nothing to do; keep current
            self._set_current_from_value(self._current_value())
            self.just_evaluated = True
            return
        status = self._apply_pending()
        if status == "error":
            return
        self.pending_op = None
        self.just_evaluated = True
        # After equals, acc holds result, current already updated

class CalculatorUI(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Calculator (iPhone-like Layout)")
        self.build_ui()
        self.calculator = Calculator(self.set_display)

    def set_display(self, text: str):
        self.display.setText(text)

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

        # Layout labels (same placement as iPhone)
        rows = [
            ["AC", "±", "%", "÷"],
            ["7", "8", "9", "×"],
            ["4", "5", "6", "−"],
            ["1", "2", "3", "+"],
            ["0", ".", "="],
        ]

        def make_btn(text, role="digit"):
            btn = QPushButton(text)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setMinimumHeight(56)
            btn.setFont(QFont("Segoe UI", 16))
            if role == "op":
                btn.setStyleSheet("QPushButton { background: #f39c12; color: white; border: none; border-radius: 12px; }")
            elif role == "func":
                btn.setStyleSheet("QPushButton { background: #a5a5a5; color: black; border: none; border-radius: 12px; }")
            else:
                btn.setStyleSheet("QPushButton { background: #333; color: white; border: none; border-radius: 12px; }")
            btn.clicked.connect(lambda _, t=text: self.on_button(t))
            return btn

        # Row 1 (functions/operators)
        r = 1
        for c, label in enumerate(rows[0]):
            role = "func" if label in ("AC", "±", "%") else "op"
            grid.addWidget(make_btn(label, role), r, c)

        # Rows 2~4
        for idx, row in enumerate(rows[1:], start=2):
            if idx < 5:
                for c, label in enumerate(row):
                    if c < 3:
                        grid.addWidget(make_btn(label, "digit"), idx, c)
                    else:
                        grid.addWidget(make_btn(label, "op"), idx, 3)
            else:
                zero_btn = make_btn("0", "digit")
                grid.addWidget(zero_btn, idx, 0, 1, 2)
                grid.addWidget(make_btn(".", "digit"), idx, 2)
                grid.addWidget(make_btn("=", "op"), idx, 3)

        self.setStyleSheet("background: #000;")
        self.setFixedWidth(360)

    def on_button(self, label: str):
        c = self.calculator
        if label == "AC":
            c.reset(); return
        if label == "±":
            c.negative_positive(); return
        if label == "%":
            c.percent(); return
        if label in ("+", "−", "×", "÷"):
            {
                "+": c.add,
                "−": c.subtract,
                "×": c.multiply,
                "÷": c.divide
            }[label](); return
        if label == "=":
            c.equal(); return
        if label == ".":
            c.input_dot(); return
        if label.isdigit():
            c.input_digit(label); return
        # Fallback: ignore

def main():
    app = QApplication(sys.argv)
    w = CalculatorUI()
    w.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
