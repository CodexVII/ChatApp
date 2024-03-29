#!/usr/bin/env python


#############################################################################
##
## Copyright (C) 2010 Riverbank Computing Limited.
## Copyright (C) 2010 Nokia Corporation and/or its subsidiary(-ies).
## All rights reserved.
##
## This file is part of the examples of PyQt.
##
## $QT_BEGIN_LICENSE:BSD$
## You may use this file under the terms of the BSD license as follows:
##
## "Redistribution and use in source and binary forms, with or without
## modification, are permitted provided that the following conditions are
## met:
##   * Redistributions of source code must retain the above copyright
##     notice, this list of conditions and the following disclaimer.
##   * Redistributions in binary form must reproduce the above copyright
##     notice, this list of conditions and the following disclaimer in
##     the documentation and/or other materials provided with the
##     distribution.
##   * Neither the name of Nokia Corporation and its Subsidiary(-ies) nor
##     the names of its contributors may be used to endorse or promote
##     products derived from this software without specific prior written
##     permission.
##
## THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
## "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
## LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
## A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
## OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
## SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
## LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
## DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
## THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
## (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
## OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE."
## $QT_END_LICENSE$
##
#############################################################################


from PyQt4 import QtCore, QtGui, QtNetwork


class Client(QtGui.QDialog):
    def __init__(self, parent=None):
        super(Client, self).__init__(parent)

        self.blockSize = 0
        self.currentFortune = ''

        # Labels for user input
        host_label = QtGui.QLabel("&Server name:")
        port_label = QtGui.QLabel("S&erver port:")

        # naming the objects for user input
        # validation included for port
        self.hostLineEdit = QtGui.QLineEdit('localhost')
        self.portLineEdit = QtGui.QLineEdit()
        self.portLineEdit.setValidator(QtGui.QIntValidator(1, 65535, self))

        # add a corresponding input for the labels
        host_label.setBuddy(self.hostLineEdit)
        port_label.setBuddy(self.portLineEdit)

        # default label
        self.statusLabel = QtGui.QLabel("This examples requires that you run "
                                        "the Fortune Server example as well.")

        # setup the button for getting a fortune
        self.getFortuneButton = QtGui.QPushButton("Get Fortune")
        self.getFortuneButton.setDefault(True)
        self.getFortuneButton.setEnabled(False)

        # containing all the buttons within a box
        quitButton = QtGui.QPushButton("Quit")

        buttonBox = QtGui.QDialogButtonBox()
        buttonBox.addButton(self.getFortuneButton,
                            QtGui.QDialogButtonBox.ActionRole)
        buttonBox.addButton(quitButton, QtGui.QDialogButtonBox.RejectRole)

        # setting up the Qt TCP Socket and binding it to this application
        self.tcpSocket = QtNetwork.QTcpSocket(self)

        # connect signals from user input with built in functions
        self.hostLineEdit.textChanged.connect(self.enableGetFortuneButton)
        self.portLineEdit.textChanged.connect(self.enableGetFortuneButton)
        self.getFortuneButton.clicked.connect(self.requestNewFortune)
        quitButton.clicked.connect(self.close)

        # connect tcp signals with built read functions
        self.tcpSocket.readyRead.connect(self.readFortune)
        self.tcpSocket.error.connect(self.displayError)

        # UI layout
        mainLayout = QtGui.QGridLayout()
        mainLayout.addWidget(host_label, 0, 0)
        mainLayout.addWidget(self.hostLineEdit, 0, 1)
        mainLayout.addWidget(port_label, 1, 0)
        mainLayout.addWidget(self.portLineEdit, 1, 1)
        mainLayout.addWidget(self.statusLabel, 2, 0, 1, 2)
        mainLayout.addWidget(buttonBox, 3, 0, 1, 2)
        self.setLayout(mainLayout)

        self.setWindowTitle("Fortune Client")
        self.portLineEdit.setFocus()

    # Get a fortune from the server
    # While getting a fortune, disable the button itself
    # set the block size to 0
    # abort the tcp connection
    # connect to the server by using the user inputs as the parameters for HOST and PORT
    def requestNewFortune(self):

        self.getFortuneButton.setEnabled(False)
        self.blockSize = 0

        # Aborts the current connection and resets the socket.
        # Unlike disconnectFromHost(), this function immediately closes the socket,
        # discarding any pending data in the write buffer.
        self.tcpSocket.abort()

        # Attempts to make a connection to hostName on the given port.
        # The protocol parameter can be used to specify which network protocol to use (eg. IPv4 or IPv6).
        self.tcpSocket.connectToHost(self.hostLineEdit.text(),
                                     int(self.portLineEdit.text()))

    # called every time a segment is ready to be read on the TCPSocket
    # reads
    def readFortune(self):
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
        nextFortune = instr.readString()

        try:
            # Python v3.
            nextFortune = str(nextFortune, encoding='ascii')
        except TypeError:
            # Python v2.
            pass

        if nextFortune == self.currentFortune:
            QtCore.QTimer.singleShot(0, self.requestNewFortune)
            return

        self.currentFortune = nextFortune
        self.statusLabel.setText(self.currentFortune)
        self.getFortuneButton.setEnabled(True)

    def displayError(self, socketError):
        if socketError == QtNetwork.QAbstractSocket.RemoteHostClosedError:
            pass
        elif socketError == QtNetwork.QAbstractSocket.HostNotFoundError:
            QtGui.QMessageBox.information(self, "Fortune Client",
                                          "The host was not found. Please check the host name and "
                                          "port settings.")
        elif socketError == QtNetwork.QAbstractSocket.ConnectionRefusedError:
            QtGui.QMessageBox.information(self, "Fortune Client",
                                          "The connection was refused by the peer. Make sure the "
                                          "fortune server is running, and check that the host name "
                                          "and port settings are correct.")
        else:
            QtGui.QMessageBox.information(self, "Fortune Client",
                                          "The following error occurred: %s." % self.tcpSocket.errorString())

        self.getFortuneButton.setEnabled(True)

    def enableGetFortuneButton(self):
        self.getFortuneButton.setEnabled(bool(self.hostLineEdit.text() and
                                              self.portLineEdit.text()))


if __name__ == '__main__':
    import sys

    app = QtGui.QApplication(sys.argv)
    client = Client()
    client.show()
    sys.exit(client.exec_())
