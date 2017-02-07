# -*- coding: utf-8 -*-
from PyQt4 import QtGui

import sys
import ui_chat
    
class MainDialog(QtGui.QMainWindow, ui_chat.Ui_MainWindow):         
    # setup the imported UI
    def __init__(self, parent=None):
        super(MainDialog, self).__init__(parent)
        self.setupUi(self)

        # connecting SIGNALS and SOCKETS
        self.pushButton.clicked.connect(self.on_send_clicked)

    # slot
    # get the current text on the screen first and then
    # append the desired message to it
    def on_send_clicked(self):
        text = self.textBrowser.toPlainText()   # inherited from TextArea
        current_text = self.lineEdit.text()
        
        # only append if message is not empty
        if(current_text != ""):
            text += current_text
            self.textBrowser.setText(text + "\n")
            
            # keep the scroll bar locked to the bottom
            self.textBrowser.verticalScrollBar()    \
                .setValue(self.textBrowser.verticalScrollBar().maximum())
        
# main method
if __name__ == "__main__":
    app = QtGui.QApplication(sys.argv)
    form = MainDialog()
    form.show()
    app.exec_()
