import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))  # noqa
from examples.example_calculator.calc_window import CalculatorWindow
from qtpy.QtWidgets import QApplication


if __name__ == '__main__':
    app = QApplication(sys.argv)

    # print(QStyleFactory.keys())
    app.setStyle('Fusion')

    wnd = CalculatorWindow()
    wnd.show()

    sys.exit(app.exec_())
