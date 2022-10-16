# This Python file uses the following encoding: utf-8
import sys
import os
import time
import traceback


from PySide2.QtWidgets import*
from PySide2.QtCore import *
from PySide2.QtUiTools import QUiLoader
from PySide2.QtGui import *

import aoi
import cnc


class ThreadSignals(QObject):
    init_prog = Signal(object)
    Images = Signal(object)
    start_scan = Signal(object)

class THT_Thread(QThread):                          
    def __init__(self, parent = None):
        super(THT_Thread, self).__init__(parent)
        self.signals = ThreadSignals()
        self.scan = False
        self.exit = False
        self.pcb_size = []

    def scan_pcb(self,s):
        self.pcb_size = s
        self.scan = True
    
    def exit(self):
        self.exit = True

    def run(self):            
        cnc.init()
        self.signals.init_prog.emit(50)
        self.data = aoi.data_init()
        print(self.data.class_names)
        self.signals.init_prog.emit(70)
        self.model = aoi.model_init(self.data)
        self.signals.init_prog.emit(100)

        while(1):
            if(self.scan == True):
                self.scan = False
                self.Images = cnc.scan(self.model,self.data,self.pcb_size)
                #self.Images = cnc.load_images_from_folder("Images", self.model,self.data)
                self.signals.Images.emit(self.Images)

            if(self.exit == True):
                self.exit = False
                break
            


class Main(QMainWindow):
    def __init__(self):
        super(Main, self).__init__()
        self.load_ui()

        self.TAB = self.findChild(QTabWidget, 'TAB')
        self.THT_SW=self.findChild(QStackedWidget, 'THT_SW')
        self.LAB_SW=self.findChild(QStackedWidget, 'LAB_SW')
        self.PROG_THT = self.findChild(QProgressBar, 'PROG_THT')
        self.THT_PREV = self.findChild(QLabel, 'THT_PREV')

        self.SOL_GOOD = self.findChild(QLabel, 'SOL_GOOD')
        self.SOL_BAD = self.findChild(QLabel, 'SOL_BAD')
        self.SOL_NOT = self.findChild(QLabel, 'SOL_NOT')
        self.SOL_BALL = self.findChild(QLabel, 'SOL_BALL')

        self.PCB_H = self.findChild(QLineEdit, 'PCB_H')
        self.PCB_W = self.findChild(QLineEdit, 'PCB_W')

        self.TAB.setCurrentIndex(0)
        self.TAB.currentChanged.connect(self.onTabChange) #changed!
        self.THT_SW.setCurrentIndex(0)

        self.THT_Scan = self.findChild(QPushButton, 'THT_Scan')
        self.THT_Scan.clicked.connect(self.ScanPress)

        #Multi_Thread
        self.main_signals = ThreadSignals()
        self.tht_thread = THT_Thread()
        self.tht_thread.signals.init_prog.connect(self.set_prog_THT)
        self.main_signals.start_scan.connect(self.tht_thread.scan_pcb)
        self.tht_thread.signals.Images.connect(self.cnc_images_loaded)

        t = QTimer(self)
        t.singleShot(2000,self.tab_init)

    def load_ui(self):
        loader = QUiLoader()
        path = os.path.join(os.path.dirname(__file__), "form.ui")
        ui_file = QFile(path)
        ui_file.open(QFile.ReadOnly)
        loader.load(ui_file, self).show()
        ui_file.close()

    def tab_init(self):
        self.THT_SW.setCurrentIndex(0)
        self.PROG_THT.setValue(0)
        self.tht_thread.start()

    def set_prog_THT(self,s):
        self.PROG_THT.setValue(s)
        if(s == 100):
            self.THT_SW.setCurrentIndex(1)

    def ScanPress(self):
        pcb_size = [int(self.PCB_W.text()),int(self.PCB_H.text())]
        self.main_signals.start_scan.emit(pcb_size)


    def cnc_images_loaded(self,data):
        images,no_steps,pad_cnts = data
        width = self.THT_PREV.frameGeometry().width()
        height = self.THT_PREV.frameGeometry().height()
        print(width,height)
        comb_img = cnc.combine(no_steps,images,width,height)
        height, width, channel = comb_img.shape
        bytesPerLine = 3 * width
        qImg = QImage(comb_img.data, width, height, bytesPerLine, QImage.Format_RGB888)
        pixmap01 = QPixmap.fromImage(qImg)
        self.THT_PREV.setPixmap(pixmap01)

        tot_pad_cnt = [0,0,0,0]
        for i in range(0,len(pad_cnts)):
            pad_cnt = pad_cnts[i]
            for j in range(0,4):
                tot_pad_cnt[j] = pad_cnt[j] + tot_pad_cnt[j]
        self.SOL_GOOD.setText(str(tot_pad_cnt[0]))
        self.SOL_BAD.setText(str(tot_pad_cnt[1]))
        self.SOL_NOT.setText(str(tot_pad_cnt[2]))
        self.SOL_BALL.setText(str(tot_pad_cnt[3]))



    def onTabChange(self,i): #changed!
        if(i==0):
            self.THT_SW.setCurrentIndex(0)
            self.PROG_THT = self.findChild(QProgressBar, 'PROG_THT')
            for i in range(0,100):
                self.PROG_THT.setValue(i)
                time.sleep(0.1)
            self.THT_SW.setCurrentIndex(1)

        if(i==1):
            self.LAB_SW.setCurrentIndex(0)
            self.PROG_LAB = self.findChild(QProgressBar, 'PROG_LAB')
            for i in range(0,100):
                self.PROG_LAB.setValue(i)
                time.sleep(0.1)
            self.LAB_SW.setCurrentIndex(1)




if __name__ == "__main__":
    app = QApplication([])
    widget = Main()
    sys.exit(app.exec_())
    print('test')


