# -*- coding: utf-8 -*-
from PyQt4 import QtGui, QtCore, QtNetwork

import sys
import ui_chat

# Thread will handle communications with the client that it's connected to.
# QTcpSocket setup to have a stream with the client
class MessageThread(QtCore.QThread):
    def __init__(self, socketDescriptor, parent):
        super(MessageThread, self).__init__(parent)

        self.socketDescriptor = socketDescriptor

    def run(self):
        pass

    # send out the message to the recipient
    def send_message(self, msg):
        tcpSocket = QtNetwork.QTcpSocket()  # ensure that the socket description is complete
        if not tcpSocket.setSocketDescriptor(self.socketDescriptor):
            self.error.emit(tcpSocket.error())
            return

        # will contain the message
        block = QtCore.QByteArray()

        # prepare the output stream
        out = QtCore.QDataStream(block, QtCore.QIODevice.WriteOnly)
        out.setVersion(QtCore.QDataStream.Qt_4_0)
        out.writeUint16(0)

        # write the message into the output stream
        out.writeString(msg)
        out.device().seek(0)
        out.writeUInt16(block.size() - 2)  # Manages the threads required for sending out messages to clients.

        # write out the message to the socket which is linked to the client
        tcpSocket.write(block)


class MessageServer(QtNetwork.QTcpServer):
    def __init__(self, parent=None):
        super(MessageServer, self).__init__(parent)

    # create a new thread for each new connection
    def incomingConnection(self, socketDescriptor):
        # the new thread will become the child of this current thread
        thread = MessageThread(socketDescriptor, self)
        thread.finished.connect(thread.deleteLater)
        thread.start()

class MainDialog(QtGui.QMainWindow, ui_chat.Ui_MainWindow):
    # setup the imported UI
    def __init__(self, parent=None):
        super(MainDialog, self).__init__(parent)

        # build UI from the one generated from pyuic4
        self.setupUi(self)

        # networking stuff
        self.tcpSocket = QtNetwork.QTcpSocket(self)
        self.messageServer = MessageServer()

        # connecting SIGNALS and SOCKETS
        self.pushButton.clicked.connect(self.on_send_clicked)

    # slot
    # connectto host (if not already connected)
    # make the client object send the message to the recipient
    def on_send_clicked(self):
        text = self.textBrowser.toPlainText()  # inherited from TextArea
        current_text = self.lineEdit.text()

        # only append if message is not empty
        if (current_text != ""):
            text += current_text
            self.textBrowser.setText(text + "\n")

            # keep the scroll bar locked to the bottom
            self.textBrowser.verticalScrollBar() \
                .setValue(self.textBrowser.verticalScrollBar().maximum())

        # add logic to communicate with the recipient
        self.setupConnection("localhost", 5319)

    def setupConnection(self, host, port):
        # check if socket is connected already
        if not (self.tcpSocket.state() is QtNetwork.QTcpSocket.ConnectedState and
                self.tcpSocket.state() is QtNetwork.QTcpSocket.HostLookupState and
                self.tcpSocket.state() is QtNetwork.QTcpSocket.ConnectingState):
            print "TCPSocket not connected.. setting up connection for you"
            self.tcpSocket.connectToHost(host, port)

        if self.tcpSocket.waitForConnected():
            print "Connected"
            self.sendMessage()
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

        print self.tcpSocket.state()
        # write out the message to the socket which is linked to the client
        self.tcpSocket.write(block)

# main method
if __name__ == "__main__":
    app = QtGui.QApplication(sys.argv)
    form = MainDialog()
    form.show()
    app.exec_()
