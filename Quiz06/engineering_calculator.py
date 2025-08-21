# engineering_calculator.py
# PyQt6: Engineering (scientific) calculator UI + logic subset
# - Calculator: basic engine (digits, dot, AC, sign, + − × ÷, %, =)
# - EngineeringCalculator(Calculator): scientific functions
#   (sin, cos, tan, sinh, cosh, tanh, π insert, x², x³) with DEG/RAD toggle
# - Remaining scientific buttons are visually appended or stubbed (not implemented)

from PyQt6.QtWidgets import QApplication, QWidget, QGridLayout, QPushButton, QLineEdit, QSizePolicy, QMessageBox
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
import sys, math, random

# ---------------- Core Calculator ----------------
class Calculator:
    def __init__(self, update_display_callback):
        self.update_display = update_display_callback
        self.reset()

    def reset(self):
        self.acc = 0.0
        self.current = "0"
        self.pending_op = None  # '+', '−', '×', '÷'
        self.just_evaluated = False
        self.update_display(self.current)

    def _current_value(self):
        try:
            return float(self.current)
        except ValueError:
            # handle things like "Error"
            return 0.0

    def _set_current_from_value(self, val: float):
        if math.isfinite(val):
            text = f"{val:.12g}"
        else:
            text = "Error"
        self.current = text
        self.update_display(self.current)

    # Input
    def input_digit(self, d: str):
        if self.just_evaluated and self.pending_op is None:
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

    def negative_positive(self):
        if self.current.startswith("-"):
            self.current = self.current[1:] or "0"
        else:
            if self.current != "0":
                self.current = "-" + self.current
        self.update_display(self.current)

    def percent(self):
        cur = self._current_value()
        if self.pending_op is not None:
            base = self.acc
            cur = base * (cur / 100.0)
        else:
            cur = cur / 100.0
        self._set_current_from_value(cur)

    # Operators
    def _apply_pending(self):
        if self.pending_op is None:
            return
        a, b = self.acc, self._current_value()
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
            self.reset(); return
        if self.pending_op is None:
            self.acc = self._current_value()
            self.pending_op = op_symbol
            self.just_evaluated = False
            self.current = "0"
        else:
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

    def equal(self):
        if self.current == "Error":
            self.reset(); return
        if self.pending_op is None:
            self._set_current_from_value(self._current_value())
            self.just_evaluated = True
            return
        status = self._apply_pending()
        if status == "error":
            return
        self.pending_op = None
        self.just_evaluated = True

# -------------- Engineering Calculator --------------
class EngineeringCalculator(Calculator):
    """
    추가/정리된 공학용 기능(예시, 총 30개 정리용 목록):
    1) 괄호 (, )             2) 메모리(clear, m+, m-, mr)
    3) 2nd                   4) x²
    5) x³                    6) x^y
    7) e^x                   8) 10^x
    9) 1/x                   10) ²√x
    11) ³√x                  12) y√x
    13) ln                   14) log₁₀
    15) x!                   16) sin
    17) cos                  18) tan
    19) sinh                 20) cosh
    21) tanh                 22) Rand
    23) e (상수)             24) EE (지수 표기 입력)
    25) Rad                  26) Deg
    27) π (상수)             28) %, ± (기본 포함)
    29) = (평가)             30) AC (초기화)

    이 중 필수 구현:
      - sin, cos, tan, sinh, cosh, tanh
      - π 삽입
      - x² (square), x³ (cube)
    """
    def __init__(self, update_display_callback):
        super().__init__(update_display_callback)
        self.is_degree_mode = True  # 기본 Deg

    # ---- Helpers ----
    def _angle(self, x: float) -> float:
        return math.radians(x) if self.is_degree_mode else x

    # ---- Implemented scientific methods ----
    def insert_pi(self):
        # 현재 입력을 π로 치환 (iOS는 상황 따라 다르지만 단순화)
        self.current = f"{math.pi:.12g}"
        self.update_display(self.current)

    def square(self):
        val = self._current_value()
        self._set_current_from_value(val * val)

    def cube(self):
        val = self._current_value()
        self._set_current_from_value(val * val * val)

    def sin(self):
        x = self._angle(self._current_value())
        self._set_current_from_value(math.sin(x))

    def cos(self):
        x = self._angle(self._current_value())
        self._set_current_from_value(math.cos(x))

    def tan(self):
        x = self._angle(self._current_value())
        try:
            self._set_current_from_value(math.tan(x))
        except Exception:
            self.current = "Error"; self.update_display(self.current)

    def sinh(self):
        x = self._current_value()
        self._set_current_from_value(math.sinh(x))

    def cosh(self):
        x = self._current_value()
        self._set_current_from_value(math.cosh(x))

    def tanh(self):
        x = self._current_value()
        self._set_current_from_value(math.tanh(x))

    # Mode toggles
    def set_deg(self): self.is_degree_mode = True
    def set_rad(self): self.is_degree_mode = False

# -------------- UI ----------------
class EngineeringCalculatorUI(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Engineering Calculator (iPhone-like Landscape)")
        self.build_ui()
        self.calculator = EngineeringCalculator(self.set_display)

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
        self.display.setMaxLength(64)
        self.display.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self.display.setStyleSheet("""
            QLineEdit { padding: 12px; border: none; background: #111; color: white; border-radius: 8px; }
        """)
        grid.addWidget(self.display, 0, 0, 1, 10)

        # Layout rows (10 columns)
        rows = [
            ["(", ")", "mc", "m+", "m-", "mr", "AC", "±", "%", "÷"],
            ["2nd", "x²", "x³", "x^y", "e^x", "10^x", "7", "8", "9", "×"],
            ["1/x", "²√x", "³√x", "y√x", "ln", "log₁₀", "4", "5", "6", "−"],
            ["x!", "sin", "cos", "tan", "sinh", "cosh", "1", "2", "3", "+"],
            ["Rand", "e", "EE", "Rad", "Deg", "π", "0", "0span2", ".", "="],
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

        # Row 1
        r = 1
        for c, label in enumerate(rows[0]):
            role = "func" if label in ("(", ")", "mc", "m+", "m-", "mr", "AC", "±", "%") else "op"
            grid.addWidget(make_btn(label, role if role!="func" else ("op" if label in ("%","÷") else "func")), r, c)

        # Row 2~4
        for ridx in range(1, 4):
            r = ridx + 1
            for c, label in enumerate(rows[ridx]):
                role = "digit"
                if label in ("×","−","+","÷","="):
                    role = "op"
                elif not label.isdigit() and label not in (".","0","0span2"):
                    role = "func"
                grid.addWidget(make_btn(label, role), r, c)

        # Row 5 (handle 0 span)
        r = 5
        for c, label in enumerate(rows[4]):
            if label == "0span2":
                continue
            if label == "0":
                zero_btn = make_btn("0", "digit")
                grid.addWidget(zero_btn, r, c, 1, 2)
            else:
                role = "digit" if label.isdigit() or label == "." else ("op" if label in ("=",) else "func")
                grid.addWidget(make_btn(label, role), r, c)

        self.setStyleSheet("background: #000;")
        self.setFixedWidth(820)

    # -------------- Button wiring --------------
    def on_button(self, label: str):
        c = self.calculator

        # Basics
        if label == "AC": c.reset(); return
        if label == "±": c.negative_positive(); return
        if label == "%": c.percent(); return
        if label in ("+", "−", "×", "÷"):
            { "+": c.add, "−": c.subtract, "×": c.multiply, "÷": c.divide }[label](); return
        if label == "=": c.equal(); return
        if label == ".": c.input_dot(); return
        if label.isdigit(): c.input_digit(label); return

        # Mode toggles
        if label == "Deg": c.set_deg(); self._toast("Degrees mode"); return
        if label == "Rad": c.set_rad(); self._toast("Radians mode"); return

        # Implemented scientific
        if label == "π": c.insert_pi(); return
        if label == "x²": c.square(); return
        if label == "x³": c.cube(); return
        if label == "sin": c.sin(); return
        if label == "cos": c.cos(); return
        if label == "tan": c.tan(); return
        if label == "sinh": c.sinh(); return
        if label == "cosh": c.cosh(); return
        if label == "tanh": c.tanh(); return

        # Unimplemented sci keys -> visual append or toast
        unimpl_funcs = {"2nd","x^y","e^x","10^x","1/x","²√x","³√x","y√x","ln","log₁₀","x!","Rand","e","EE","mc","m+","m-","mr","(",")"}
        if label in unimpl_funcs:
            # For clarity, show a one-time toast when first pressed
            self._toast(f"'{label}' not implemented in this assignment")
            # Visual append for feeling (optional):
            cur = self.display.text()
            sep = "" if (not cur or cur.endswith(" ")) else " "
            self.display.setText(cur + sep + label + " ")
            return

        # Fallback ignore
        return

    def _toast(self, msg: str):
        # Simple info popup (non-blocking would need timers; keep it modal & brief)
        box = QMessageBox(self)
        box.setWindowTitle("Info")
        box.setText(msg)
        box.setStandardButtons(QMessageBox.StandardButton.Ok)
        box.exec()

def main():
    app = QApplication(sys.argv)
    w = EngineeringCalculatorUI()
    w.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
