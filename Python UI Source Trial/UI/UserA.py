# -*- coding: utf-8 -*-
from PyQt4 import QtGui, QtCore, QtNetwork
from random import randint
from time import strftime, gmtime

import sys
import ui_chat
import ui_connect
import ctypes


# Inherit QObject to use signals
class Communication(QtCore.QObject):
    HEADER_SIZE = 3  # in bytes
    CONNECTED = 1  # 1=connected, 0=not connected

    # SIGNALS
    messageReady = QtCore.pyqtSignal()
    listenError = QtCore.pyqtSignal()
    pairComplete = QtCore.pyqtSignal()

    def __init__(self, parent):
        super(Communication, self).__init__(parent)
        # IO variables
        self.blockSize = 0
        self.msgType = 0
        self.pairPort = 0

        # Variables to be passed by signals
        self.msg = None
        self.listenStatus = None
        self.pairStatus = None

        # One TcpSocket is for the server portion of the program (_receive)
        # the other is for the client portion of the program (_request)
        self.tcpSocket_receive = QtNetwork.QTcpSocket(self)
        self.tcpSocket_request = QtNetwork.QTcpSocket(self)
        self.tcpServer = QtNetwork.QTcpServer(self)

        # begin listening at a random port
        if not self.tcpServer.listen(QtNetwork.QHostAddress("localhost"), randint(5000, 65535)):
            # server couldn't start
            self.listenStatus = 1
            self.listenError.emit()

        # connecting SIGNALS and SLOTS
        self.tcpServer.newConnection.connect(self.incomingClient)

    def incomingClient(self):
        # assign the incoming connection to a socket and connect that socket's
        # readyRead signal to read the message
        self.tcpSocket_receive = self.tcpServer.nextPendingConnection()
        self.tcpSocket_receive.readyRead.connect(self.read)

    # write routine which doesn't care about what it's writing or who it's writing to
    def write(self, payload_t, payload):
        # will contain the message
        block = QtCore.QByteArray()

        # inform that this message is to show the listening port
        # prepare the output stream
        out = QtCore.QDataStream(block, QtCore.QIODevice.WriteOnly)
        out.setVersion(QtCore.QDataStream.Qt_4_0)
        out.writeUInt16(0)
        out.writeUInt8(payload_t)

        # write the server port into the message
        out.writeQString(str(payload))
        out.device().seek(0)
        out.writeUInt16(block.size() - self.HEADER_SIZE)

        # write out the message to the socket which is linked to the client
        self.tcpSocket_request.write(block)

    # returns QDataStream object for processing
    def read(self):
        # Constructs a data stream that uses the I/O device d.
        instr = QtCore.QDataStream(self.tcpSocket_receive)
        instr.setVersion(QtCore.QDataStream.Qt_4_0)

        # if we haven't read anything yet from the server and size is not set
        if self.blockSize == 0:
            # the first two bytes are reserved for the size of the payload.
            # must check it is at least that size to take in a valid payload size.
            if self.tcpSocket_receive.bytesAvailable() < self.HEADER_SIZE:
                return

            # read the size of the byte array payload from server.
            # Once the first flag is consumed, read the message type on the payload
            self.blockSize = instr.readUInt16()
            self.msgType = instr.readUInt8()

        # the data is incomplete so we return until the data is good
        if self.tcpSocket_receive.bytesAvailable() < self.blockSize:
            return

        # sort out what to do with the received data
        self.processReceivedMessage(instr)

    # process the message depending on its type
    def processReceivedMessage(self, instr):
        # normal message
        if self.msgType is "1":
            # read in the message and inform connected objects about the contents
            self.msg = instr.readQString()
            self.messageReady.emit()

        # message contains port information
        elif self.msgType is "2":
            # save the port to set the request socket to point at that port
            self.pairPort = instr.readQString()
            self.pair(QtCore.QString("localhost"), self.pairPort.toInt()[0])

        # reset the block size for next msg to be read
        self.blockSize = 0

    def pair(self, host, port):
        # allows for connection between two chatting programmes
        # possibly the place where AES, SHA and RSA will take place
        if self.CONNECTED == 1:
            self.tcpSocket_request.connectToHost(host, port)
            if self.tcpSocket_request.waitForConnected():
                # connection succeeded
                self.pairStatus = 0
                self.CONNECTED = 0
            else:
                # connection failed
                self.pairStatus = 1

            # pairing done, let connected objects know
            self.pairComplete.emit()

            # alert the paired socket about the listening port by sending a message
            self.write("2", str(self.tcpServer.serverPort()))


class ConnectDialog(QtGui.QDialog, ui_connect.Ui_Dialog):
    # SIGNALS
    inputReady = QtCore.pyqtSignal()

    def __init__(self, parent):
        super(ConnectDialog, self).__init__(parent)
        self.setupUi(self)

        # default values for connection
        self.lineEdit.setText("localhost")

        # connect SIGNALS to SLOTS
        self.lineEdit.textChanged.connect(self.on_input_changed)
        self.lineEdit_2.textChanged.connect(self.on_input_changed)
        self.lineEdit.returnPressed.connect(self.on_connect_clicked)
        self.lineEdit_2.returnPressed.connect(self.on_connect_clicked)
        self.pushButton.clicked.connect(self.on_connect_clicked)

        self.pushButton.setDisabled(True)

    def on_input_changed(self):
        # disable the button if input is not valid
        if self.isValidInput():
            self.pushButton.setEnabled(True)
        else:
            self.pushButton.setDisabled(True)

    def on_connect_clicked(self):
        # inform other objects that the user has completed the form
        # close the form once done.
        if self.isValidInput():
            self.inputReady.emit()
            self.close()

    # can be made more rigorous if felt needed
    def isValidInput(self):
        # check if either of the inputs are empty
        if self.lineEdit.text() and self.lineEdit_2.text():
            return True
        else:
            return False


class MainWindow(QtGui.QMainWindow, ui_chat.Ui_MainWindow):
    # setup the imported UI
    def __init__(self, parent=None):
        super(MainWindow, self).__init__(parent)

        # create a dialog which will become a popup
        self.connectDialog = ConnectDialog(self)

        # handles all communication logic
        self.comm = Communication(self)

        # build UI from the one generated from pyuic4
        self.setupUi(self)

        # update the port number in GUI with listening port
        self.lineEdit_5.setText(str(self.comm.tcpServer.serverPort()))

        # connecting SIGNALS to SLOTS
        self.pushButton.clicked.connect(self.sendMessage)
        self.lineEdit.returnPressed.connect(self.sendMessage)
        self.lineEdit.textChanged.connect(self.on_message_update)
        self.actionConnect.triggered.connect(self.on_connect_triggered)
        self.connectDialog.inputReady.connect(self.on_connect_info_ready)
        self.comm.messageReady.connect(lambda: self.displayMessage(self.comm.msg))
        self.comm.pairComplete.connect(lambda: self.displayConnectionStatus(self.comm.pairStatus))
        self.comm.listenError.connect(lambda: self.displayListenStaus(self.comm.listenStatus))

        # user hasn't placed any input yet so disable the button
        self.pushButton.setDisabled(True)

    def on_message_update(self):
        # only allow the button to be pressed if there is user input
        if not str(self.lineEdit.text()):
            self.pushButton.setDisabled(True)
        else:
            self.pushButton.setEnabled(True)

    def on_connect_triggered(self):
        # pop up the connection dialog
        self.connectDialog.show()

    def on_connect_info_ready(self):
        # ensure that each connection/reconnect is a fresh one
        self.comm.tcpSocket_request.abort()
        self.comm.CONNECTED = 1

        # get the connection details from the connection dialog
        self.comm.pair(self.connectDialog.lineEdit.text(), int(self.connectDialog.lineEdit_2.text()))

    # send out a message to the server whenever the user hits
    # the 'send' button. It will take in whatever is on the
    # LineEdit box and write it into a socket
    def sendMessage(self):
        msg = str(self.lineEdit.text())

        # check if the msg is empty
        if msg:
            # append current user message to textBrowser and  clear the user input box
            timestamp = strftime("%H:%M", gmtime())
            self.textBrowser.append("[" + str(timestamp) + "] " + "You>> " + msg)
            self.lineEdit.clear()

            # write out the message to the client
            self.comm.write("1", msg)

    def displayMessage(self, msg):
        timestamp = strftime("%H:%M", gmtime())
        self.textBrowser.append("[" + str(timestamp) + "] " + "Anonymous>> " + msg)

    def displayConnectionStatus(self, status):
        if status is 0:
            self.statusBar.showMessage("Connected")
        else:
            self.statusBar.showMessage("Failed to connect")

    def displayListenStaus(self, status):
        if status is 1:
            self.statusBar.showMessage("Unable to start listening port")


if __name__ == "__main__":
    app = QtGui.QApplication(sys.argv)

    # setting app icon
    app.setWindowIcon(QtGui.QIcon('D.png'))
    myappid = u'dollars.chat.app'  # arbitrary string
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)

    chat = MainWindow()
    chat.show()
    app.exec_()
