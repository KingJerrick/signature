# DEBUG = True
DEBUG = False
version = "v2.3.1_Beta"        #版本号在此修改

import numpy as np
import ui.ui_mainwindow
import os
from PyQt5.QtWidgets import QMainWindow, QApplication, QFileDialog, QTextEdit, QLabel, QGridLayout,QWidget,QSlider,QSpinBox
from PyQt5.QtCore import QTimer, Qt, QObject, pyqtSignal,QThread,QUrl
from PIL import Image
from PyQt5 import QtGui
from PyQt5.QtGui import QPixmap, QImage,QDesktopServices,QColor
import slot.Custom_Widgets as CS
import slot.utils as UT
from datetime import datetime
import time
import slot.utils
import colorsys
import threading
import time
from PyQt5.QtCore import QObject, pyqtSignal


class MainwindowAct(QWidget,ui.ui_mainwindow.Ui_Form):
    def __init__(self):
        super(MainwindowAct, self).__init__()

        self.setupUi(self)

        layout = self.widget.parent().layout()    ###替换控件
        index = layout.indexOf(self.widget)
        layout.removeWidget(self.widget)
        self.widget.deleteLater()
        self.widget = CS.ColorPickerWidget(self)
        layout.insertWidget(index, self.widget)   ###替换控件 

        self._updating = False  # 防止循环更新

        # 绑定每组 slider-spinbox
        self.link_slider_spinbox("R")
        self.link_slider_spinbox("G")
        self.link_slider_spinbox("B")
        self.link_slider_spinbox("H")
        self.link_slider_spinbox("S")
        self.link_slider_spinbox("V")

        # RGB -> HSV
        self.spinBox_R.valueChanged.connect(self.update_from_rgb)
        self.spinBox_G.valueChanged.connect(self.update_from_rgb)
        self.spinBox_B.valueChanged.connect(self.update_from_rgb)

        # HSV -> RGB
        self.spinBox_H.valueChanged.connect(self.update_from_hsv)
        self.spinBox_S.valueChanged.connect(self.update_from_hsv)
        self.spinBox_V.valueChanged.connect(self.update_from_hsv)
        
        self.widget.colorChanged.connect(self.update_from_color)

    def link_slider_spinbox(self, name):
        """绑定单个 Slider 和 SpinBox"""
        slider = getattr(self, f"horizontalSlider_{name}")
        spinbox = getattr(self, f"spinBox_{name}")

        spinbox.setRange(slider.minimum(), slider.maximum())

        spinbox.valueChanged.connect(lambda v: slider.setValue(v))
        slider.valueChanged.connect(lambda v: spinbox.setValue(v))

    def update_from_rgb(self):
        if self._updating:
            return
        self._updating = True

        r, g, b = self.spinBox_R.value(), self.spinBox_G.value(), self.spinBox_B.value()
        h, s, v = colorsys.rgb_to_hsv(r / 255, g / 255, b / 255)
        self.spinBox_H.setValue(int(h * 360))
        self.spinBox_S.setValue(int(s * 255))
        self.spinBox_V.setValue(int(v * 255))

        self.widget.set_rgb(r,g,b)

        self.update_preview(r, g, b)
        self._updating = False

    def update_from_hsv(self):
        if self._updating:
            return
        self._updating = True

        h, s, v = self.spinBox_H.value() / 360, self.spinBox_S.value() / 255, self.spinBox_V.value() / 255
        r, g, b = colorsys.hsv_to_rgb(h, s, v)
        self.spinBox_R.setValue(int(r * 255))
        self.spinBox_G.setValue(int(g * 255))
        self.spinBox_B.setValue(int(b * 255))

        self.widget.set_hsv(self.spinBox_H.value(),s,v)

        self.update_preview(int(r * 255), int(g * 255), int(b * 255))
        self._updating = False

    def update_preview(self, r, g, b):
        color = QColor(r, g, b)
        self.label_color.setStyleSheet(f"background-color: {color.name()};")
    
    def update_from_color(self,c):
        h, s, v, a = c.getHsv()   # h: 0-359, s/v: 0-255
        self.spinBox_H.setValue(h)
        self.spinBox_S.setValue(s)
        self.spinBox_V.setValue(v)