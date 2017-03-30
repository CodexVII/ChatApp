# -*- coding: utf-8 -*-
from PyQt4 import Qt, QtGui, QtCore, QtNetwork
from random import randint
from time import strftime, localtime
from emoji import emojize

from Crypto.PublicKey import RSA
from Crypto import Random
import ast  # ast = Abstract Syntax Trees - used for decrypting message

import sys
import ui_chat, ui_connect, ui_about, ui_demo
import ctypes
import hashlib
import aes
import socket
import security


########################################################################################################################
# ChatWindow
#
# DESCRIPTION:
# This is the initial window that pops up once the application is ran. It provides the user abilities to connect
# to other users and to send messages/files. Messages passed between users appear in the chat box while a text field is
# available for user input. Files may be attached to messages by clicking on the 'Attach' button. The server information
# can be found in the "User Info" box and is what other users use to connect to you.
#
# The UI was designed in Qt Designer and converted into valid .py files from XML. This made UI design much more straight
# forward as there was less focus in putting effort to coding the button placements/layouts.
#
# Once imported the file simply needed to be connected using the SIGNALS and SLOTS mechanisms which a core mechanic
# built into the Qt framework. User actions (signals) can be appropriately mapped into reactions in code (slots).
#
# The design is then a simple:
#   emit signal from UI event
#       process input in a slot within this class
#           call the logic class functions if necessary (for functional actions)
#
#   slot event result
#       process result in logic
#           give feedback in GUI
#
# SIGNALS:
#   -
#
# SLOTS:
#   def on_send_triggered()
#   def on_attach_clicked()
#   def on_messageDraft_changed()
#   def on_connect_clicked()
#   def on_about_clicked()
#   def on_quit_clicked()
#   def on_disconnect_clicked()
#   def on_connectInfo_ready()
#   def on_serverPort_ready(port)
#   def on_socketState_changed(status)
#   def on_file_attached()
#
# PUBLIC FUNCTIONS
#   def showFileInfo(fileName, fileSize, hash, sender)
#   def displayMessage(msg, sender)
#   def sendMessage()
#   def sendFile()
#   def keyPressEvent(event)
########################################################################################################################


class ChatWindow(QtGui.QMainWindow, ui_chat.Ui_MainWindow):
    # setup the imported UI
    def __init__(self, parent=None):
        super(ChatWindow, self).__init__(parent)

        # prevent resizing
        self.setFixedSize(652, 358)

        # build UI from the one generated from pyuic4
        self.setupUi(self)

        # Logic signals and slots
        self.logic = Logic()
        self.logic.messageReceived.connect(self.displayMessage)
        self.logic.forwardServerPort.connect(self.on_serverPort_ready)
        self.logic.forwardFileDetails.connect(self.showFileInfo)
        self.logic.forwardSocketState.connect(self.on_socketState_changed)
        self.logic.fileRead.connect(self.on_file_attached)
        self.logic.fileSent.connect(self.on_file_sent)
        self.logic.encryptedUpdate.connect(self.on_encryptedUpdate)
        self.logic.forwardPeerDetails.connect(self.on_peer_update)

        # keep track of all sent messages
        self.history = []
        self.currMsgIndex = -1

        # connect dialog
        self.connectDialog = ConnectDialog(self)
        self.aboutDialog = AboutDialog(self)
        self.demoDialog = DemoDialog(self)

        # UI signals to slots
        self.pushButton.clicked.connect(self.on_send_triggered)
        self.pushButton_2.clicked.connect(self.on_attach_clicked)
        self.lineEdit.returnPressed.connect(self.on_send_triggered)
        self.lineEdit.textChanged.connect(self.on_messageDraft_changed)
        self.actionConnect.triggered.connect(self.on_connect_clicked)
        self.actionAbout.triggered.connect(self.on_about_clicked)
        self.actionQuit.triggered.connect(self.on_quit_clicked)
        self.actionDisconnect.triggered.connect(self.on_disconnect_clicked)
        self.actionDemo.triggered.connect(self.on_demo_clicked)
        self.connectDialog.inputReady.connect(self.on_connectInfo_ready)
        self.radioButton.clicked.connect(self.on_encrypt_clicked)
        self.radioButton_2.clicked.connect(self.on_decrypt_clicked)
        self.pushButton_3.clicked.connect(self.on_quickConnect_clicked)
        # user hasn't placed any input yet so disable the button
        self.pushButton.setDisabled(True)
        self.pushButton_3.setDisabled(True)

        self.lineEdit_4.setText(socket.gethostbyname(socket.gethostname()))

        # connection vars
        self.address = ""
        self.port = ""

        # flags
        self.connectinInfoReady_f = False

        # set font for chat box and user input
        Qt.QFontDatabase.addApplicationFont("Segoe-UI-Emoji.ttf")
        self.textBrowser.setStyleSheet("""
               .QTextBrowser {
                   font-family: "Segoe UI Emoji";
                   font-size: 14px;
                   }
               """)
        self.lineEdit.setStyleSheet("""
               .QLineEdit {
                   font-size: 14px;
                   }
               """)

    def on_peer_update(self, address, port):
        self.address = address
        self.port = port
        self.connectinInfoReady_f = True
        print "Address: %s, Port: %s" % (address, port)
        self.pushButton_3.setEnabled(True)

        self.displayMessage("Connected to %s" % address, sender=True)

    def on_encryptedUpdate(self, encrypted):
        if encrypted and not self.radioButton.isChecked():
            self.radioButton.click()
            self.displayMessage("Connection encrypted.")
        elif not encrypted and not self.radioButton_2.isChecked():
            self.radioButton_2.click()
            self.displayMessage("Connection decrypted.")

    def on_quickConnect_clicked(self):
        if self.radioButton.isChecked():
            self.logic.beginPairing(self.address, self.port, encrypted=True)
        else:
            self.logic.beginPairing(self.address, self.port, encrypted=False)

    ####################################################################
    # on_serverPort_ready:
    #
    # Updates the listening port number visible in the User Info box.
    #
    # PARAMS:
    #   port    -   The listening port on the TCP Server socket (int)
    ####################################################################
    def on_serverPort_ready(self, port):
        # update the port number in GUI with listening port
        self.lineEdit_5.setText(str(port))

    ####################################################################
    # on_connected_clicked:
    #
    # Displays the Connect dialog box, which lets the user enter the
    # details of the client they wish to communicate with
    ####################################################################
    def on_connect_clicked(self):
        # pop up the connection dialog
        self.connectDialog.show()

    ####################################################################
    # on_connectInfo_ready:
    #
    # Attempts to connect to the specified host.
    #
    # PARAMS:
    #   address -   host address    (str)
    #   port    -   The target host's listening port    (str)
    ####################################################################
    def on_connectInfo_ready(self, address, port):
        self.connectinInfoReady_f = True
        self.address = address
        self.port = port

        if self.radioButton.isChecked():
            # encrypted
            self.logic.beginPairing(address, port, encrypted=True)
        elif self.radioButton_2.isChecked():
            # decrypted
            self.logic.beginPairing(address, port, encrypted=False)

    def on_encrypt_clicked(self, human):
        self.logic.encryptConnection()
        # if self.connectinInfoReady_f and human:
        # self.connectDialog.pushButton.click()
        # pass
        # self.logic.beginPairing(self.address, self.port, encrypted=True)

    def on_decrypt_clicked(self):
        self.logic.decryptConnection()
        # if self.connectinInfoReady_f:
        # self.connectDialog.pushButton.click()
        # pass
        # self.logic.beginPairing(self.address, self.port, encrypted=False)

    ####################################################################
    # on_about_clicked
    #
    # Displays the About window
    ####################################################################
    def on_about_clicked(self):
        self.aboutDialog.show()

    def on_demo_clicked(self):
        self.demoDialog.show()

    ####################################################################
    # on_attach_clicked:
    #
    # Brings up the Choose File dialog to get the path for the file
    # that needs to be attached to the message. Once the path is
    # retrieved, the chosen file will be stored to memory in preparation
    # for transit.
    ####################################################################
    def on_attach_clicked(self):
        # print "Attaching file"
        path = QtGui.QFileDialog.getOpenFileName(self, 'Open file',
                                                 'c:\\', "Any (*)")
        self.logic.attachFile(path)

    ####################################################################
    # on_send_triggered
    #
    # Sends out the current message/file to the connected host
    ####################################################################
    def on_send_triggered(self):
        self.sendMessage()
        self.sendFile()

    ####################################################################
    # on_messageDraft_changed
    #
    # Disables the send button if there is no text in the input field
    ####################################################################
    def on_messageDraft_changed(self):
        if not str(self.lineEdit.text()):
            self.pushButton.setDisabled(True)
        else:
            self.pushButton.setEnabled(True)

    ####################################################################
    # on_file_attached
    #
    # Updates the field which notifies the user about the current file
    # that's attached
    ####################################################################
    def on_file_attached(self, fileName):
        self.textBrowser_2.setText("Attached: " + fileName)
        self.textBrowser_2.setToolTip("Attached: " + fileName)

        self.pushButton.setEnabled(True)
        # cursor
        # insert html

    ####################################################################
    # on_socketState_changed
    #
    # Displays the current status of the connection to connected host
    # in the status bar
    ####################################################################
    def on_socketState_changed(self, status):
        # print "Connection state: " + str(status)
        self.statusBar.showMessage(status)

    ####################################################################
    # on_disconnect_clicked
    #
    # Closes the current connection
    ####################################################################
    def on_disconnect_clicked(self):
        self.logic.tearDownConnection()

    ####################################################################
    # on_quit_clicked
    #
    # Closes the application
    ####################################################################
    def on_quit_clicked(self):
        QtCore.QCoreApplication.quit()

    ####################################################################
    # on_file_sent
    #
    # Displays the hash of the file being sent on the text browser
    #
    # PARAMS
    #   hash    -   The hash of the file sent   (str)
    ####################################################################
    def on_file_sent(self, hash):
        self.displayMessage("Sending file with hash: " + hash, sender=True)

    ####################################################################
    # sendMessage
    #
    # Sends the text in the input field to the connected host.
    #
    # The actual message appears on the sender's text area and the user
    # input is cleared to allow for the next message to be typed in.
    # Stores the message as well for future use, if needed.
    ####################################################################
    def sendMessage(self):
        msg = str(self.lineEdit.text())
        if msg:
            self.displayMessage(msg, sender=True)
            self.lineEdit.clear()
            self.logic.deliverMessage(msg)
            self.recordMessage(msg)

    ####################################################################
    # sendFile
    #
    # Sends the file currently attached to the message.
    ####################################################################
    def sendFile(self):
        # Check to see if the text field containing information about
        # the attached file is empty which doubles as a check to see
        # if there is a file attached in the first place.
        if self.textBrowser_2.toPlainText():
            # Clear the attached box to prepare for the next file to
            # be attached
            self.textBrowser_2.clear()
            self.logic.deliverFile()

        self.pushButton.setEnabled(False)

    ####################################################################
    # showFileInfo
    #
    # Displays dialog box containing information about the file that
    # was received or just attached.
    #
    # PARAMS
    #   fileName    -   name of the file    (str)
    #   fileSize    -   size of the file    (int)
    #   hash        -   hash of the file    (str)
    #   sender      -   if the file originated from the user or from
    #                   someone else. Default to False.     (bool)
    ####################################################################
    def showFileInfo(self, fileName, fileSize, hash, sender=False):
        # Prepare dialog window and disable user input outside the box while active
        msg = QtGui.QMessageBox()
        msg.setIcon(QtGui.QMessageBox.Information)
        msg.setStandardButtons(QtGui.QMessageBox.Ok)
        msg.setModal(False)

        # Depending on whether or not the file was received or is being
        # sent, different flavor texts will be shown
        if sender:
            msg.setWindowTitle("File Attached")
            msg.setText("A file was successfully attached to the message")

        else:
            msg.setWindowTitle("Message Received.")
            msg.setText("A file was received")

        # Display file statistics
        msg.setInformativeText("File Name: " + str(fileName) + "\n" +
                               "File Size: " + str(fileSize) + " kB" + "\n\n" +
                               "SHA-256: " + str(hash))

        # Executes the dialog box rather than just showing as show()
        # will cause the dialog to immediately terminate once program
        # returns from this function causing it to go out of scope
        msg.exec_()

    ####################################################################
    # displayMessage
    #
    # Displays the messages sent or received to the chat box prepended
    # by the user name and time stamp
    #
    # PARAMS
    #   msg     -   message sent/received   (str)
    #   sender  -   flag which dictates whether they were the sender
    #               or receiver. Defaults to False     (bool)
    ####################################################################
    def displayMessage(self, msg, sender=False):
        timestamp = strftime("%H:%M", localtime())
        if sender:
            self.textBrowser.append("[" + str(timestamp) + "] " + "You>> " + emojize(str(msg), use_aliases=True))
        else:
            self.textBrowser.append("[" + str(timestamp) + "] " + "Anonymous>> " + emojize(str(msg), use_aliases=True))

    ####################################################################
    # recordMessage
    #
    # Stores the message sent by the user to a list for future use
    #
    # PARAMS
    #   msg     -   message sent    (str)
    ####################################################################
    def recordMessage(self, msg):
        # store message into history
        self.history.append(msg)

        # reset the index to point at the last message that was sent
        self.currMsgIndex = len(self.history) - 1
        self.currMsgIndex += 1

    ####################################################################
    # displayListenStatus
    #
    # Pretty useless since it will never get called
    #
    # PARAMS
    #   status      -   status of the listening port    (str)
    ####################################################################
    def displayListenStatus(self, status):
        if status is 1:
            self.statusBar.showMessage("Unable to start listening port")

    ####################################################################
    # keyPressEvent
    #
    # Allows the user to step through to older messages that were
    # previously sent and updates the current input field with that
    # message.
    #
    # Messages are stepped through using the up and down arrow leys
    #
    # PARAMS
    #   event   -   the key that was pressed
    ####################################################################
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


########################################################################################################################
# Logic
#
# DESCRIPTION:
# Handles the communication between the Communication and ChatWindow classes. Acts as the "API layer" of sorts
# which is accessible to the ChatWindow class. This way the GUI doesn't need to know anything about how the
# underlying communication works and needs only access the methods available in this class.
#
# Cross-class interaction is done through the use of signals and slots. Signals are required to be sent to the
# Communications class as that is running on a separate thread, meaning that calling its functions directly would
# cause unintentional behavior. The GUI is then sent signals to update its components with new information such as
# files or messages received.
#
# File i/o tasks are run on a separate thread to make sure that the GUI isn't impacted. For the same reason, the
# Communication class is also set to run on a separate thread. However with the use of signals and sockets this isn't
# necessary since it will never take over the GUI thread. It was simply done for convenience.
#
# SLOTS:
#   def forwardReceivedMessage(msg)
#   def on_pair_state_changed(state)
#   def on_file_received(name, size, hash)
#   def on_server_ready(port)
#   def on_file_loaded(data, name, size, hash)
#
# SIGNALS:
#   outGoingMessageReady(int, QString)
#   messageReceived(str)
#   fileSent(str)
#   pairRequest(str, str)
#   tearDownInitiated()
#   forwardServerPort(int)
#   forwardConnectionStatus(str)
#   forwardSocketState(str)
#
# PUBLIC FUNCTIONS
#   def deliverMessage(msg)
#   def deliverFile(file)
#   def tearDownConnection()
#   def beginPairing(address, port)
#   def attachFile(file)
########################################################################################################################

class Logic(QtCore.QObject):
    """""""""""""""""""""""""""""""""""""""
    MESSAGE SIGNALS
    """""""""""""""""""""""""""""""""""""""
    # To comms class
    outgoingMessageReady = QtCore.pyqtSignal(int, str)

    # to GUI class
    messageReceived = QtCore.pyqtSignal(str)
    fileSent = QtCore.pyqtSignal(str)
    encryptedUpdate = QtCore.pyqtSignal(bool)

    """""""""""""""""""""""""""""""""""""""
    CONNECTION SIGNALS
    """""""""""""""""""""""""""""""""""""""
    # To comms class
    pairRequest = QtCore.pyqtSignal(str, str)
    tearDownInitiated = QtCore.pyqtSignal()
    updateInitiator = QtCore.pyqtSignal(bool)
    updateEncrypted = QtCore.pyqtSignal(bool)

    # To GUI class
    forwardServerPort = QtCore.pyqtSignal(int)
    forwardConnectionStatus = QtCore.pyqtSignal(str)
    forwardSocketState = QtCore.pyqtSignal(str)
    forwardPeerDetails = QtCore.pyqtSignal(str, str)

    """""""""""""""""""""""""""""""""""""""
    FILE SIGNALS
    """""""""""""""""""""""""""""""""""""""
    # To GUI class
    forwardFileDetails = QtCore.pyqtSignal(str, int, str)
    fileReadyForWrite = QtCore.pyqtSignal(int, QtCore.QByteArray)
    readAttachedFile = QtCore.pyqtSignal(str)
    fileRead = QtCore.pyqtSignal(str)

    def __init__(self):
        QtCore.QObject.__init__(self)

        # handles all communication logic
        self.comm = Communication()

        # sending data
        self.rawFile = None
        self.fileName = ""
        self.fileSize = 0
        self.fileHash = None

        # connect comm signal/slots
        self.comm.messageReceived.connect(self.forwardReceivedMessage)
        self.comm.pairStateChanged.connect(self.on_pair_state_changed)
        #        self.comm.listenError.connect(lambda: self.displayListenStatus(self.comm.__listenPortLive))
        self.comm.fileReceived.connect(self.on_file_received)
        self.comm.serverReady.connect(self.on_server_ready)
        self.comm.encrypted.connect(self.on_encrypted)
        self.comm.peerDetails.connect(self.on_peerDetails_arrived)
        self.commThread = QtCore.QThread()
        self.comm.moveToThread(self.commThread)

        self.outgoingMessageReady.connect(self.comm.write)
        self.fileReadyForWrite.connect(self.comm.write)
        self.pairRequest.connect(self.comm.pair)
        self.tearDownInitiated.connect(self.comm.tearDown)
        self.updateInitiator.connect(self.comm.on_update_initiator)
        self.updateEncrypted.connect(self.comm.on_update_encrypted)

        self.commThread.started.connect(self.comm.run)
        self.commThread.start()

        # file IO stuff
        self.fileIO = FileIOThread()
        self.fileIO.readComplete.connect(self.on_file_loaded)

        self.fileIOThread = QtCore.QThread()
        self.fileIO.moveToThread(self.fileIOThread)

        self.readAttachedFile.connect(self.fileIO.readFile)
        self.fileIOThread.started.connect(self.fileIO.run)
        self.fileIOThread.start()

    def on_peerDetails_arrived(self, address, port):
        self.forwardPeerDetails.emit(address, port)

    def on_encrypted(self, encrypted):
        self.encryptedUpdate.emit(encrypted)

    ####################################################################
    # on_pair_state_changed
    #
    # Categorises the status of the request port's state based on
    # the state code provided.
    #
    # EMITS
    #   forwardSocketState(state)
    #
    # PARAMS
    #   state   -   status of the listening port    (str)
    ####################################################################
    def on_pair_state_changed(self, state):
        if state == 0:
            self.forwardSocketState.emit("Disconnected")
        elif state == 1:
            self.forwardSocketState.emit("Looking up host name..")
        elif state == 2:
            self.forwardSocketState.emit("Connecting..")
        elif state == 3:
            self.forwardSocketState.emit("Connected")
        elif state == 6:
            self.forwardSocketState.emit("Disconnecting..")

    ####################################################################
    # on_file_received
    #
    # This is called whenever files have been read into the receiver
    # socket.
    #
    # EMITS
    #   forwardFileDetails(str, int, str)
    #
    # PARAMS
    #   name    -   name of the file
    #   size    -   size of the file
    #   hash    -   hash of the file
    ####################################################################
    def on_file_received(self, name, size, hash):
        # print "received file"
        self.forwardFileDetails.emit(name, size, hash)

    ####################################################################
    # on_file_loaded
    #
    # Called whenever a file has been stored into memory when the user
    # requests to attach it to a message. Separate from on_file_received
    # as this is from a literal FileIO operation
    #
    # PARAMS
    #   data    -   raw file data in bit
    #   name    -   name of the file
    #   size    -   size of the file
    #   hash    -   hash of the file
    ####################################################################
    def on_file_loaded(self, data, name, size, hash):
        # print "Got to on_fileReady"
        # get the data
        self.rawFile = data

        # extract name, size and hash
        self.fileName = name
        self.fileSize = size
        self.fileHash = hash

        self.fileRead.emit(self.fileName)

    ####################################################################
    # on_server_ready
    #
    # Called when the listening socket has successfully started and is
    # listening for new connections
    #
    # EMITS
    #   forwardServerPort(int)
    #
    ####################################################################
    def on_server_ready(self, port):
        # alert the UI about the port that the server is listening on
        self.forwardServerPort.emit(port)

    ####################################################################
    # deliverFile
    #
    # Writes the file into the TCP stream to send it off to the listening
    # socket.
    #
    # EMITS
    #   outgoingMessageReady(int, str)
    #   fileReadyForWrite(int, str)
    #   fileSent(str)
    #
    ####################################################################
    def deliverFile(self):
        # inform the user about the incoming file
        self.outgoingMessageReady.emit(Config.Message_t, "Sending file with hash: " + self.fileHash)

        # first send the file name
        self.outgoingMessageReady.emit(Config.FileName_t, self.fileName)

        # send out the file and reset the file attached flag
        self.fileReadyForWrite.emit(Config.FileData_t, self.rawFile)

        # send out a signal with the file hash
        self.fileSent.emit(self.fileHash)

    ####################################################################
    # attachFile
    #
    # Called when the user requests to attach a file. The FileIO thread
    # is alerted about the file to be attached.
    #
    # PARAMS
    #   path    -   the complete path to the file to attached
    ####################################################################
    def attachFile(self, path):
        # if the path isn't empty, set the file flag to true and prep the file for transfer
        if path:
            # print "File Attached"
            # signal out to the FileIO object that a file is ready to be read
            self.readAttachedFile.emit(path)

    ####################################################################
    # forwardReceivedMessage
    #
    # Called when the receiving socket has received a message. Sends out
    # the message to the UI to display it.
    #
    # EMITS
    #   messageReceived(str)
    #
    ####################################################################
    def forwardReceivedMessage(self, msg):
        # print "Forwarding message"
        self.messageReceived.emit(msg)

    ####################################################################
    # beginPairing
    #
    # Commences the pairing action between two applications. Alerts
    # the communication class about an address and a port that it would
    # like to communicate with.
    #
    # EMITS
    #   address     -   host address of the target client   (str)
    #   port        -   port of the receiving port  (int)
    #
    ####################################################################
    def beginPairing(self, address, port, encrypted=False):
        # print "pairing from logic"
        # ensure that each connection/reconnect is a fresh one

        self.tearDownInitiated.emit()
        # get the connection details from the connection dialog
        self.updateInitiator.emit(True)
        print "Comm status: %r" % self.comm.initiator
        self.updateEncrypted.emit(encrypted)
        self.pairRequest.emit(address, port)
        # self.comm.pair(address, port)

    ####################################################################
    # deliverMessage
    #
    # Alerts the Communication object that a message is ready to be
    # written into the stream
    #
    # PARAMS
    #   msg     -   message to be sent (str)
    #
    # EMITS
    #   outgoingMessageReady()
    ####################################################################
    def deliverMessage(self, msg):
        # print "Sending msg from Logic" + str(int(QtCore.QThread.currentThreadId()))

        # check if the msg is empty
        if msg:
            self.outgoingMessageReady.emit(Config.Message_t, msg)

    ####################################################################
    # displayMessage
    #
    # Alerts the GUI that a message has been received and would like to
    # be displayed on the chat screen with the appropriate sender/receiver
    # tag
    #
    # PARAMS
    #   msg     -   message to be sent (str)
    #   sender  -   flags the origination of the message being  (bool)
    ####################################################################
    def displayMessage(self, msg, sender):
        self.messageReceived.emit(msg, sender)
        # print "got message: " + msg

    ####################################################################
    # tearDownConnection
    #
    # Alerts the Communication object that a request to disconnect the
    # socket has been made
    #
    # EMITS
    #   tearDownInitiated()
    ####################################################################
    def tearDownConnection(self):
        self.tearDownInitiated.emit()

    def decryptConnection(self):
        self.updateEncrypted.emit(False)

    def encryptConnection(self):
        self.updateEncrypted.emit(True)


########################################################################################################################
# Communication
#
# DESCRIPTION:
# This class' sole purpose is to take care of all TCP communications. It is written using the QtNetwork library,
# utilising the QtTcpSocket and QtTcpServer classes to handle connections and communications.
#
# Three sockets in total are being managed within this class and their names are:
#   1) tcpServer
#   2) tcpSocket_request
#   3) tcpSocket_receive
#
# tcpServer is maintained throughout the entire application's lifetime. It is the socket that other users connect to.
# tcpSocket_request is the socket which takes care of all outgoing communications to TCP servers. Messages are written
# to this socket and will then be readable by the socket it is connected to.
# tcpSocket_receive is a socket returned by tcpServer whenever a new connection is detected. Until disconnected, this
# will be live and listening for any new data to arrive.
#
# This class is expected to be ran in its own thread which is why it inherits QThread. Once started in its own thread,
# the overloaded function 'run()' will be called which will kick start tcpServer to begin listening for new connections
# as well as make the necessary connections between signals and slots.
#
# Once data has been read (be it files or messages), signals are sent back out where any subscribed classes can listen
# in and make use of that data for their own processing. In this way the only domain that this class knows of is its own
# networking one. It does not know what happens to the data it reads or writes.
#
# SIGNALS
#   messageReceived(str)
#   fileReceived(str, int, str)
#   pairStateChanged(SocketState)
#   pairSuccess()
#   serverReady(int)
#
# SLOTS
#   def on_connection_accepted()
#   def on_connection_failed(error)
#   def on_connectionState_changed(state)
#   def on_newConnection()
#
########################################################################################################################
class Communication(QtCore.QThread):
    HEADER_SIZE = 6  # 4 bytes for payload size, 2 bytes for payload type

    """""""""""""""""""""""""""""""""""""""
    MESSAGE/FILE SIGNALS
    """""""""""""""""""""""""""""""""""""""
    messageReceived = QtCore.pyqtSignal(str)
    fileReceived = QtCore.pyqtSignal(str, int, str)
    encrypted = QtCore.pyqtSignal(bool)

    """""""""""""""""""""""""""""""""""""""
    PAIRING SIGNALS
    """""""""""""""""""""""""""""""""""""""
    listenError = QtCore.pyqtSignal()
    pairStateChanged = QtCore.pyqtSignal(int)
    pairSuccess = QtCore.pyqtSignal()
    serverReady = QtCore.pyqtSignal(int)
    peerDetails = QtCore.pyqtSignal(str, str)

    def __init__(self):
        super(Communication, self).__init__()

        # IO variables
        self.__blockSize = 0

        self.__msgType = -1
        self.__pairPort = -1

        # Variables to be passed by signals
        self.__msg = None
        self.__fileHash = ""
        self.__fileName = ""
        self.__fileSize = 0
        self.__rawFile = None
        self.__listenPortLive = False

        # One TcpSocket is for the server portion of the program (_receive)
        # the other is for the client portion of the program (_request)
        self.__tcpSocket_receive = QtNetwork.QTcpSocket(self)
        self.__tcpSocket_request = QtNetwork.QTcpSocket(self)
        self.__tcpServer = QtNetwork.QTcpServer(self)

        # encryption variables
        self.__stage = 0
        self.encrypted_f = False
        self.__key = RSA.generate(1024)
        print "Generated Key"
        print self.__key.publickey().exportKey()
        self.__partnerKey = ""
        self.__pass = str(randint(0, sys.maxint))
        self.__partnerPass = ""
        self.__sessionKey = ""
        self.initiator = False
        self.__secretReady = False
        self.__aes = aes.AESCipher(key="")
        # self.identity = ""

    ####################################################################
    # run
    #
    # When the communication thread is started this is the method that's
    # called.
    # Sets up the signals and slots for the request and server sockets
    # for new connections
    ####################################################################
    def run(self):
        # connecting SIGNALS and SLOTS
        self.__tcpSocket_request.connected.connect(self.on_connection_accepted)
        self.__tcpSocket_request.error.connect(self.on_connection_failed)
        self.__tcpSocket_request.disconnected.connect(self.tearDown)
        self.__tcpSocket_request.stateChanged.connect(self.on_connectionState_changed)
        self.__tcpServer.newConnection.connect(self.on_newConnection)

        self.startTcpServer()
        QtCore.QThread.exec_(self)

    def on_update_encrypted(self, encrypted):
        self.encrypted_f = encrypted

    def on_update_initiator(self, initiator):
        self.initiator = initiator

    ####################################################################
    # on_connectionState_changed
    #
    # The request socket has changed its state and this slot is called
    # inform subscribed objects of the new state
    #
    # EMITS
    #   pairStateChanged(str)
    ####################################################################
    def on_connectionState_changed(self, state):
        # print "Socket state is now: " + str(self.__tcpSocket_request.state())
        self.pairStateChanged.emit(state)

    ####################################################################
    # on_connection_failed
    #
    # EMITS
    #   pairStateChanged(str)
    ####################################################################
    def on_connection_failed(self, error):
        # print error
        # print "Something went wrong"
        pass

    # move to its own function so that this won't be running on the main thread
    def startTcpServer(self):
        # begin listening at a random port
        if not self.__tcpServer.listen(QtNetwork.QHostAddress(socket.gethostbyname(socket.gethostname())),
                                       randint(5000, 65535)):
            # server couldn't start
            self.__listenPortLive = False
            self.listenError.emit()
        else:
            # server started successfully
            self.__listenPortLive = True
            self.serverReady.emit(self.__tcpServer.serverPort())

    def on_newConnection(self):
        # assign the incoming connection to a socket and connect that socket's
        # readyRead signal to read the message
        self.__tcpSocket_receive = self.__tcpServer.nextPendingConnection()
        self.__tcpSocket_receive.readyRead.connect(self.read)

    # write routine which doesn't care about what it's writing or who it's writing to
    def write(self, payload_t, payload):
        # print "Writing from thread: " + str(int(QtCore.QThread.currentThreadId()))
        # will contain the message
        block = QtCore.QByteArray()

        # inform that this message is to show the listening port
        # prepare the output stream
        out = QtCore.QDataStream(block, QtCore.QIODevice.WriteOnly)
        out.setVersion(QtCore.QDataStream.Qt_4_0)
        out.writeUInt32(0)  # placeholder for payload size
        out.writeUInt16(payload_t)  # payload_t is int, constructor only takes str

        if self.__secretReady:
            print "Encrypting with AES"
            payload = self.__aes.encrypt(payload)

        # # print "past header"
        # determine which procedure to use when writing to the datastream
        if payload_t == Config.Port_t or payload_t == Config.Message_t or payload_t == Config.FileName_t:
            # payload is a string
            if payload_t == Config.Port_t:
                print "Sending server's listening port: " + payload
            out.writeString(payload)
        elif payload_t == Config.FileData_t:
            # payload is a byte array
            out.writeRawData(payload)
        elif payload_t == Config.Security_t:
            # payload is a stream of bytes dealing with security
            out.writeBytes(payload)

        # # print "data on datastream"
        # go back to the start and write the size of the payload
        out.device().seek(0)
        out.writeUInt32(block.size() - self.HEADER_SIZE)

        # encrypt block here if AES is ready

        self.__tcpSocket_request.write(block)

    # returns QDataStream object for processing
    def blockBuilder(self, *args):
        block = QtCore.QByteArray()
        stream = QtCore.QDataStream(block, QtCore.QIODevice.WriteOnly)

        for arg in args:
            stream.writeString(arg)

        return block

    # Goal: set a session key
    # if B, I am B
    #   stage 0
    #       send Kb
    #       stage++
    #   stage 1
    #       gen Kab
    #       send PassB (challenge)
    #       stage++
    #   stage2
    #       verify response
    #       stage++
    # if A, I am A
    #   stage 0
    #       send PassA
    #       stage++
    #   stage 1
    #       stage++
    #       send PassB (response)
    #
    def read(self):
        # print "Reading from thread: " + str(int(QtCore.QThread.currentThreadId()))
        # Constructs a data stream that uses the I/O device.
        instr = QtCore.QDataStream(self.__tcpSocket_receive)
        instr.setVersion(QtCore.QDataStream.Qt_4_0)

        # updates the GUI on the status of encryption for toggle button
        # if not self.__secretReady:
        #     self.encrypted.emit(False)
        # else:
        #     self.encrypted.emit(True)

        # if we haven't read anything yet from the server and size is not set
        if self.__blockSize == 0:
            # the first two bytes are reserved for the size of the payload.
            # must check it is at least that size to take in a valid payload size.
            if self.__tcpSocket_receive.bytesAvailable() < self.HEADER_SIZE:
                # print "smaller than header"
                return

            # read the size of the byte array payload from server.
            # Once the first flag is consumed, read the message type on the payload
            # print "getting new payload info"

            self.__blockSize = instr.readUInt32()
            self.__msgType = instr.readUInt16()
            # print "Msg type: " + str(self.__msgType)
        # the data is incomplete so we return until the data is good
        if self.__tcpSocket_receive.bytesAvailable() < self.__blockSize:
            # print "message incomplete"
            return

        # sort out what to do with the received data
        # go back to the start of the payload
        if self.__msgType == Config.Port_t:
            # message contains port information
            # save the port to set the request socket to point at that port
            # sometimes required.. ie. over local network this seemed to become an issue.. fine local
            self.__pairPort = instr.readString()
            print "Port read as: " + self.__pairPort
            self.peerDetails.emit(str(self.__tcpSocket_receive.peerAddress().toString()), self.__pairPort)
            self.pair(self.__tcpSocket_receive.peerAddress(), int(self.__pairPort))

        elif self.__msgType == Config.Message_t:
            # normal message
            # read in the message and inform connected objects about the contents
            if self.__secretReady:
                encrypted_msg = instr.readString()
                msg = self.__aes.decrypt(encrypted_msg)
                # self.encrypted.emit(True)
            else:
                msg = instr.readString()
                # self.encrypted.emit(False)
            self.messageReceived.emit(msg)
        elif self.__msgType == Config.FileData_t:
            if self.__secretReady:
                # self.encrypted.emit(True)
                self.__rawFile = self.__aes.decrypt(instr.readRawData(self.__blockSize))
            else:
                self.__rawFile = instr.readRawData(self.__blockSize)
                # self.encrypted.emit(False)
            # downloads go to the user's desktop folder. will emit a signal when finished
            file = QtCore.QFile(Config.DownloadDir + self.__fileName)
            file.open(QtCore.QIODevice.WriteOnly)
            file.write(self.__rawFile)
            file.close()

            fileSize = QtCore.QFileInfo(file).size() / 1000
            fileHash = hashlib.sha256(self.__rawFile).hexdigest()
            self.fileReceived.emit(self.__fileName, fileSize, fileHash)
        elif self.__msgType == Config.FileName_t:
            # store the file name. used when saving the received file that should come straight after this
            if self.__secretReady:
                # self.encrypted.emit(True)
                self.__fileName = self.__aes.decrypt(instr.readString())
            else:
                # self.encrypted.emit(False)
                self.__fileName = instr.readString()
                # print "received file name: " + str(self.__fileName)
        elif self.__msgType == Config.Security_t:
            print "security msg"
            recreate = QtCore.QByteArray(instr.readBytes())
            in_rec = QtCore.QDataStream(recreate, QtCore.QIODevice.ReadOnly)
            sender = in_rec.readString()
            receiver = in_rec.readString()

            # print "Sender: %s, Receiver: %s" % (sender, receiver)
            # if not self.initiator:
            #     self.identity = "B"
            # else:
            #     self.identity = "A"

            # Go through all of the stages depending on whether the client is the initiator or not
            if "B" in receiver:
                # this is the receiver
                # print "not initiator"
                if self.__stage == 0:
                    # print "received Ka.. sending kb"
                    self.__partnerKey = RSA.importKey(in_rec.readString())
                    # send public key
                    out = self.blockBuilder("B", "A", self.__key.publickey().exportKey())
                    self.write(Config.Security_t, out)
                    # increment stage
                    self.__stage += 1
                elif self.__stage == 1:
                    # print "Received PassA... generating session key.. sending Pass B"
                    self.__partnerPass = in_rec.readString()
                    # generate session key
                    self.__sessionKey = self.__partnerPass + self.__pass
                    signature = in_rec.readString()
                    security.verify(self.__partnerPass, signature, self.__partnerKey.exportKey())
                    # send pass B
                    out = self.blockBuilder("B", "A", self.__pass, self.__partnerPass)
                    self.write(Config.Security_t, out)
                    # increment stage
                    self.__stage += 1
                elif self.__stage == 2:
                    # print "Received PassB... checking if correct"
                    nonce = in_rec.readString()
                    if nonce in self.__pass:
                        print "We have a match"
                    else:
                        print "Nonce: %s did not match %s" % (nonce, self.__pass)
                    # setup AES cipher
                    self.__secretReady = True
                    print "Session key: " + self.__sessionKey
                    self.__aes = aes.AESCipher(key=self.__sessionKey)
                    # increment stage
                    self.__stage += 1
            elif "A" in receiver:
                # print "initiator"
                if self.__stage == 0:
                    # print "Received Kb... Sending PassA"
                    key = in_rec.readString()
                    self.__partnerKey = RSA.importKey(key)
                    # sign pass
                    signature = security.sign(self.__pass, self.__key.exportKey())
                    # send pass and signature
                    out = self.blockBuilder("A", "B", self.__pass, str(signature))
                    self.write(Config.Security_t, out)
                    # increment stage
                    self.__stage += 1
                elif self.__stage == 1:
                    # print "Received PassB... generating session key... sending pass b"
                    self.__partnerPass = in_rec.readString()
                    nonce = in_rec.readString()  # read back response should be same
                    if nonce in self.__pass:
                        print "We have a match"
                    else:
                        print "Nonce: %s did not match %s" % (nonce, self.__pass)
                    # generate session key
                    self.__sessionKey = self.__pass + self.__partnerPass
                    out = self.blockBuilder("A", "B", self.__partnerPass)
                    # send challenge response
                    self.write(Config.Security_t, out)
                    # setup AES cipher
                    # print "Session key: " + self.__sessionKey
                    self.__secretReady = True
                    self.__aes = aes.AESCipher(key=self.__sessionKey)
                    # increment stage
                    self.__stage += 1

        # reset the block size for next msg to be read
        self.__blockSize = 0
        self.__msgType = -1

        # recursive call to check if there is data still to be read.
        self.read()

    def pair(self, host, port):
        # allows for connection between two chatting programmes
        # possibly the place where AES, SHA and RSA will take place
        # # print "pairing from thread: " + str(int(QtCore.QThread.currentThreadId()))
        if self.__tcpSocket_request.state() != QtNetwork.QAbstractSocket.ConnectedState:
            # print "Pairing bruh"
            self.__tcpSocket_request.connectToHost(host, int(port))
            # print "Called connectToHost yo"

    # request socket has been connected to the host
    # assume we are A and act accordingly
    def on_connection_accepted(self):
        # print "connection accepted in thread: " + str(int(QtCore.QThread.currentThreadId()))
        # pairing done, let connected objects know
        self.pairSuccess.emit()

        # give the connected host the port address of the listening server to allow them to connect back
        self.write(Config.Port_t, str(self.__tcpServer.serverPort()))

        print "========================================================"
        print "Starting security"
        print "========================================================"
        print "Initiator: %r, Encrypted: %r" % (self.initiator, self.encrypted_f)

        if self.encrypted_f:
            self.encrypted.emit(True)
        else:
            self.encrypted.emit(False)

        if self.initiator and self.encrypted_f:
            # self.identity = "A"
            block = QtCore.QByteArray()
            out = QtCore.QDataStream(block, QtCore.QIODevice.WriteOnly)
            out.writeString("A")
            out.writeString("B")
            out.writeString(self.__key.publickey().exportKey())
            self.write(Config.Security_t, block)

    def tearDown(self):
        # disconnect both request and receive sockets
        print "Tearing down"
        self.__tcpSocket_request.abort()
        self.__tcpSocket_receive.abort()

        self.__stage = 0
        self.__key = RSA.generate(1024)
        self.__partnerKey = ""
        self.__pass = str(randint(0, sys.maxint))
        self.__partnerPass = ""
        self.__sessionKey = ""
        self.__secretReady = False
        self.encrypted_f = False
        self.__aes = aes.AESCipher("")
        self.initiator = False
        # self.identity = ""

        # updates the GUI depending on encrypted flag
        # if self.encrypted_f:
        #     self.encrypted.emit(True)
        # else:
        #     self.encrypted.emit(False)


########################################################################################################################
# FileIOThread
#
# //TO DOX
#
########################################################################################################################
class FileIOThread(QtCore.QThread):
    readComplete = QtCore.pyqtSignal(QtCore.QByteArray, str, int, str)
    error = QtCore.pyqtSignal()

    def __init__(self):
        QtCore.QThread.__init__(self)

    def run(self):
        # run within its own event loop
        QtCore.QThread.exec_(self)

    def readFile(self, path):
        # print "Reading file"
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


########################################################################################################################
# AboutDialog
#
# DESCRIPTION:
# Provides a window which gives a description on what the program is and what is was built with.
#
# The UI is imported from a python file that was generated from the XML file designed in Qt Designer using pyuic4.
########################################################################################################################
class AboutDialog(QtGui.QDialog, ui_about.Ui_Dialog):
    def __init__(self, parent=None):
        super(AboutDialog, self).__init__(parent)
        self.setupUi(self)

        # keep focus fixed to this window
        self.setModal(True)

        # prevent resizing
        self.setFixedSize(451, 213)


class DemoDialog(QtGui.QDialog, ui_demo.Ui_Dialog):
    def __init__(self, parent=None):
        super(DemoDialog, self).__init__(parent)
        self.setupUi(self)

        # keep focus fixed to this window
        self.setModal(True)

        # connect button to slot
        self.pushButton.clicked.connect(self.on_demo_clicked)
        self.lineEdit.textChanged.connect(self.on_messageDraft_changed)
        self.lineEdit_2.textChanged.connect(self.on_messageDraft_changed)
        self.comboBox.currentIndexChanged.connect(self.on_comboBox_changed)
        self.pushButton.setDisabled(True)

    def on_demo_clicked(self):
        self.textBrowser.clear()
        crypt = self.comboBox.itemText(self.comboBox.currentIndex())

        if crypt == "AES":
            self.on_aes_requested()
        elif crypt == "RSA":
            self.on_rsa_requested()
        elif crypt == "SHA-256":
            self.on_sha_requested()

    def on_comboBox_changed(self, index):
        if index == 0:
            self.lineEdit_2.setEnabled(True)
            self.label_3.setEnabled(True)
        else:
            self.lineEdit_2.setDisabled(True)
            self.label_3.setDisabled(True)

    def on_messageDraft_changed(self):
        if self.comboBox.itemText(self.comboBox.currentIndex()) == "AES":
            if not str(self.lineEdit.text()) or not str(self.lineEdit_2.text()):
                self.pushButton.setDisabled(True)
            else:
                self.pushButton.setEnabled(True)
        else:
            if not str(self.lineEdit.text()):
                self.pushButton.setDisabled(True)
            else:
                self.pushButton.setEnabled(True)

    def on_rsa_requested(self):
        random_generator = Random.new().read
        key = RSA.generate(1024, random_generator)  # generate public & private key
        # 1024 = key length (bits) of RSA modulus

        publickey = key.publickey()  # pub key export for exchange

        data = str(self.lineEdit.text())
        encrypted = publickey.encrypt(data, 32)  # 32 = number of bit
        # message to encrypt is in the above line 'encrypt this message'

        f = open('encryption.txt', 'w')
        f.write(str(encrypted))  # write ciphertext to file
        f.close()

        # decrypted code below
        f = open('encryption.txt', 'r')
        message = f.read()

        decrypted = key.decrypt(
            ast.literal_eval(str(message)))  # literal_eval = used to safely evaluated the encrypted text
        # key.decrypt will not evaluate str(encrypt) without
        # literal_eval.  Error = str too large

        self.textBrowser.insertHtml("<b>Plain:</b> " + data)
        self.textBrowser.insertHtml("<br></br>")
        self.textBrowser.insertHtml("<b>Encrypted:</b> " + str(encrypted))
        self.textBrowser.insertHtml("<br></br>")
        self.textBrowser.insertHtml("<b>Decrypted:</b> " + str(decrypted))

    def on_aes_requested(self):
        key = str(self.lineEdit_2.text())
        ian = aes.AESCipher(key=key)

        # create data (str)
        data = str(self.lineEdit.text())
        # encrypt data
        encrypted = ian.encrypt(data)

        # decrypt data
        decrypted = ian.decrypt(encrypted)
        self.textBrowser.insertHtml("<b>Plain:</b> " + data)
        self.textBrowser.insertHtml("<br></br>")
        self.textBrowser.insertHtml("<b>Key:</b> " + key)
        self.textBrowser.insertHtml("<br></br>")
        self.textBrowser.insertHtml("<b>Encrypted:</b> " + str(encrypted))
        self.textBrowser.insertHtml("<br></br>")
        self.textBrowser.insertHtml("<b>Decrypted:</b> " + str(decrypted))

    def on_sha_requested(self):
        data = str(self.lineEdit.text())
        hash = hashlib.sha256(data).hexdigest()

        self.textBrowser.insertHtml("<b>Plain:</b> " + data)
        self.textBrowser.insertHtml("<br></br>")
        self.textBrowser.insertHtml("<b>Hashed:</b> " + str(hash))


########################################################################################################################
# ConnectDialog
#
# DESCRIPTION:
# Provides a window which allows the user to initiate a connection with another client.
#
# The UI is imported from a python file that was generated from the XML file designed in Qt Designer using pyuic4.
#
# SIGNALS:
#   inputReady(str, str)
#
# SLOTS:
#   def on_input_changed()
#   def on_connect_clicked()
#
# PUBLIC FUNCTIONS:
#   isValidInput()
########################################################################################################################
class ConnectDialog(QtGui.QDialog, ui_connect.Ui_Dialog):
    # SIGNALS
    inputReady = QtCore.pyqtSignal(str, str)

    def __init__(self, parent=None):
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
            self.inputReady.emit(self.lineEdit.text(), self.lineEdit_2.text())
            self.close()

    # can be made more rigorous if felt needed
    def isValidInput(self):
        # check if either of the inputs are empty
        if self.lineEdit.text() and self.lineEdit_2.text():
            return True
        else:
            return False


########################################################################################################################
# Config
#
# DESCRIPTION:
# Collection of constants used throughout the program
########################################################################################################################
class Config:
    DownloadDir = QtCore.QDir.homePath() + "\\Desktop\\"
    Port_t, Message_t, FileData_t, FileName_t, Security_t = range(5)  # Message types


if __name__ == "__main__":
    app = QtGui.QApplication(sys.argv)

    # setting app icon
    app.setWindowIcon(QtGui.QIcon('D.png'))
    appId = u'dollars.chat.app'
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(appId)

    chat = ChatWindow()
    chat.show()
    exit(app.exec_())
