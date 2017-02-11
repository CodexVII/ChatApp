# -*- coding: utf-8 -*-
from PyQt4 import QtGui, QtCore, QtNetwork
from random import randint
from time import strftime, gmtime
from emoji import emojize

import sys
import ui_chat, ui_connect, ui_about
import ctypes
import hashlib


# Inherit QObject to use signals
class Communication(QtCore.QObject):
    Port_t, Message_t, FileData_t, FileName_t = range(4)  # Message types
    HEADER_SIZE = 6  # 4 bytes for payload size, 2 bytes for payload type
    CONNECTED = False  # used to prevent infinite pairing loop

    # SIGNALS
    messageReceived = QtCore.pyqtSignal()
    fileReceived = QtCore.pyqtSignal()
    listenError = QtCore.pyqtSignal()
    pairComplete = QtCore.pyqtSignal()

    def __init__(self, parent):
        super(Communication, self).__init__(parent)
        # IO variables
        self.blockSize = 0
        self.msgType = -1
        self.pairPort = -1

        # Variables to be passed by signals
        self.msg = None
        self.fileHash = ""
        self.fileName = ""
        self.fileSize = 0
        self.rawFile = None
        self.listenPortLive = False

        # One TcpSocket is for the server portion of the program (_receive)
        # the other is for the client portion of the program (_request)
        self.tcpSocket_receive = QtNetwork.QTcpSocket(self)
        self.tcpSocket_request = QtNetwork.QTcpSocket(self)
        self.tcpServer = QtNetwork.QTcpServer(self)

        # begin listening at a random port
        if not self.tcpServer.listen(QtNetwork.QHostAddress("localhost"), randint(5000, 65535)):
            # server couldn't start
            self.listenPortLive = False
            self.listenError.emit()
        else:
            # server started successfully
            self.listenPortLive = True

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
        out.writeUInt32(0)  # placeholder for payload size
        out.writeUInt16(payload_t)  # payload_t is int, constructor only takes str

        # determine which procedure to use when writing to the datastream
        if payload_t == self.Port_t or payload_t == self.Message_t or payload_t == self.FileName_t:
            # payload is a string
            out.writeString(payload)
        elif payload_t == self.FileData_t:
            # payload is a byte array
            out.writeRawData(payload)

        # go back to the start and write the size of the payload
        out.device().seek(0)
        out.writeUInt32(block.size() - self.HEADER_SIZE)

        # write out the message to the socket which is linked to the client
        self.tcpSocket_request.write(block)

        # wait until this has finished writing
        if not self.tcpSocket_request.waitForBytesWritten():
            print "Failed to write in time"

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
            self.blockSize = instr.readUInt32()
            self.msgType = instr.readUInt16()

        # the data is incomplete so we return until the data is good
        if self.tcpSocket_receive.bytesAvailable() < self.blockSize:
            # print "Bytes available: " + str(self.tcpSocket_receive.bytesAvailable())
            # print "Block size: " + str(self.blockSize)
            return

        print "msg ready"
        print "Bytes available: " + str(self.tcpSocket_receive.bytesAvailable())
        print "Block size: " + str(self.blockSize)
        print "Message type: " + str(self.msgType)




        # sort out what to do with the received data
        # if self.tcpSocket_receive.bytesAvailable() == self.blockSize:
        # go back to the start of the payload
        # fixes a big issue with sending a message, followed by another type which would then kill the communication
        # due to a mismatch between block size and byte size available
        # instr.device().reset()
        if self.msgType == self.Port_t:
            # message contains port information
            # save the port to set the request socket to point at that port
            # sometimes required.. ie. over local network this seemed to become an issue.. fine local
            self.pairPort = instr.readString()
            self.pair(self.tcpSocket_receive.peerAddress(), int(self.pairPort))

            # pairing done, let connected objects know
            self.pairComplete.emit()
        elif self.msgType == self.Message_t:
            # normal message
            # read in the message and inform connected objects about the contents

            self.msg = instr.readString()
            self.messageReceived.emit()
        elif self.msgType == self.FileData_t:
            # payload contains file
            self.rawFile = instr.readRawData(self.blockSize)
            file = QtCore.QFile("C:/Users/keita/Desktop/" + self.fileName)
            file.open(QtCore.QIODevice.WriteOnly)
            file.write(self.rawFile)
            file.close()

            # self.qFile = QtCore.QFile(rawFile)
            # get file data
            self.fileHash = hashlib.sha256(self.rawFile).hexdigest()
            self.fileSize = QtCore.QFileInfo(file).size() / 1000
            print "read file data"
            self.fileReceived.emit()
        elif self.msgType == self.FileName_t:
            # store the file name. used when saving the received file that should come straight after this
            self.fileName = instr.readString()
            print "received file name: " + str(self.fileName)
        # else:
        #     print "block size did not match."

        # reset the block size for next msg to be read
        self.blockSize = 0
        self.msgType = -1

    def pair(self, host, port):
        # allows for connection between two chatting programmes
        # possibly the place where AES, SHA and RSA will take place
        if not self.CONNECTED:
            self.tcpSocket_request.connectToHost(host, int(port))
            if self.tcpSocket_request.waitForConnected():
                # connection succeeded
                self.CONNECTED = True
            else:
                # connection failed
                self.CONNECTED = False

            # alert the paired socket about the listening port by sending a message
            self.write(self.Port_t, str(self.tcpServer.serverPort()))


class AboutDialog(QtGui.QDialog, ui_about.Ui_Dialog):
    def __init__(self, parent):
        super(AboutDialog, self).__init__(parent)
        self.setupUi(self)

        # keep focus fixed to this window
        self.setModal(True)

        # prevent resizing
        self.setFixedSize(437, 188)


class ConnectDialog(QtGui.QDialog, ui_connect.Ui_Dialog):
    # SIGNALS
    inputReady = QtCore.pyqtSignal()

    def __init__(self, parent):
        super(ConnectDialog, self).__init__(parent)
        self.setupUi(self)

        # keep focus fixed to this window
        self.setModal(True)

        # prevent resizing
        self.setFixedSize(254, 96)

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

        # prevent resizing
        self.setFixedSize(550, 286)

        # build UI from the one generated from pyuic4
        self.setupUi(self)

        # Extra dialogs
        self.connectDialog = ConnectDialog(self)
        self.aboutDialog = AboutDialog(self)

        # handles all communication logic
        self.comm = Communication(self)

        # update the port number in GUI with listening port
        self.lineEdit_5.setText(str(self.comm.tcpServer.serverPort()))

        # keep track of all sent messages
        self.history = []
        self.currMsgIndex = -1

        # sending data
        self.msg = None
        self.rawFile = None
        self.fileName = ""
        self.fileSize = 0
        self.fileHash = None

        # flg to check if a file is attached to the message
        self.fileAttached = False

        # connecting SIGNALS to SLOTS
        self.pushButton.clicked.connect(self.on_send_triggered)
        self.pushButton_2.clicked.connect(self.attachFile)
        self.lineEdit.returnPressed.connect(self.on_send_triggered)
        self.lineEdit.textChanged.connect(self.on_message_update)
        self.actionConnect.triggered.connect(self.on_connect_triggered)
        self.actionAbout.triggered.connect(self.on_about_triggered)
        self.connectDialog.inputReady.connect(self.on_connect_info_ready)
        self.comm.messageReceived.connect(lambda: self.displayMessage(self.comm.msg, sender=False))
        self.comm.pairComplete.connect(lambda: self.displayConnectionStatus(self.comm.CONNECTED))
        self.comm.listenError.connect(lambda: self.displayListenStaus(self.comm.listenPortLive))
        self.comm.fileReceived.connect(
            lambda: self.showFileInfoDialog(self.comm.fileName, self.comm.fileSize, self.comm.fileHash, sender=False))
        self.comm.fileReceived.connect(
            lambda: self.displayMessage("Received file with hash: " + str(self.comm.fileHash), sender=False))
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

    def on_about_triggered(self):
        self.aboutDialog.show()

    def on_connect_info_ready(self):
        # ensure that each connection/reconnect is a fresh one
        self.comm.tcpSocket_request.abort()
        self.comm.CONNECTED = False

        # get the connection details from the connection dialog
        self.comm.pair(self.connectDialog.lineEdit.text(), self.connectDialog.lineEdit_2.text())

    def on_send_triggered(self):
        self.sendMessage()

        # check if there is a file attached before sending it out
        if self.fileAttached:
            self.sendFile()

    def keyPressEvent(self, event):
        # get current key
        key = event.key()

        # new messages will be at the very end of the list so we work backwards when retrieving old messages
        if key == QtCore.Qt.Key_Up:
            # check that we won't go below 0 once we decrement
            if self.currMsgIndex > 0:
                self.currMsgIndex -= 1
                self.lineEdit.setText(self.history[self.currMsgIndex])  # get previous message
        elif key == QtCore.Qt.Key_Down:
            # check that we are not trying to access a message outside the bounds of the list
            if self.currMsgIndex < len(self.history) - 1:
                self.currMsgIndex += 1
                self.lineEdit.setText(self.history[self.currMsgIndex])

    # send out a message to the server whenever the user hits
    # the 'send' button. It will take in whatever is on the
    # LineEdit box and write it into    a socket
    def sendMessage(self):
        self.msg = self.lineEdit.text()

        # check if the msg is empty
        if self.msg:
            # append current user message to textBrowser and  clear the user input box
            self.displayMessage(self.msg, sender=True)
            self.lineEdit.clear()

            # write out the message to the client
            self.comm.write(self.comm.Message_t, self.msg)

            # add message to history
            self.recordMessage(self.msg)

    def sendFile(self):
        # show the
        self.displayMessage("Sending file with hash: " + self.fileHash, sender=True)

        # first send the file name
        print self.fileName
        self.comm.write(self.comm.FileName_t, self.fileName)
        # send out the file and reset the file attached flag
        self.comm.write(self.comm.FileData_t, self.rawFile)

        # self.lineEdit.setText("Sending file with hash: " + self.fileHash)

        # file has been sent. do tear down to prepare for next file
        self.fileAttached = False
        self.rawFile = None
        self.fileName = ""
        self.fileSize = 0

    def displayMessage(self, msg, sender):
        timestamp = strftime("%H:%M", gmtime())
        if sender:
            self.textBrowser.append("[" + str(timestamp) + "] " + "You>> " + emojize(str(msg), use_aliases=True))
        else:
            self.textBrowser.append("[" + str(timestamp) + "] " + "Anonymous>> " + emojize(str(msg), use_aliases=True))

    def recordMessage(self, msg):
        # store message into history
        self.history.append(msg)
        self.currMsgIndex = len(self.history) - 1
        self.currMsgIndex += 1

    def attachFile(self):
        # get the path to the desired file to be attached
        path = QtGui.QFileDialog.getOpenFileName(self, 'Open file',
                                                 'c:\\', "Any (*)")

        # if the path isn't empty, set the file flag to true and prep the file for transfer
        if path:
            print "File Attached"
            self.fileAttached = True

            # Create a QFile object based on the given path and store its name
            attachedFile = QtCore.QFile(path)

            # Open the file to read all of its contents in a byte array that's ready for sending
            if not attachedFile.open(QtCore.QIODevice.ReadOnly):
                print "Could not open file"

            # read the file and prepare for sending
            self.rawFile = attachedFile.readAll()

            # store the name
            fileInfo = QtCore.QFileInfo(attachedFile.fileName())
            self.fileName = fileInfo.fileName()
            self.fileSize = fileInfo.size() / 1000
            self.fileHash = hashlib.sha256(self.rawFile).hexdigest()

            # give feedback to user that file has been attached
            # self.showFileInfoDialog(self.fileName, self.fileSize, self.fileHash, sender=True)

    def displayConnectionStatus(self, connected):
        if connected:
            self.statusBar.showMessage("Connected")
        else:
            self.statusBar.showMessage("Failed to connect")

    def displayListenStaus(self, status):
        if status is 1:
            self.statusBar.showMessage("Unable to start listening port")

    # quick dialog box to inform user about the attached file
    # could also let user know about any errors with file attachment
    def showFileInfoDialog(self, fileName, fileSize, hash, sender):
        msg = QtGui.QMessageBox()
        msg.setIcon(QtGui.QMessageBox.Information)
        msg.setStandardButtons(QtGui.QMessageBox.Ok)
        msg.setModal(False)
        if sender:
            msg.setWindowTitle("File Attached")
            msg.setText("A file was successfully attached to the message")

        else:
            msg.setWindowTitle("Message Received.")
            msg.setText("A file was received")

        msg.setInformativeText("File Name: " + str(fileName) + "\n" +
                               "File Size: " + str(fileSize) + " kb" + "\n\n" +
                               "SHA-256: " + str(hash))
        msg.exec_()


if __name__ == "__main__":
    app = QtGui.QApplication(sys.argv)

    # using custom fonts
    QtGui.QFontDatabase().addApplicationFont("OpenSansEmoji.ttf")
    font = QtGui.QFont("OpenSansEmoji")
    font.setPointSize(10)
    app.setFont(font)

    # setting app icon
    app.setWindowIcon(QtGui.QIcon('D.png'))
    appId = u'dollars.chat.app'
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(appId)

    chat = MainWindow()
    chat.show()
    app.exec_()
