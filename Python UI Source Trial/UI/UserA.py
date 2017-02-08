# initially will become the server
from PyQt4 import QtGui

import SocketServer
import threading
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
        if current_text != "":
            text += current_text
            self.textBrowser.setText(text + "\n")
            
            # keep the scroll bar locked to the bottom
            self.textBrowser.verticalScrollBar()    \
                .setValue(self.textBrowser.verticalScrollBar().maximum())
                
    # take in message
    # update the text area

    def handle(self):
        # self.request is the TCP socket connected to the client
        self.data = self.request.recv(1024).strip()
        print self.data
        # update text area with msg
        text = self.textBrowser.toPlainText()   # inherited from TextArea
        
        if(self.data != ""):
            text += self.data
            self.textBrowser.setText(text + "\n")
            
            # keep the scroll bar locked to the bottom
            self.textBrowser.verticalScrollBar()    \
            .setValue(self.textBrowser.verticalScrollBar().maximum())
 
class MyTCPHandler(SocketServer.BaseRequestHandler):
    """
    The request handler class for our server.

    It is instantiated once per connection to the server, and must
    override the handle() method to implement communication to the
    client.
    """
 
    def handle(self):
        # self.request is the TCP socket connected to the client
        self.data = self.request.recv(1024).strip()
        print "{} wrote:".format(self.client_address[0])
        print self.data
        # just send back the same data, but upper-cased
        self.request.sendall(self.data.upper())

class ThreadedTCPServer(SocketServer.ThreadingMixIn, SocketServer.TCPServer):
    pass
        
# main method
if __name__ == "__main__":
    
#    #TCP setup
    HOST, PORT = "localhost", 14022

    server = ThreadedTCPServer((HOST, PORT), MyTCPHandler)
    ip, port = server.server_address

    # Start a thread with the server -- that thread will then start one
    # more thread for each request
    server_thread = threading.Thread(target=server.serve_forever)
    # Exit the server thread when the main thread terminates
    server_thread.daemon = True
    server_thread.start()
 
    app = QtGui.QApplication(sys.argv)
    form = MainDialog()
    form.show()
    app.exec_()