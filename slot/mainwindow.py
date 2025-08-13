# DEBUG = True
DEBUG = False
version = "v1.00.00"        #版本号在此修改

import numpy as np
import ui.ui_mainwindow
import ui.ui_signature
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
from PIL import Image

class signaturewindow(QWidget,ui.ui_signature.Ui_Form):
    changeSignalSignal = pyqtSignal(bool)
    SignatureSignal = pyqtSignal(object)
    def __init__(self):
        super(signaturewindow,self).__init__()
        self.setupUi(self)
        self._signature = False
        
        self.pushButton.clicked.connect(self.import_signature)


    def import_signature(self):
        file_dialog = QFileDialog()
        file_dialog.setNameFilter("Images (*.png *.xpm *.jpg *.bmp)")
        file_dialog.setViewMode(QFileDialog.Detail)
        self.path, _ = file_dialog.getOpenFileName(self, '选择图片文件', '',
                                                        'Images (*.png *.xpm *.jpg *.bmp)')
        if self.path == "":
            return
        else:
            self._signature = True
            pixmap = QtGui.QPixmap(self.path)
            img_ratio = pixmap.width() / pixmap.height()
            label_ratio = self.label_3.width() / self.label_3.height()
            if img_ratio >= label_ratio:
                pixmap = pixmap.scaled(self.label_3.width(),int(self.label_3.width()/img_ratio))
            else:
                pixmap = pixmap.scaled(int(self.label_3.height()*img_ratio),self.label_3.height())
            self.label_3.setPixmap(pixmap)

    def closeEvent(self, event):
        if self._signature:
            img = Image.open(self.path).convert("RGBA")
            self.SignatureSignal.emit(img)
            self.changeSignalSignal.emit(self._signature)


class MainwindowAct(QWidget,ui.ui_mainwindow.Ui_Form):
    def __init__(self):
        super(MainwindowAct, self).__init__()

        self.setupUi(self)
        self.signaturepage = signaturewindow()
        self.label_8.setText(f"Copyright © 2025 Jerrick Zhu, All rights reserved.    {version}")

        layout = self.widget.parent().layout()    ###替换控件
        index = layout.indexOf(self.widget)
        layout.removeWidget(self.widget)
        self.widget.deleteLater()
        self.widget = CS.ColorPickerWidget(self)
        layout.insertWidget(index, self.widget)   ###替换控件 

        self._updating = False  # 防止循环更新

        self._picture = False
        self._signature = False #确定是否导入签名和图片

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
        self.update_preview(self.spinBox_R.value(),
                            self.spinBox_G.value(),
                            self.spinBox_B.value())
        
        self.pushButton.clicked.connect(self.import_picture)
        self.pushButton_2.clicked.connect(self.import_signature)
        self.pushButton_3.clicked.connect(self.checkSignature)
        self.pushButton_4.clicked.connect(self.savePicture)
        self.pushButton_5.clicked.connect(self.close)

        self.signaturepage.changeSignalSignal.connect(lambda v:setattr(self,"_signature",v))
        self.signaturepage.SignatureSignal.connect(self.changeSignature)

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
        if self._signature:
            self.changeSignature(self.signature)

    def update_from_color(self,c):
        h, s, v, a = c.getHsv()   # h: 0-359, s/v: 0-255
        self.spinBox_H.setValue(h)
        self.spinBox_S.setValue(s)
        self.spinBox_V.setValue(v)
    
    def import_picture(self):
        file_dialog = QFileDialog()
        file_dialog.setNameFilter("Images (*.png *.xpm *.jpg *.bmp)")
        file_dialog.setViewMode(QFileDialog.Detail)
        self.path, _ = file_dialog.getOpenFileName(self, '选择图片文件', '',
                                                        'Images (*.png *.xpm *.jpg *.bmp)')
        if self.path == "":
            return
        else:
            self._picture = True
            pixmap = QtGui.QPixmap(self.path)
            img_ratio = pixmap.width() / pixmap.height()
            label_ratio = self.label_picture.width() / self.label_picture.height()
            if img_ratio >= label_ratio:
                pixmap = pixmap.scaled(self.label_picture.width(),int(self.label_picture.width()/img_ratio))
            else:
                pixmap = pixmap.scaled(int(self.label_picture.height()*img_ratio),self.label_picture.height())
            self.label_picture.setPixmap(pixmap)

    def import_signature(self):
        self.signaturepage.show()

    def changeSignature(self,signature):
        arr = np.array(signature)  # (H, W, 4)
         # 透明度通道
        alpha = arr[:, :, 3]
        mask = alpha > 0  # True = 非透明

        # 替换颜色（保留原来的 alpha）
        arr[mask, 0] = self.spinBox_R.value()
        arr[mask, 1] = self.spinBox_G.value()
        arr[mask, 2] = self.spinBox_B.value()

        self.signature = Image.fromarray(arr, "RGBA")
        data = self.signature.tobytes("raw", "RGBA")
        qimage = QImage(data, self.signature.width, self.signature.height, QImage.Format_RGBA8888)
        pixmap = QPixmap.fromImage(qimage)

        img_ratio = pixmap.width() / pixmap.height()
        label_ratio = self.label_signature.width() / self.label_signature.height()
        if img_ratio >= label_ratio:
            pixmap = pixmap.scaled(self.label_signature.width(),int(self.label_signature.width()/img_ratio))
        else:
            pixmap = pixmap.scaled(int(self.label_signature.height()*img_ratio),self.label_signature.height())
        self.label_signature.setPixmap(pixmap)


    def checkSignature(self):
        if self._picture & self._signature:
            self.picture = Image.open(self.path).convert("RGBA")

            target_height = self.picture.height // 10
            scale_ratio = target_height / self.signature.height
            target_width = int(self.signature.width * scale_ratio)
            overlay_img = self.signature.resize((target_width, target_height), Image.LANCZOS)
            
            self.picture_with_signature = self.picture.copy()
            self.picture_with_signature.paste(overlay_img, (0, self.picture.height - target_height), overlay_img)

            data = self.picture_with_signature.tobytes("raw", "RGBA")
            qimage = QImage(data, self.picture_with_signature.width, self.picture_with_signature.height, QImage.Format_RGBA8888)
            pixmap = QPixmap.fromImage(qimage)

            img_ratio = pixmap.width() / pixmap.height()
            label_ratio = self.label_picture.width() / self.label_picture.height()
            if img_ratio >= label_ratio:
                pixmap = pixmap.scaled(self.label_picture.width(),int(self.label_picture.width()/img_ratio))
            else:
                pixmap = pixmap.scaled(int(self.label_picture.height()*img_ratio),self.label_picture.height())
            self.label_picture.setPixmap(pixmap)
        
    def savePicture(self):    
        if self.picture_with_signature:
            filename = os.path.basename(self.path)  # 只取文件名（含扩展名）
            save_path, _ = QFileDialog.getSaveFileName(self, '保存图片文件', f'S{filename}', 'Images (*.png *.xpm *.jpg *.bmp)')
            if save_path == "":
                return
            else:
                self.picture_with_signature.save(save_path)




