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
        MainWindow.resize(555, 275)
        self.centralwidget = QtGui.QWidget(MainWindow)
        self.centralwidget.setObjectName(_fromUtf8("centralwidget"))
        self.listWidget = QtGui.QListWidget(self.centralwidget)
        self.listWidget.setGeometry(QtCore.QRect(427, 10, 111, 192))
        self.listWidget.setObjectName(_fromUtf8("listWidget"))
        item = QtGui.QListWidgetItem()
        self.listWidget.addItem(item)
        item = QtGui.QListWidgetItem()
        self.listWidget.addItem(item)
        item = QtGui.QListWidgetItem()
        self.listWidget.addItem(item)
        self.textBrowser = QtGui.QTextBrowser(self.centralwidget)
        self.textBrowser.setGeometry(QtCore.QRect(20, 10, 401, 192))
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
        MainWindow.setCentralWidget(self.centralwidget)
        self.menuBar = QtGui.QMenuBar(MainWindow)
        self.menuBar.setGeometry(QtCore.QRect(0, 0, 555, 21))
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
        __sortingEnabled = self.listWidget.isSortingEnabled()
        self.listWidget.setSortingEnabled(False)
        item = self.listWidget.item(0)
        item.setText(_translate("MainWindow", "Cian", None))
        item = self.listWidget.item(1)
        item.setText(_translate("MainWindow", "Ian", None))
        item = self.listWidget.item(2)
        item.setText(_translate("MainWindow", "Mark", None))
        self.listWidget.setSortingEnabled(__sortingEnabled)
        self.pushButton_2.setText(_translate("MainWindow", "Attach", None))
        self.pushButton.setText(_translate("MainWindow", "Send", None))
        self.menuMenu.setTitle(_translate("MainWindow", "Menu", None))
        self.actionLogout.setText(_translate("MainWindow", "Logout", None))
        self.actionSave.setText(_translate("MainWindow", "Save", None))
        self.actionConnect.setText(_translate("MainWindow", "Connect", None))

