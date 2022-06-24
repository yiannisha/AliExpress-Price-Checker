#!/usr/bin/env python3

import sys

# inner modules
from ui import app

# third party modules
from PyQt5.QtWidgets import QApplication

def main () -> None:
    # set up the app ui
    my_app = QApplication(sys.argv)
    ex = app.App()
    # ex.setButtonFunction(on_click)
    ex.show()

    sys.exit(my_app.exec_())

if __name__ == '__main__':
    main()
