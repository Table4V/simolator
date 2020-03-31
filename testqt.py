# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'testqt.ui'
#
# Created by: PyQt5 UI code generator 5.13.0
#
# WARNING! All changes made in this file will be lost!


from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtGui import QRegExpValidator
from PyQt5.QtCore import pyqtSignal, pyqtSlot, QRegExp
import Translator
import webbrowser
import os
import subprocess

page_size_options = {'0 Bare': [], '1 SV32(RV32)': ['4Kb', '4Mb'], '8 SV39(RV64)': ['4Kb', '2Mb', '1Gb'], '9 SV48(RV64)': ['4Kb', '2Mb', '1Gb', '512Gb']}
translator_mode_options = {'0 Bare': 0, '1 SV32(RV32)': 32, '8 SV39(RV64)': 39, '9 SV48(RV64)': 48}

class RemoveButton(QtWidgets.QPushButton):
    def __init__(self, label, row):
        super(RemoveButton, self).__init__(label)
        self.row = row

    def setrow(self, row):
        self.row = row

    remove_clicked = pyqtSignal(int)

    @pyqtSlot()
    def tmpSlot(self):
        self.remove_clicked.emit(self.row)


class Ui_MainWindow(object):
    translation_writer = Translator.Interface()

    def removeFiles(self):
        if(os.path.exists(os.path.abspath('gui_output.xml'))):
            os.remove(os.path.abspath('gui_output.xml'))
        if(os.path.exists(os.path.abspath('translator_output.xml'))):
            os.remove(os.path.abspath('translator_output.xml'))

    def createXMLForTranslation(self):
        translator = Translator.Translator()
        translator.clear()
        ppn = 0 if not self.satp_ppn.text() else int(self.satp_ppn.text(), 16)
        ppnIsEmpty = True if not self.satp_ppn.text() else False
        mode = translator_mode_options[self.modeSelect.currentText()]
        translator.satp = Translator.SATP(mode=mode, ppn=ppn, ppn_isEmpty=ppnIsEmpty)
        for row in range(0, self.tableWidget.rowCount()):
            va = 0 if not self.tableWidget.cellWidget(row, 1).text() else int(self.tableWidget.cellWidget(row, 1).text() ,16)
            vaIsEmpty = True if not self.tableWidget.cellWidget(row, 1).text() else False
            vaObj = Translator.VA(data=va, mode=mode)
            vaObj.isEmpty = vaIsEmpty
            tw = Translator.TranslationWalk(mode=mode, pageSize=self.tableWidget.cellWidget(row, 0).currentText()[:-1], va=vaObj, ptes=[])
            for pte in range(2, 6):
                if(self.tableWidget.cellWidget(row, pte).isEnabled()):
                    currentPTE = Translator.PTE(mode=mode)
                    addr = 0 if not self.tableWidget.cellWidget(row, pte).children()[1].text() else int(self.tableWidget.cellWidget(row, pte).children()[1].text(), 16)
                    addIsEmpty = True # if not self.tableWidget.cellWidget(row, pte).children()[1].text() else False
                    data = 0 if not self.tableWidget.cellWidget(row, pte).children()[2].text() else int(self.tableWidget.cellWidget(row, pte).children()[2].text(), 16)
                    dataIsEmpty = True #if not self.tableWidget.cellWidget(row, pte).children()[2].text() else False
                    currentPTE.isAddrEmpty = addIsEmpty
                    currentPTE.isDataEmpty = dataIsEmpty
                    currentPTE.set(5-pte, addr, data, mode=mode)
                    tw.ptes.append(currentPTE)
            pa = 0 if not self.tableWidget.cellWidget(row, 6).text() else int(self.tableWidget.cellWidget(row, 6).text() ,16)
            paIsEmpty = True if not self.tableWidget.cellWidget(row, 6).text() else False
            tw.pa = Translator.PA(data=pa, mode=mode)
            tw.pa.isEmpty = paIsEmpty
            translator.translationWalks.append(tw)
        self.translation_writer.save_file(translator, 'gui_output.xml')
        print("Created XML for Translation by GUI")

    def executeTranslator(self):
        command = 'python TransBuilder.py gui_output.xml translator_output.xml'
        os.system(command)
        print("Executed Translator by GUI")


    def readXMLFromTranslation(self):
        translator = Translator.Translator()
        translator.clear()
        self.translation_writer.load_file(translator, 'translator_output.xml')
        if not translator.satp.ppn_isEmpty: # ugl code, but I'm tired
            self.satp_ppn.setText(hex(translator.satp.ppn)[2:])
        else:
            self.satp_ppn.setText("")
        row_counter=0 # to match translationWalk to row
        for tw in translator.translationWalks:
            if not tw.va.isEmpty: # set the VA
                self.tableWidget.cellWidget(row_counter, 1).setText(hex(tw.va.data())[2:])
            else:
                self.tableWidget.cellWidget(row_counter, 1).setText("")
            for pte in tw.ptes: # printing the PTES
                if not pte:
                    continue
                level = pte.level # 0-3
                if not pte.isAddrEmpty: # read PTE Address
                    self.tableWidget.cellWidget(row_counter, 5-level).children()[1].setText(hex(pte.address)[2:])
                else:
                    self.tableWidget.cellWidget(row_counter, 5-level).children()[1].setText("")
                if not pte.isDataEmpty: # read PTE data
                    self.tableWidget.cellWidget(row_counter, 5-level).children()[2].setText(hex(pte.data())[2:])
                else:
                    self.tableWidget.cellWidget(row_counter, 5-level).children()[2].setText("")
            if not tw.pa.isEmpty: # set the PA
                self.tableWidget.cellWidget(row_counter, 6).setText("%X" % tw.pa.data())
            else:
                self.tableWidget.cellWidget(row_counter, 6).setText("")
            row_counter+=1



    def handlePlayButtonPressed(self):
        print("Removing old files")
        self.removeFiles()
        print("Create XML for Translation")
        self.createXMLForTranslation()
        print("Executing Translator")
        self.executeTranslator()
        print("Reading XML")
        self.readXMLFromTranslation()
        print("Tables rebuild completed!")

    def addRow(self):
        self.tableWidget.insertRow(self.tableWidget.rowCount())
        ps = QtWidgets.QComboBox()
        ps.insertItems(0, page_size_options[ui.modeSelect.currentText()])
        ps.currentIndexChanged['QString'].connect(self.updateTableByMode)
        row = self.tableWidget.rowCount() - 1
        self.tableWidget.setCellWidget(row , 0, ps)
        rm = RemoveButton('X', row)
        self.tableWidget.setCellWidget(row, 7, rm)
        rm.remove_clicked.connect(self.rmRow)
        rm.clicked.connect(rm.tmpSlot)
        for c in range(1,7):
            addr = QtWidgets.QLineEdit()
            rx = QRegExp('[A-Fa-f0-9]*')
            validator = QRegExpValidator(rx, addr)
            addr.setValidator(validator)
            if c in range(2, 6):
                cellWidget = QtWidgets.QWidget()
                layout = QtWidgets.QVBoxLayout()
                layout.setContentsMargins(0, 0, 0, 0)
                layout.setSpacing(0)
                data = QtWidgets.QLineEdit()
                validator = QRegExpValidator(rx, data)
                data.setValidator(validator)
                layout.addWidget(addr)
                layout.addWidget(data)
                cellWidget.setLayout(layout)
                self.tableWidget.setCellWidget(row, c, cellWidget)
            else:
                self.tableWidget.setCellWidget(row, c, addr)
        self.updateTableByMode(self.modeSelect.currentText)
        self.tableWidget.resizeRowsToContents()

    def rmRow(self, row):
        # print(row)
        self.tableWidget.removeRow(row)
        for row in range(0, self.tableWidget.rowCount()):
            self.tableWidget.cellWidget(row, 7).setrow(row)

    def modeChanged(self, text):
        self.updateModeSelect(text)
        self.updateTableByMode(text)

    def updateModeSelect(self, text):
        if text in ('0 Bare', '1 SV32(RV32)') :
            self.mode_bit_0.setText('31')
            self.mode_bit_1.setText('31')
            self.mode_size.setText('1')
            self.asid_bit_0.setText('30')
            self.asid_bit_1.setText('22')
            self.asid_size.setText('9')
            self.ppn_bit_0.setText('21')
            self.ppn_bit_1.setText('0')
            self.ppn_size.setText('22')
        else:
            self.mode_bit_0.setText('63')
            self.mode_bit_1.setText('60')
            self.mode_size.setText('4')
            self.asid_bit_0.setText('59')
            self.asid_bit_1.setText('44')
            self.asid_size.setText('16')
            self.ppn_bit_0.setText('43')
            self.ppn_bit_1.setText('0')
            self.ppn_size.setText('44')
        for row in range(self.tableWidget.rowCount()):
            for i in range(self.tableWidget.cellWidget(row, 0).count()):
                self.tableWidget.cellWidget(row, 0).removeItem(0)
            self.tableWidget.cellWidget(row, 0).insertItems(0, page_size_options[ui.modeSelect.currentText()])

    def updateTableByMode(self, text):
        dis = {'0 Bare ': [0, 2, 3, 4, 5],
               '1 SV32(RV32) 4Kb' : [2, 3],
               '1 SV32(RV32) 4Mb' : [2, 3, 5],
               '8 SV39(RV64) 4Kb' : [2],
               '8 SV39(RV64) 2Mb' : [2, 5],
               '8 SV39(RV64) 1Gb' : [2, 4, 5],
               '9 SV48(RV64) 4Kb' : [],
               '9 SV48(RV64) 2Mb' : [5],
               '9 SV48(RV64) 1Gb' : [4, 5],
               '9 SV48(RV64) 512Gb' : [3, 4, 5]
               }
        en = {'0 Bare ': [1],
               '1 SV32(RV32) 4Kb': [0, 1, 4, 5],
               '1 SV32(RV32) 4Mb': [0, 1, 4],
               '8 SV39(RV64) 4Kb': [0, 1, 3, 4, 5],
               '8 SV39(RV64) 2Mb': [0, 1, 3, 4],
               '8 SV39(RV64) 1Gb': [0, 1, 3],
               '9 SV48(RV64) 4Kb': [0, 1, 2, 3, 4, 5],
               '9 SV48(RV64) 2Mb': [0, 1, 2, 3, 4],
               '9 SV48(RV64) 1Gb': [0, 1, 2, 3],
               '9 SV48(RV64) 512Gb': [0, 1, 2]
               }
        for row in range(0, self.tableWidget.rowCount()):
            key = self.modeSelect.currentText() + ' ' + self.tableWidget.cellWidget(row, 0).currentText()
            if key in dis.keys():
               for cl in dis[key]:
                  self.tableWidget.cellWidget(row, cl).setEnabled(False)
            if key in en.keys():
               for cl in en[key]:
                  self.tableWidget.cellWidget(row, cl).setEnabled(True)


    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(1238, 907)
        self.centralwidget = QtWidgets.QWidget(MainWindow)
        self.centralwidget.setObjectName("centralwidget")
        self.frame = QtWidgets.QFrame(self.centralwidget)
        self.frame.setGeometry(QtCore.QRect(70, 0, 871, 131))
        self.frame.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.frame.setFrameShadow(QtWidgets.QFrame.Raised)
        self.frame.setObjectName("frame")
        self.layoutWidget = QtWidgets.QWidget(self.frame)
        self.layoutWidget.setGeometry(QtCore.QRect(20, 12, 791, 61))
        self.layoutWidget.setObjectName("layoutWidget")
        self.horizontalLayout_6 = QtWidgets.QHBoxLayout(self.layoutWidget)
        self.horizontalLayout_6.setContentsMargins(0, 0, 0, 0)
        self.horizontalLayout_6.setObjectName("horizontalLayout_6")
        self.label = QtWidgets.QLabel(self.layoutWidget)
        font = QtGui.QFont()
        font.setPointSize(14)
        font.setBold(True)
        font.setWeight(75)
        self.label.setFont(font)
        self.label.setObjectName("label")
        self.horizontalLayout_6.addWidget(self.label)
        self.horizontalLayout_5 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_5.setSpacing(0)
        self.horizontalLayout_5.setObjectName("horizontalLayout_5")
        self.verticalLayout_2 = QtWidgets.QVBoxLayout()
        self.verticalLayout_2.setSpacing(0)
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        self.horizontalLayout_2 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        self.mode_bit_0 = QtWidgets.QLabel(self.layoutWidget)
        font = QtGui.QFont()
        font.setBold(True)
        font.setWeight(75)
        self.mode_bit_0.setFont(font)
        self.mode_bit_0.setObjectName("mode_bit_0")
        self.horizontalLayout_2.addWidget(self.mode_bit_0)
        self.mode_bit_1 = QtWidgets.QLabel(self.layoutWidget)
        font = QtGui.QFont()
        font.setBold(True)
        font.setWeight(75)
        self.mode_bit_1.setFont(font)
        self.mode_bit_1.setAlignment(QtCore.Qt.AlignRight|QtCore.Qt.AlignTrailing|QtCore.Qt.AlignVCenter)
        self.mode_bit_1.setObjectName("mode_bit_1")
        self.horizontalLayout_2.addWidget(self.mode_bit_1)
        self.verticalLayout_2.addLayout(self.horizontalLayout_2)
        self.modeSelect = QtWidgets.QComboBox(self.layoutWidget)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(1)
        sizePolicy.setHeightForWidth(self.modeSelect.sizePolicy().hasHeightForWidth())
        self.modeSelect.setSizePolicy(sizePolicy)
        self.modeSelect.setObjectName("modeSelect")
        self.modeSelect.insertItems(0, ('0 Bare', '1 SV32(RV32)', '8 SV39(RV64)', '9 SV48(RV64)'))
        self.modeSelect.setCurrentIndex(1)
        self.verticalLayout_2.addWidget(self.modeSelect)
        self.mode_size = QtWidgets.QLabel(self.layoutWidget)
        font = QtGui.QFont()
        font.setBold(True)
        font.setWeight(75)
        self.mode_size.setFont(font)
        self.mode_size.setAlignment(QtCore.Qt.AlignCenter)
        self.mode_size.setObjectName("mode_size")
        self.verticalLayout_2.addWidget(self.mode_size)
        self.horizontalLayout_5.addLayout(self.verticalLayout_2)
        self.verticalLayout_3 = QtWidgets.QVBoxLayout()
        self.verticalLayout_3.setSpacing(0)
        self.verticalLayout_3.setObjectName("verticalLayout_3")
        self.horizontalLayout_3 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_3.setObjectName("horizontalLayout_3")
        self.asid_bit_0 = QtWidgets.QLabel(self.layoutWidget)
        font = QtGui.QFont()
        font.setBold(True)
        font.setWeight(75)
        self.asid_bit_0.setFont(font)
        self.asid_bit_0.setObjectName("asid_bit_0")
        self.horizontalLayout_3.addWidget(self.asid_bit_0)
        self.asid_bit_1 = QtWidgets.QLabel(self.layoutWidget)
        font = QtGui.QFont()
        font.setBold(True)
        font.setWeight(75)
        self.asid_bit_1.setFont(font)
        self.asid_bit_1.setAlignment(QtCore.Qt.AlignRight|QtCore.Qt.AlignTrailing|QtCore.Qt.AlignVCenter)
        self.asid_bit_1.setObjectName("asid_bit_1")
        self.horizontalLayout_3.addWidget(self.asid_bit_1)
        self.verticalLayout_3.addLayout(self.horizontalLayout_3)
        self.satp_asid = QtWidgets.QLineEdit(self.layoutWidget)
        self.satp_asid.setEnabled(False)
        self.satp_asid.setObjectName("satp_asid")
        self.satp_asid.setSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        self.verticalLayout_3.addWidget(self.satp_asid)
        self.asid_size = QtWidgets.QLabel(self.layoutWidget)
        font = QtGui.QFont()
        font.setBold(True)
        font.setWeight(75)
        self.asid_size.setFont(font)
        self.asid_size.setAlignment(QtCore.Qt.AlignCenter)
        self.asid_size.setObjectName("asid_size")
        self.verticalLayout_3.addWidget(self.asid_size)
        self.horizontalLayout_5.addLayout(self.verticalLayout_3)
        self.verticalLayout_4 = QtWidgets.QVBoxLayout()
        self.verticalLayout_4.setSpacing(0)
        self.verticalLayout_4.setObjectName("verticalLayout_4")
        self.horizontalLayout_4 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_4.setObjectName("horizontalLayout_4")
        self.ppn_bit_0 = QtWidgets.QLabel(self.layoutWidget)
        font = QtGui.QFont()
        font.setBold(True)
        font.setWeight(75)
        self.ppn_bit_0.setFont(font)
        self.ppn_bit_0.setObjectName("ppn_bit_0")
        self.horizontalLayout_4.addWidget(self.ppn_bit_0)
        self.ppn_bit_1 = QtWidgets.QLabel(self.layoutWidget)
        font = QtGui.QFont()
        font.setBold(True)
        font.setWeight(75)
        self.ppn_bit_1.setFont(font)
        self.ppn_bit_1.setAlignment(QtCore.Qt.AlignRight|QtCore.Qt.AlignTrailing|QtCore.Qt.AlignVCenter)
        self.ppn_bit_1.setObjectName("ppn_bit_1")
        self.horizontalLayout_4.addWidget(self.ppn_bit_1)
        self.verticalLayout_4.addLayout(self.horizontalLayout_4)
        self.satp_ppn = QtWidgets.QLineEdit(self.layoutWidget)
        self.satp_ppn.setObjectName("satp_ppn")
        self.satp_ppn.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        ppn_rx = QRegExp('[A-Fa-f0-9]*')
        ppn_validator = QRegExpValidator(ppn_rx, self.satp_ppn)
        self.satp_ppn.setValidator(ppn_validator)
        self.verticalLayout_4.addWidget(self.satp_ppn)
        self.ppn_size = QtWidgets.QLabel(self.layoutWidget)
        font = QtGui.QFont()
        font.setBold(True)
        font.setWeight(75)
        self.ppn_size.setFont(font)
        self.ppn_size.setAlignment(QtCore.Qt.AlignCenter)
        self.ppn_size.setObjectName("ppn_size")
        self.verticalLayout_4.addWidget(self.ppn_size)
        self.horizontalLayout_5.addLayout(self.verticalLayout_4)
        self.horizontalLayout_6.addLayout(self.horizontalLayout_5)
        self.playButton = QtWidgets.QPushButton(self.layoutWidget)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.playButton.sizePolicy().hasHeightForWidth())
        self.playButton.setSizePolicy(sizePolicy)
        self.playButton.setObjectName("playButton")
        self.playButton.setStyleSheet('border: none')
        self.horizontalLayout_6.addWidget(self.playButton)
        self.frame_2 = QtWidgets.QFrame(self.centralwidget)
        self.frame_2.setGeometry(QtCore.QRect(20, 140, 1101, 591))
        self.frame_2.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.frame_2.setFrameShadow(QtWidgets.QFrame.Raised)
        self.frame_2.setObjectName("frame_2")
        self.widget = QtWidgets.QWidget(self.frame_2)
        self.widget.setGeometry(QtCore.QRect(50, 10, 1053, 545))
        self.widget.setObjectName("widget")
        self.verticalLayout = QtWidgets.QVBoxLayout(self.widget)
        self.verticalLayout.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout.setObjectName("verticalLayout")
        self.tableWidget = QtWidgets.QTableWidget(self.widget)
        self.tableWidget.setRowCount(0)
        self.tableWidget.setColumnCount(8)
        self.tableWidget.setObjectName("tableWidget")
        self.tableWidget.horizontalHeader().setStyleSheet('border: 1px solid black')
        self.tableWidget.horizontalHeader().setStretchLastSection(True);
        self.tableWidget.setHorizontalHeaderLabels(('Page Size', 'VA', 'PTE[3]', 'PTE[2]', 'PTE[1]', 'PTE[0]', 'PA', 'Remove'))
        self.verticalLayout.addWidget(self.tableWidget)
        self.horizontalLayout = QtWidgets.QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.plusButton = QtWidgets.QPushButton(self.widget)
        font = QtGui.QFont()
        font.setPointSize(22)
        font.setBold(True)
        font.setWeight(75)
        self.plusButton.setFont(font)
        self.plusButton.setObjectName("plusButton")
        self.horizontalLayout.addWidget(self.plusButton)
        spacerItem = QtWidgets.QSpacerItem(968, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout.addItem(spacerItem)
        self.verticalLayout.addLayout(self.horizontalLayout)

        # new
        self.widget = QtWidgets.QWidget(self.centralwidget)
        self.widget.setGeometry(QtCore.QRect(20, 700, 1211, 161))
        self.widget.setObjectName("widget")
        self.horizontalLayout_19 = QtWidgets.QHBoxLayout(self.widget)
        self.horizontalLayout_19.setContentsMargins(0, 0, 0, 0)
        self.horizontalLayout_19.setObjectName("horizontalLayout_19")
        self.label_4 = QtWidgets.QLabel(self.widget)
        self.label_4.setObjectName("label_4")
        self.horizontalLayout_19.addWidget(self.label_4)
        spacerItem2 = QtWidgets.QSpacerItem(300, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout_19.addItem(spacerItem2)
        self.label_5 = QtWidgets.QLabel(self.widget)
        self.label_5.setObjectName("label_5")
        self.horizontalLayout_19.addWidget(self.label_5)
        spacerItem1 = QtWidgets.QSpacerItem(300, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout_19.addItem(spacerItem1)
        self.logoButton = QtWidgets.QPushButton(self.widget)
        self.logoButton.setObjectName("logoButton")
        self.horizontalLayout_19.addWidget(self.logoButton)
        # new

        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QtWidgets.QMenuBar(MainWindow)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 1238, 21))
        self.menubar.setObjectName("menubar")
        MainWindow.setMenuBar(self.menubar)
        self.statusbar = QtWidgets.QStatusBar(MainWindow)
        self.statusbar.setObjectName("statusbar")
        MainWindow.setStatusBar(self.statusbar)

        self.retranslateUi(MainWindow)
        self.modeSelect.currentIndexChanged['QString'].connect(self.modeChanged)
        self.plusButton.clicked.connect(self.addRow)

        # self.modeSelect.currentIndexChanged['QString'].connect(self.updateTableByMode)

        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    def retranslateUi(self, MainWindow):
        _translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(_translate("MainWindow", "MainWindow"))
        self.label.setText(_translate("MainWindow", "SATP"))
        self.mode_bit_0.setText(_translate("MainWindow", "31"))
        self.mode_bit_1.setText(_translate("MainWindow", "31"))
        self.mode_size.setText(_translate("MainWindow", "1"))
        self.asid_bit_0.setText(_translate("MainWindow", "30"))
        self.asid_bit_1.setText(_translate("MainWindow", "22"))
        self.satp_asid.setPlaceholderText(_translate("MainWindow", "ASID"))
        self.asid_size.setText(_translate("MainWindow", "9"))
        self.ppn_bit_0.setText(_translate("MainWindow", "21"))
        self.ppn_bit_1.setText(_translate("MainWindow", "0"))
        self.satp_ppn.setPlaceholderText(_translate("MainWindow", "PPN"))
        self.ppn_size.setText(_translate("MainWindow", "22"))
        pixmap = QtGui.QPixmap()
        pixmap.load(os.path.abspath('playIcon.png'))
        play_icon = QtGui.QIcon(pixmap)
        self.playButton.setIcon(play_icon)
        self.playButton.clicked.connect(self.handlePlayButtonPressed)
        self.plusButton.setText(_translate("MainWindow", "+"))
        pixmap.load(os.path.abspath('ibm_logo.png'))
        self.label_4.setPixmap(pixmap)
        pixmap.load(os.path.abspath('RiscVaddrTrans_mod.png'))
        self.label_5.setPixmap(pixmap)
        pixmap.load(os.path.abspath('Logo_name.png'))
        icon = QtGui.QIcon(pixmap)
        self.logoButton.setIcon(icon)
        self.logoButton.setIconSize(pixmap.rect().size())
        self.logoButton.clicked.connect(lambda: webbrowser.open('http://www.research.ibm.com/haifa/dept/vst/simulation_pvt.shtml'))


if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    MainWindow = QtWidgets.QMainWindow()
    ui = Ui_MainWindow()
    ui.setupUi(MainWindow)
    MainWindow.show()
    sys.exit(app.exec_())
