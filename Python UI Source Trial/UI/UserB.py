# -*- coding: utf-8 -*-
from PyQt4 import QtGui, QtCore, QtNetwork
from random import randint

import sys
import ui_chat
import ui_connect


class ConnectDialog(QtGui.QDialog, ui_connect.Ui_Dialog):
    inputReady = QtCore.pyqtSignal()

    def __init__(self, parent):
        super(ConnectDialog, self).__init__(parent)
        self.setupUi(self)

        self.lineEdit.setText("localhost")
        self.pushButton.clicked.connect(self.on_connect_clicked)

    def on_connect_clicked(self):
        self.inputReady.emit()
        self.close()


class MainWindow(QtGui.QMainWindow, ui_chat.Ui_MainWindow):
    HEADER_SIZE = 3  # in bytes
    CONNECTED = 0

    # setup the imported UI
    def __init__(self, parent=None):
        super(MainWindow, self).__init__(parent)

        # create a dialog which will become a popup
        self.connectDialog = ConnectDialog(self)

        # build UI from the one generated from pyuic4
        self.setupUi(self)

        # networking stuff
        self.blockSize = 0
        self.msgType = 0
        self.pairPort = 0

        # One TcpSocket is for the server portion of the program (_receive)
        # the other is for the client portion of the program (_request)
        self.tcpSocket_receive = QtNetwork.QTcpSocket(self)
        self.tcpSocket_request = QtNetwork.QTcpSocket(self)
        self.tcpServer = QtNetwork.QTcpServer(self)

        # begin listening at a random port
        if not self.tcpServer.listen(QtNetwork.QHostAddress("localhost"), randint(5000, 65535)):
            self.statusBar.showMessage("Unablet to start server")

        # update the port number in GUI with listening port
        self.lineEdit_5.setText(str(self.tcpServer.serverPort()))

        # connecting SIGNALS and SOCKETS
        self.pushButton.clicked.connect(self.on_send_clicked)
        self.actionConnect.triggered.connect(self.on_connect_triggered)
        self.connectDialog.inputReady.connect(self.on_connect_info_ready)
        self.tcpServer.newConnection.connect(self.incomingClient)

    def incomingClient(self):
        # assign the incoming connection to a socket and connect that socket's
        # readyRead signal to read the message
        self.tcpSocket_receive = self.tcpServer.nextPendingConnection()
        self.tcpSocket_receive.readyRead.connect(self.readMessage)

    def on_send_clicked(self):
        # append current user message to textBrowser
        self.textBrowser.append("You>> " + self.lineEdit.text())

        # call the routine which sends the message to the connected server
        self.sendMessage()

    def on_connect_triggered(self):
        # pop up the connection dialog
        self.connectDialog.show()

    def on_connect_info_ready(self):
        # ensure that each connection/reconnect is a fresh one
        self.tcpSocket_request.abort()

        # get the connection details from the connection dialog
        self.pair(self.connectDialog.lineEdit.text(), int(self.connectDialog.lineEdit_2.text()))

    def pair(self, host, port):
        # allows for connection between two chatting programmes
        # possibly the place where AES, SHA and RSA will take place
        if self.CONNECTED == 0:
            print "Request socket not setup... connecting for you"
            print "Target host: " + str(host)
            print "Target port: " + str(port)
            self.tcpSocket_request.connectToHost(host, port)
            if self.tcpSocket_request.waitForConnected():
                self.statusBar.showMessage("Connected")
                self.CONNECTED = 1
            else:
                self.statusBar.showMessage("Failed to connect")

            # will contain the message
            block = QtCore.QByteArray()

            # inform that this message is to show the listening port
            # prepare the output stream
            out = QtCore.QDataStream(block, QtCore.QIODevice.WriteOnly)
            out.setVersion(QtCore.QDataStream.Qt_4_0)
            out.writeUInt16(0)
            out.writeUInt8("2")

            # write the server port into the message
            out.writeQString(str(self.tcpServer.serverPort()))
            out.device().seek(0)
            out.writeUInt16(
                block.size() - self.HEADER_SIZE)  # Manages the threads required for sending out messages to clients.
            # write out the message to the socket which is linked to the client
            self.tcpSocket_request.write(block)

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
        out.writeUInt8("1")

        # write the message into the output stream
        out.writeQString(msg)
        out.device().seek(0)
        out.writeUInt16(
            block.size() - self.HEADER_SIZE)  # Manages the threads required for sending out messages to clients.

        # write out the message to the socket which is linked to the client
        self.tcpSocket_request.write(block)  # main method

        # clear the user input box
        self.lineEdit.setText('')

    def readMessage(self):
        # Constructs a data stream that uses the I/O device d.
        instr = QtCore.QDataStream(self.tcpSocket_receive)
        instr.setVersion(QtCore.QDataStream.Qt_4_0)

        # if we haven't read anything yet from the server and size is not set
        if self.blockSize == 0:
            # the first two bytes are reserved for the size of the payload.
            # must check it is at least that size to take in a valid payload size.
            if self.tcpSocket_receive.bytesAvailable() < self.HEADER_SIZE:
                return

            # read the size of the byte array payload from server
            self.blockSize = instr.readUInt16()

            # read the message type on the payload
            self.msgType = instr.readUInt8()

        # the data is incomplete so we return until the data is good
        if self.tcpSocket_receive.bytesAvailable() < self.blockSize:
            return

        # read the data from the datastream
        if self.msgType is "1":
            msg = instr.readQString()

            # append the received msg to the text browser
            self.textBrowser.append("Anonymous>>" + msg)

        elif self.msgType is "2":
            # save the port to set the request socket to point at that port
            self.pairPort = instr.readQString()
            self.pair(QtCore.QString("localhost"), self.pairPort.toInt()[0])

        self.blockSize = 0  # reset the block size for next msg to default


if __name__ == "__main__":
    app = QtGui.QApplication(sys.argv)
    form = MainWindow()
    form.show()
    app.exec_()
