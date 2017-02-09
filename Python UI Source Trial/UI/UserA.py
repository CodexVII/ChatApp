# -*- coding: utf-8 -*-
from PyQt4 import QtGui, QtCore, QtNetwork

import sys
import ui_chat
import ui_connect

class ConnectDialog(QtGui.QDialog, ui_connect.Ui_Dialog):
    inputReady = QtCore.pyqtSignal()

    def __init__(self, parent):
        super(ConnectDialog,self).__init__(parent)
        self.setupUi(self)

        self.pushButton.clicked.connect(self.on_connect_clicked)

    def on_connect_clicked(self):
        self.inputReady.emit()
        self.close()

class MainWindow(QtGui.QMainWindow, ui_chat.Ui_MainWindow):
    # setup the imported UI
    def __init__(self, parent=None):
        super(MainWindow, self).__init__(parent)

        # create a dialog which will become a popup
        self.connectDialog = ConnectDialog(self)

        # build UI from the one generated from pyuic4
        self.setupUi(self)

        # networking stuff
        self.tcpSocket = QtNetwork.QTcpSocket(self)

        # connecting SIGNALS and SOCKETS
        self.pushButton.clicked.connect(self.on_send_clicked)
        self.actionConnect.triggered.connect(self.on_connect_triggered)
        self.connectDialog.inputReady.connect(self.on_connect_info_ready)

    # slot
    # connectto host (if not already connected)
    # make the client object send the message to the recipient
    def on_send_clicked(self):
        # append current user message to textBrowser
        self.textBrowser.append(self.lineEdit.text())

        # call the routine which sends the message to the connected server
        self.sendMessage()

    def on_connect_triggered(self):
        # pop up the connection dialog
        self.connectDialog.show()

    def on_connect_info_ready(self):
        # check if socket is connected already
        print "TCPSocket not connected.. setting up connection for you"
        self.tcpSocket.connectToHost(self.connectDialog.lineEdit.text(), int(self.connectDialog.lineEdit_2.text()))

        if self.tcpSocket.waitForConnected():
            self.statusBar.showMessage("Connected")

        else:
            print "Failed to connect"

    # send out a message to the server whenever the user hits
    # the 'send' button. It will take in whatever is on the
    # LineEdit box and write it into a socket
    def sendMessage(self):
        # get msg from  the UI
        msg = self.lineEdit.text()

        # will contain the message
        block = QtCore.QByteArray()

        # prepare the output stream
        out = QtCore.QDataStream(block, QtCore.QIODevice.WriteOnly)
        out.setVersion(QtCore.QDataStream.Qt_4_0)
        out.writeUInt16(0)

        # write the message into the output stream
        out.writeQString(msg)
        out.device().seek(0)
        out.writeUInt16(block.size() - 2)  # Manages the threads required for sending out messages to clients.

        # write out the message to the socket which is linked to the client
        self.tcpSocket.write(block)  # main method

        # clear the user input box
        self.lineEdit.setText('')

if __name__ == "__main__":
    app = QtGui.QApplication(sys.argv)
    form = MainWindow()
    form.show()
    app.exec_()
