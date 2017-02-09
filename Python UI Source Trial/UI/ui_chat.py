# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'ChatUI.ui'
#
# Created by: PyQt4 UI code generator 4.11.4
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    def _fromUtf8(s):
        return s

try:
    _encoding = QtGui.QApplication.UnicodeUTF8
    def _translate(context, text, disambig):
        return QtGui.QApplication.translate(context, text, disambig, _encoding)
except AttributeError:
    def _translate(context, text, disambig):
        return QtGui.QApplication.translate(context, text, disambig)

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        MainWindow.setObjectName(_fromUtf8("MainWindow"))
        MainWindow.resize(550, 275)
        self.centralwidget = QtGui.QWidget(MainWindow)
        self.centralwidget.setObjectName(_fromUtf8("centralwidget"))
        self.textBrowser = QtGui.QTextBrowser(self.centralwidget)
        self.textBrowser.setGeometry(QtCore.QRect(20, 10, 361, 192))
        self.textBrowser.setObjectName(_fromUtf8("textBrowser"))
        self.lineEdit = QtGui.QLineEdit(self.centralwidget)
        self.lineEdit.setGeometry(QtCore.QRect(21, 211, 361, 20))
        self.lineEdit.setObjectName(_fromUtf8("lineEdit"))
        self.pushButton_2 = QtGui.QPushButton(self.centralwidget)
        self.pushButton_2.setGeometry(QtCore.QRect(464, 210, 75, 23))
        self.pushButton_2.setObjectName(_fromUtf8("pushButton_2"))
        self.pushButton = QtGui.QPushButton(self.centralwidget)
        self.pushButton.setGeometry(QtCore.QRect(383, 210, 75, 23))
        self.pushButton.setObjectName(_fromUtf8("pushButton"))
        self.groupBox = QtGui.QGroupBox(self.centralwidget)
        self.groupBox.setGeometry(QtCore.QRect(390, 10, 151, 121))
        self.groupBox.setObjectName(_fromUtf8("groupBox"))
        self.label_3 = QtGui.QLabel(self.groupBox)
        self.label_3.setGeometry(QtCore.QRect(11, 21, 39, 16))
        self.label_3.setObjectName(_fromUtf8("label_3"))
        self.lineEdit_4 = QtGui.QLineEdit(self.groupBox)
        self.lineEdit_4.setGeometry(QtCore.QRect(11, 40, 129, 20))
        self.lineEdit_4.setDragEnabled(True)
        self.lineEdit_4.setReadOnly(True)
        self.lineEdit_4.setObjectName(_fromUtf8("lineEdit_4"))
        self.label_4 = QtGui.QLabel(self.groupBox)
        self.label_4.setGeometry(QtCore.QRect(11, 66, 20, 16))
        self.label_4.setObjectName(_fromUtf8("label_4"))
        self.lineEdit_5 = QtGui.QLineEdit(self.groupBox)
        self.lineEdit_5.setGeometry(QtCore.QRect(11, 85, 129, 20))
        self.lineEdit_5.setDragEnabled(True)
        self.lineEdit_5.setReadOnly(True)
        self.lineEdit_5.setObjectName(_fromUtf8("lineEdit_5"))
        self.label_3.raise_()
        self.textBrowser.raise_()
        self.lineEdit.raise_()
        self.pushButton_2.raise_()
        self.pushButton.raise_()
        self.label_4.raise_()
        self.label_3.raise_()
        self.groupBox.raise_()
        MainWindow.setCentralWidget(self.centralwidget)
        self.menuBar = QtGui.QMenuBar(MainWindow)
        self.menuBar.setGeometry(QtCore.QRect(0, 0, 550, 21))
        self.menuBar.setObjectName(_fromUtf8("menuBar"))
        self.menuMenu = QtGui.QMenu(self.menuBar)
        self.menuMenu.setObjectName(_fromUtf8("menuMenu"))
        MainWindow.setMenuBar(self.menuBar)
        self.statusBar = QtGui.QStatusBar(MainWindow)
        self.statusBar.setObjectName(_fromUtf8("statusBar"))
        MainWindow.setStatusBar(self.statusBar)
        self.actionLogout = QtGui.QAction(MainWindow)
        self.actionLogout.setObjectName(_fromUtf8("actionLogout"))
        self.actionSave = QtGui.QAction(MainWindow)
        self.actionSave.setObjectName(_fromUtf8("actionSave"))
        self.actionConnect = QtGui.QAction(MainWindow)
        self.actionConnect.setObjectName(_fromUtf8("actionConnect"))
        self.menuMenu.addAction(self.actionConnect)
        self.menuBar.addAction(self.menuMenu.menuAction())

        self.retranslateUi(MainWindow)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    def retranslateUi(self, MainWindow):
        MainWindow.setWindowTitle(_translate("MainWindow", "MainWindow", None))
        self.pushButton_2.setText(_translate("MainWindow", "Attach", None))
        self.pushButton.setText(_translate("MainWindow", "Send", None))
        self.groupBox.setTitle(_translate("MainWindow", "User Info", None))
        self.label_3.setText(_translate("MainWindow", "Address", None))
        self.lineEdit_4.setText(_translate("MainWindow", "localhost", None))
        self.label_4.setText(_translate("MainWindow", "Port", None))
        self.menuMenu.setTitle(_translate("MainWindow", "Menu", None))
        self.actionLogout.setText(_translate("MainWindow", "Logout", None))
        self.actionSave.setText(_translate("MainWindow", "Save", None))
        self.actionConnect.setText(_translate("MainWindow", "Connect", None))

