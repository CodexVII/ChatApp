# -*- coding: utf-8 -*-
from PyQt4 import Qt, QtGui, QtCore, QtNetwork
from random import randint
from time import strftime, gmtime
from emoji import emojize

import sys
import ui_chat, ui_connect, ui_about
import ctypes
import hashlib


class Config:
    DownloadDir = QtCore.QDir.homePath() + "\\Desktop\\"
    Port_t, Message_t, FileData_t, FileName_t = range(4)  # Message types


# Inherit QObject to use signals
class Communication(QtCore.QThread):
    HEADER_SIZE = 6  # 4 bytes for payload size, 2 bytes for payload type
    CONNECTED = False  # used to prevent infinite pairing loop

    # SIGNALS
    messageReceived = QtCore.pyqtSignal()
    fileReceived = QtCore.pyqtSignal(str, int, str)
    listenError = QtCore.pyqtSignal()
    pairStateChanged = QtCore.pyqtSignal(int)
    pairSuccess = QtCore.pyqtSignal()
    pairFailed = QtCore.pyqtSignal()
    serverReady = QtCore.pyqtSignal(int)

    def __init__(self):
        super(Communication, self).__init__()

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

    def run(self):
        # connecting SIGNALS and SLOTS
        self.tcpSocket_request.connected.connect(self.on_connection_accepted)
        self.tcpSocket_request.error.connect(self.on_connection_failed)
        self.tcpSocket_request.stateChanged.connect(self.on_connection_state_changed)
        self.tcpServer.newConnection.connect(self.incomingClient)

        self.startTcpServer()
        QtCore.QThread.exec_(self)

    def on_connection_state_changed(self, state):
        print "Socket state is now: " + str(self.tcpSocket_request.state())
        self.pairStateChanged.emit(state)

    def on_connection_failed(self):
        self.CONNECTED = False
        self.pairFailed.emit()

    # move to its own function so that this won't be running on the main thread
    def startTcpServer(self):
        # begin listening at a random port
        if not self.tcpServer.listen(QtNetwork.QHostAddress("localhost"), randint(5000, 65535)):
            # server couldn't start
            self.listenPortLive = False
            self.listenError.emit()
        else:
            # server started successfully
            self.listenPortLive = True
            self.serverReady.emit(self.tcpServer.serverPort())

    def incomingClient(self):
        # assign the incoming connection to a socket and connect that socket's
        # readyRead signal to read the message
        self.tcpSocket_receive = self.tcpServer.nextPendingConnection()
        self.tcpSocket_receive.readyRead.connect(self.read)

    # write routine which doesn't care about what it's writing or who it's writing to
    def write(self, payload_t, payload):
        print "Writing from thread: " + str(int(QtCore.QThread.currentThreadId()))
        # will contain the message
        block = QtCore.QByteArray()

        # inform that this message is to show the listening port
        # prepare the output stream
        out = QtCore.QDataStream(block, QtCore.QIODevice.WriteOnly)
        out.setVersion(QtCore.QDataStream.Qt_4_0)
        out.writeUInt32(0)  # placeholder for payload size
        out.writeUInt16(payload_t)  # payload_t is int, constructor only takes str

        # print "past header"
        # determine which procedure to use when writing to the datastream
        if payload_t == Config.Port_t or payload_t == Config.Message_t or payload_t == Config.FileName_t:
            # payload is a string
            out.writeString(payload)
        elif payload_t == Config.FileData_t:
            # payload is a byte array
            out.writeRawData(payload)

        # print "data on datastream"
        # go back to the start and write the size of the payload
        out.device().seek(0)
        out.writeUInt32(block.size() - self.HEADER_SIZE)

        self.tcpSocket_request.write(block)

    # returns QDataStream object for processing
    def read(self):
        print "Reading from thread: " + str(int(QtCore.QThread.currentThreadId()))
        # Constructs a data stream that uses the I/O device d.
        instr = QtCore.QDataStream(self.tcpSocket_receive)
        instr.setVersion(QtCore.QDataStream.Qt_4_0)

        # if we haven't read anything yet from the server and size is not set
        if self.blockSize == 0:
            # the first two bytes are reserved for the size of the payload.
            # must check it is at least that size to take in a valid payload size.
            if self.tcpSocket_receive.bytesAvailable() < self.HEADER_SIZE:
                print "smaller than header"
                return

            # read the size of the byte array payload from server.
            # Once the first flag is consumed, read the message type on the payload
            print "getting new payload info"

            self.blockSize = instr.readUInt32()
            self.msgType = instr.readUInt16()
            print "Msg type: " + str(self.msgType)
        # the data is incomplete so we return until the data is good
        if self.tcpSocket_receive.bytesAvailable() < self.blockSize:
            print "message incomplete"
            return

        # sort out what to do with the received data
        # if self.tcpSocket_receive.bytesAvailable() == self.blockSize:
        # go back to the start of the payload
        if self.msgType == Config.Port_t:
            # message contains port information
            # save the port to set the request socket to point at that port
            # sometimes required.. ie. over local network this seemed to become an issue.. fine local
            self.pairPort = instr.readString()
            # self.pairPort = payload
            self.pair(self.tcpSocket_receive.peerAddress(), int(self.pairPort))

        elif self.msgType == Config.Message_t:
            # normal message
            # read in the message and inform connected objects about the contents
            self.msg = instr.readString()
            self.messageReceived.emit()
        elif self.msgType == Config.FileData_t:
            self.rawFile = instr.readRawData(self.blockSize)

            # downloads go to the user's desktop folder. will emit a signal when finished
            file = QtCore.QFile(Config.DownloadDir + self.fileName)
            file.open(QtCore.QIODevice.WriteOnly)
            file.write(self.rawFile)
            file.close()

            fileSize = QtCore.QFileInfo(file).size() / 1000
            fileHash = hashlib.sha256(self.rawFile).hexdigest()
            self.fileReceived.emit(self.fileName, fileSize, fileHash)

        elif self.msgType == Config.FileName_t:
            # store the file name. used when saving the received file that should come straight after this
            self.fileName = instr.readString()
            print "received file name: " + str(self.fileName)

        # reset the block size for next msg to be read
        self.blockSize = 0
        self.msgType = -1

        # recursive call to check if there is data still to be read.
        self.read()

    def pair(self, host, port):
        # allows for connection between two chatting programmes
        # possibly the place where AES, SHA and RSA will take place
        print "pairing from thread: " + str(int(QtCore.QThread.currentThreadId()))
        if not self.CONNECTED:
            self.tcpSocket_request.connectToHost(host, int(port))

    def on_connection_accepted(self):
        print "connection accepted in thread: " + str(int(QtCore.QThread.currentThreadId()))
        self.CONNECTED = True

        # pairing done, let connected objects know
        self.pairSuccess.emit()

        # attempt to connect to the listening port of the other user
        self.write(Config.Port_t, str(self.tcpServer.serverPort()))


class AboutDialog(QtGui.QDialog, ui_about.Ui_Dialog):
    def __init__(self, parent):
        super(AboutDialog, self).__init__(parent)
        self.setupUi(self)

        # keep focus fixed to this window
        self.setModal(True)

        # prevent resizing
        self.setFixedSize(451, 213)


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


class FileIOThread(QtCore.QThread):
    readComplete = QtCore.pyqtSignal(QtCore.QByteArray, str, int, str)
    error = QtCore.pyqtSignal()

    def __init__(self):
        QtCore.QThread.__init__(self)

    def run(self):
        # run within its own event loop
        QtCore.QThread.exec_(self)

    def readFile(self, path):
        print "Reading file"
        attachedFile = QtCore.QFile(path)

        # check that the file opens successfully
        if not attachedFile.open(QtCore.QIODevice.ReadOnly):
            return False

        # get file info
        fileInfo = QtCore.QFileInfo(attachedFile.fileName())

        # read the file and prepare for sending
        rawFile = attachedFile.readAll()

        fileName = fileInfo.fileName()
        fileSize = fileInfo.size() / 1000
        fileHash = hashlib.sha256(rawFile).hexdigest()

        self.readComplete.emit(rawFile, fileName, fileSize, fileHash)

    def writeToFile(self, data):
        pass

    # return byte array
    def bytesToFile(self, data, path):
        # open file with given path (which includes file name)
        file = QtCore.QFile(path)
        file.open(QtCore.QIODevice.WriteOnly)

        file.write(data)
        file.close()

        self.readComplete.emit()


# middle man between the GUI class and TCP communication
class Logic(QtCore.QObject):
    # messaging signals
    outgoingMessageReady = QtCore.pyqtSignal(int, QtCore.QString)
    messageReceived = QtCore.pyqtSignal(str)

    # pairing/connectiong signals
    pairRequest = QtCore.pyqtSignal(str, str)
    forwardServerPort = QtCore.pyqtSignal(int)
    forwardConnectionStatus = QtCore.pyqtSignal(str)
    pairSocketStateChanged = QtCore.pyqtSignal(str)

    # file signals
    fileAttached = QtCore.pyqtSignal()
    forwardFileDetails = QtCore.pyqtSignal(str, int, str)
    fileReadyForWrite = QtCore.pyqtSignal(int, QtCore.QByteArray)
    readAttachedFile = QtCore.pyqtSignal(str)
    fileRead = QtCore.pyqtSignal()

    def __init__(self):
        QtCore.QObject.__init__(self)

        # handles all communication logic
        self.comm = Communication()

        # sending data
        self.rawFile = None
        self.fileName = ""
        self.fileSize = 0
        self.fileHash = None

        # flg to check if a file is attached to the message
        self.fileAttached = False

        # connect comm signal/slots
        self.comm.messageReceived.connect(self.forwardReceivedMessage)
        self.comm.pairStateChanged.connect(self.on_pair_state_changed)
        self.comm.listenError.connect(lambda: self.displayListenStaus(self.comm.listenPortLive))
        self.comm.fileReceived.connect(self.on_fileReceived)
        self.comm.serverReady.connect(self.on_serverReady)

        self.commThread = QtCore.QThread()
        self.comm.moveToThread(self.commThread)

        self.outgoingMessageReady.connect(self.comm.write)
        self.fileReadyForWrite.connect(self.comm.write)
        self.pairRequest.connect(self.comm.pair)

        self.commThread.started.connect(self.comm.run)
        self.commThread.start()

        # file IO stuff
        self.fileIO = FileIOThread()
        self.fileIO.readComplete.connect(self.on_fileRead)

        self.fileIOThread = QtCore.QThread()
        self.fileIO.moveToThread(self.fileIOThread)

        self.readAttachedFile.connect(self.fileIO.readFile)
        self.fileIOThread.started.connect(self.fileIO.run)
        self.fileIOThread.start()

    def on_pair_state_changed(self, state):
        if state == 0:
            self.pairSocketStateChanged.emit("Disconnected")
        elif state == 1:
            self.pairSocketStateChanged.emit("Looking up host name..")
        elif state == 2:
            self.pairSocketStateChanged.emit("Connecting..")
        elif state == 3:
            self.pairSocketStateChanged.emit("Connected")
        elif state == 6:
            self.pairSocketStateChanged.emit("Disconnecting..")

    def on_fileReceived(self, name, size, hash):
        print "received file"
        self.forwardFileDetails.emit(name, size, hash)

    def on_fileRead(self, data, name, size, hash):
        print "Got to on_fileReady"
        # get the data
        self.rawFile = data

        # extract name, size and hash
        self.fileName = name
        self.fileSize = size
        self.fileHash = hash

        self.fileRead.emit()

    def sendFile(self):
        # inform the user about the incoming file
        self.outgoingMessageReady.emit(Config.Message_t, "Sending file with hash: " + self.fileHash)

        # first send the file name
        self.outgoingMessageReady.emit(Config.FileName_t, self.fileName)

        # send out the file and reset the file attached flag
        self.fileReadyForWrite.emit(Config.FileData_t, self.rawFile)

        # file has been sent. do tear down to prepare for next file
        self.fileAttached = False

    def attachFile(self, path):
        # if the path isn't empty, set the file flag to true and prep the file for transfer
        if path:
            print "File Attached"
            self.fileAttached = True

            self.readAttachedFile.emit(path)

    def on_serverReady(self, port):
        self.forwardServerPort.emit(port)

    def forwardReceivedMessage(self):
        print "Forwarding message"
        self.messageReceived.emit(self.comm.msg)

    def on_messageReady(self, payload_t, payload):
        print "inside logic"
        self.outgoingMessageReady.emit(payload_t, payload)
        # self.comm.write(payload_t, payload)

    def beginPairing(self, address, port):
        print "pairing from logic"
        # ensure that each connection/reconnect is a fresh one
        self.comm.tcpSocket_request.abort()

        self.comm.CONNECTED = False

        # get the connection details from the connection dialog
        self.pairRequest.emit(address, port)
        # self.comm.pair(address, port)

    def sendMessage(self, msg):
        print "Sending msg from Logic" + str(int(QtCore.QThread.currentThreadId()))

        # check if the msg is empty
        if msg:
            self.outgoingMessageReady.emit(Config.Message_t, msg)

    def on_send_triggered(self):
        self.sendMessage()

        # check if there is a file attached before sending it out
        if self.fileAttached:
            self.sendFile()

    def displayConnectionStatus(self, status):
        print "Connected"

    def displayMessage(self, msg, sender):
        self.messageReceived.emit(msg, sender)
        print "got message: " + msg


# the MainWindow class should only be concerned about displying/updating information on the screen.
# it should not be concerned about how any of the logic works
# design is then a simple:
#   emit signal from UI event
#       emit signal containing event details for processing
#
#   slot event result
#       process result and give feedback in GUI
class MainWindow(QtGui.QMainWindow, ui_chat.Ui_MainWindow):
    messageReadyForWrite = QtCore.pyqtSignal(int, QtCore.QString)
    fileReadyForWrite = QtCore.pyqtSignal(int, QtCore.QByteArray)
    doBenchTest = QtCore.pyqtSignal()

    # actual signals
    connectInfoReady = QtCore.pyqtSignal(str, str)
    messageOut = QtCore.pyqtSignal(str)

    # setup the imported UI
    def __init__(self, parent=None):
        super(MainWindow, self).__init__(parent)

        # prevent resizing
        self.setFixedSize(652, 358)

        # build UI from the one generated from pyuic4
        self.setupUi(self)

        # Extra dialogs
        self.connectDialog = ConnectDialog(self)
        self.aboutDialog = AboutDialog(self)

        # pass over logic to this object through signals and slots
        self.logic = Logic()
        self.logic.messageReceived.connect(self.displayMessage)
        self.logic.forwardServerPort.connect(self.updateServerPort)
        self.logic.forwardFileDetails.connect(self.showFileInfoDialog)
        self.logic.pairSocketStateChanged.connect(self.displayConnectionStatus)
        self.logic.fileRead.connect(self.on_file_attached)

        # keep track of all sent messages
        self.history = []
        self.currMsgIndex = -1

        # connecting SIGNALS to SLOTS
        self.pushButton.clicked.connect(self.on_send_triggered)
        self.pushButton_2.clicked.connect(self.attachFile)
        self.lineEdit.returnPressed.connect(self.on_send_triggered)
        self.lineEdit.textChanged.connect(self.on_message_update)
        self.actionConnect.triggered.connect(self.on_connect_triggered)
        self.actionAbout.triggered.connect(self.on_about_triggered)
        self.connectDialog.inputReady.connect(self.on_connect_info_ready)

        # user hasn't placed any input yet so disable the button
        self.pushButton.setDisabled(True)

        # set font for text box
        QtGui.QFontDatabase().addApplicationFont("OpenSansEmoji.ttf")
        self.textBrowser.setStyleSheet("""
               .QTextBrowser {
                   font-family: "OpenSansEmoji";
                   font-size: 14px;
                   }
               """)

        self.lineEdit.setStyleSheet("""
               .QLineEdit {
                   font-family: "OpenSansEmoji";
                   font-size: 14px;
                   }
               """)

        print "Main GUI initialised with ID: " + str(int(QtCore.QThread.currentThreadId()))

    def updateServerPort(self, port):
        # update the port number in GUI with listening port
        self.lineEdit_5.setText(str(self.logic.comm.tcpServer.serverPort()))

    def on_connect_info_ready(self):
        address = self.connectDialog.lineEdit.text()
        port = self.connectDialog.lineEdit_2.text()

        self.logic.beginPairing(address, port)

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

    def on_send_triggered(self):
        self.on_send_trigger()

        # check if there is a file attached before sending it out
        if self.logic.fileAttached:
            self.sendFile()

    # send out a message to the server whenever the user hits
    # the 'send' button. It will take in whatever is on the
    # LineEdit box and write it into    a socket
    def on_send_trigger(self):
        msg = self.lineEdit.text()
        if msg:
            self.displayMessage(msg, sender=True)
            self.lineEdit.clear()
            self.logic.sendMessage(msg)
            self.recordMessage(msg)

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

    def sendFile(self):
        # inform the user that they are sending a file before actually sending it
        self.textBrowser_2.clear()
        self.logic.sendFile()

    def displayMessage(self, msg, sender=False):
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
        print "Attaching file"
        path = QtGui.QFileDialog.getOpenFileName(self, 'Open file',
                                                 'c:\\', "Any (*)")

        self.logic.attachFile(path)

    def on_file_attached(self):
        # small info feedback to user
        self.textBrowser_2.setText("Attached: " + self.logic.fileName)
        self.textBrowser_2.setToolTip("Attached: " + self.logic.fileName)

    def displayConnectionStatus(self, status):
        print "Connection state: " + str(status)
        self.statusBar.showMessage(status)

    def displayListenStatus(self, status):
        if status is 1:
            self.statusBar.showMessage("Unable to start listening port")

    # quick dialog box to inform user about the attached file
    # could also let user know about any errors with file attachment
    def showFileInfoDialog(self, fileName, fileSize, hash, sender=False):
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

    # setting app icon
    app.setWindowIcon(QtGui.QIcon('D.png'))
    appId = u'dollars.chat.app'
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(appId)

    chat = MainWindow()
    chat.show()
    exit(app.exec_())
