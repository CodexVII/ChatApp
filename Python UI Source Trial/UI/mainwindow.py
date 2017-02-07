# -*- coding: utf-8 -*-
from PyQt4 import QtGui

import sys
import ui_chat

class MainDialog(QtGui.QMainWindow, ui_chat.Ui_MainWindow):
    
    def __init__(self, parent=None):
        super(MainDialog, self).__init__(parent)
        self.setupUi(self)
        
app = QtGui.QApplication(sys.argv)
form = MainDialog()
form.show()
app.exec_()