#!/usr/bin/env python

import random

from PyQt4 import QtCore, QtGui, QtNetwork


class Server(QtGui.QDialog):
    def __init__(self, parent=None):
        super(Server, self).__init__(parent)

        statusLabel = QtGui.QLabel()
        quitButton = QtGui.QPushButton("Quit")
        quitButton.setAutoDefault(False)

        self.tcpServer = QtNetwork.QTcpServer(self)
        self.tcpSocket = QtNetwork.QTcpSocket() # just declare it

        self.request = None
        self.blockSize = 0

        if not self.tcpServer.listen(QtNetwork.QHostAddress("localhost"), 5319):
            QtGui.QMessageBox.critical(self, "Fortune Server",
                                       "Unable to start the server: %s." % self.tcpServer.errorString())
            self.close()
            return

        statusLabel.setText("The server is running on port %d.\nRun the "
                            "Fortune Client example now." % self.tcpServer.serverPort())

        self.fortunes = (
            "You've been leading a dog's life. Stay off the furniture.",
            "You've got to think about tomorrow.",
            "You will be surprised by a loud noise.",
            "You will feel hungry again in another hour.",
            "You might have mail.",
            "You cannot kill time without injuring eternity.",
            "Computers are not intelligent. They only think they are.")

        quitButton.clicked.connect(self.close)
        self.tcpServer.newConnection.connect(self.newClient)


        buttonLayout = QtGui.QHBoxLayout()
        buttonLayout.addStretch(1)
        buttonLayout.addWidget(quitButton)
        buttonLayout.addStretch(1)

        mainLayout = QtGui.QVBoxLayout()
        mainLayout.addWidget(statusLabel)
        mainLayout.addLayout(buttonLayout)
        self.setLayout(mainLayout)

        self.setWindowTitle("Fortune Server")

    # The purpose of this slot is to select a random line from our list of fortunes,
    # encode it into a QByteArray using QDataStream, and then write it to the connecting socket.
    def sendFortune(self):
        # set the block size and bit size of datastream
        block = QtCore.QByteArray()

        # prepare a datastream that's only for writing using the byte array object as the set of data
        # that needs to be sent across
        out = QtCore.QDataStream(block, QtCore.QIODevice.WriteOnly)
        out.setVersion(QtCore.QDataStream.Qt_4_0)
        # Writes a signed 16-bit integer, i, to the stream and returns a reference to the stream.
        # initially size is unknown, simply reserve the spot here at the start
        out.writeUInt16(0)

        # get a fortune from the list of fortunes.
        fortune = self.fortunes[random.randint(0, len(self.fortunes) - 1)]

        try:
            # Python v3.
            fortune = bytes(fortune, encoding='ascii')
        except:
            # Python v2.
            pass

        # fortune is string so write it into the data stream as such
        out.writeString(fortune)
        # back track to position 0 of the IO stream to prepare to set the
        # actual size of the data
        out.device().seek(0)
        # write the actual data size into the beginning of the datastream
        out.writeUInt16(block.size() - 2)

        # store the pending connection as a TcpSocket
        clientConnection = self.tcpServer.nextPendingConnection()
        clientConnection.disconnected.connect(clientConnection.deleteLater)

        # write the byte array that has been populated with 'out' object into the socket
        clientConnection.write(block)
        clientConnection.disconnectFromHost()

    # connect to the other end of the line
    def setupConnection(self):
        # Attempts to make a connection to hostName on the given port.
        # The protocol parameter can be used to specify which network protocol to use (eg. IPv4 or IPv6).
        self.tcpSocket.connectToHost(self.hostLineEdit.text(),
                                     int(self.portLineEdit.text()))

    def newClient(self):
        self.tcpSocket = self.tcpServer.nextPendingConnection()
        self.tcpSocket.readyRead.connect(self.readMessage)
        print "new client detected"

    def readMessage(self):
        print "Received message, beginning to print"

        # Constructs a data stream that uses the I/O device d.
        instr = QtCore.QDataStream(self.tcpSocket)
        instr.setVersion(QtCore.QDataStream.Qt_4_0)


        # if we haven't read anything yet from the server and size is not set
        if self.blockSize == 0:
            # the first two bytes are reserved for the size of the payload.
            # must check it is at least that size to take in a valid payload size.
            if self.tcpSocket.bytesAvailable() < 2:
                return

            # read the size of the byte array payload from server
            self.blockSize = instr.readUInt16()

        # the data is incomplete so we return until the data is good
        if self.tcpSocket.bytesAvailable() < self.blockSize:
            return

        # read the data from the datastream
        msg = instr.readQString()
        instr.read
        print msg
        self.blockSize = 0  # reset the block size for next msg to default


if __name__ == '__main__':
    import sys

    app = QtGui.QApplication(sys.argv)
    server = Server()
    random.seed(None)
    sys.exit(server.exec_())
