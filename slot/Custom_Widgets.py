"""
自定义控件库
"""
from PyQt5.QtWidgets import QLabel, QTextEdit, QPushButton, QVBoxLayout, QHBoxLayout, QWidget, QMenu, QLineEdit, QFileDialog,QSizePolicy
from PyQt5.QtGui import QContextMenuEvent,QColor,QImage,QPainter,QPixmap,QPen
from PyQt5.QtCore import pyqtSignal , Qt, QSize
import math

class ClickableLabel(QLabel):
    """
    提升控件,可点击的label类,返回点击点对应图像的坐标
    """
    pointClicked = pyqtSignal(int,int)
    def __init__(self, parent=None):
        super(ClickableLabel, self).__init__(parent)
        self.scale_ratio = (1.0,1.0)
        self.image = None

    def setImage(self, image):
        self.image = image
        h_image, w_image = image.shape[:2]
        h_label, w_label = self.height(), self.width()
        self.scale_ratio = (w_image / w_label, h_image / h_label)

    def mousePressEvent(self, event):
        if self.image is None:
            return
        x = int(event.pos().x()*self.scale_ratio[0])
        y = int(event.pos().y()*self.scale_ratio[1])
        if 0 <= x < self.image.shape[1] and 0 <= y < self.image.shape[0]:
            self.pointClicked.emit(x,y)

class ClearableTextEdit(QTextEdit):
    """
    带清空的textedit
    """
    def contextMenuEvent(self, event: QContextMenuEvent):
        menu = self.createStandardContextMenu()
        menu.addSeparator()
        clear_action = menu.addAction("clear")
        action = menu.exec_(event.globalPos())
        if action == clear_action:
            self.clear()

class CameraLabel(QLabel):
    """
    相机专用label
    """
    closed = pyqtSignal(int)
    pause = pyqtSignal(int)
    save = pyqtSignal(int)
    def __init__(self, serial, parent=None):
        super().__init__(parent)
        self.serial = serial
        self.on_pause = None      # 回调函数（暂停）
        self.on_save = None       # 回调函数（保存）
        self.on_close = None      # 回调函数（关闭）

    def contextMenuEvent(self, event):
        menu = QMenu(self)
        pause_action = menu.addAction("暂停")
        save_action = menu.addAction("保存图像")
        close_action = menu.addAction("关闭相机")
        action = menu.exec_(event.globalPos())

        if action == pause_action:
            self.pause.emit(self.serial)
            
        elif action == save_action:
            self.save.emit(self.serial)

        elif action == close_action:
            self.closed.emit(self.serial)

class FolderSelectLineEdit(QLineEdit):
    """
    存储文件夹选择lineEdit
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setReadOnly(True)  # 可选：防止用户手动编辑

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            folder_path = QFileDialog.getExistingDirectory(self, "选择文件夹")
            if folder_path:
                folder_path = folder_path.replace("/", "\\")
                self.setText(folder_path)
        # 继续调用父类方法以保持其他行为（如焦点）
        super().mousePressEvent(event)

class ColorPickerWidget(QWidget):
    """
    自绘色环 + 中间 S/V 正方形的调色控件。

    """
    colorChanged = pyqtSignal(QColor)

    def __init__(self, parent=None, base_size: int = None):
        super().__init__(parent)

        # HSV internal (h in [0,360), s/v in [0,1])
        self.h = 224
        self.s = 1.0
        self.v = 1.0

        # 比例参数（可调）
        self.ring_ratio = 0.12    # 色环厚度占 side 比例
        self.square_ratio = 0.50  # 中间正方形边长占 side 比例

        # 缓存：ring image 与其 side
        self._ring_image = None    # QImage or None
        self._ring_side = 0        # integer side for which ring image was generated

        # QSizePolicy：希望横向扩展，纵向随宽度保持正方形
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        if base_size:
            self.setFixedSize(int(base_size), int(base_size))


    def sizeHint(self):
        return QSize(250, 250)

    def resizeEvent(self, event):
        # Keep square: width decides. We do not permanently lock width.
        w = self.width()
        h = self.height()

        # If height != width, set height limits so widget's height becomes equal to width.
        # Using min/max avoids setFixedHeight which may interfere with layouts later.
        if h != w:
            self.setMinimumHeight(w)
            self.setMaximumHeight(w)

        side = min(w, self.height())
        if side <= 0:
            return

        # regenerate ring only when side changed
        if self._ring_image is None or self._ring_side != side:
            self._generate_ring(int(side))
            self._ring_side = int(side)

        super().resizeEvent(event)

    def _generate_ring(self, side: int):
        """生成 side x side 的色环 QImage（ARGB32，透明背景）"""
        if side <= 0:
            return
        img = QImage(side, side, QImage.Format_ARGB32)
        img.fill(Qt.transparent)

        cx = (side - 1) / 2.0
        cy = cx
        outer_r = side / 2.0
        ring_w = max(1, int(self.ring_ratio * side))
        inner_r = outer_r - ring_w

        # Precompute integer bounds for faster loops
        inner_r2 = inner_r * inner_r
        outer_r2 = outer_r * outer_r

        for y in range(side):
            dy = y - cy
            dy2 = dy * dy
            for x in range(side):
                dx = x - cx
                dist2 = dx * dx + dy2
                if inner_r2 <= dist2 <= outer_r2:
                    angle = (math.degrees(math.atan2(dy, dx)) + 360.0) % 360.0
                    c = QColor()
                    # QColor.setHsv expects H:0..359, S/V:0..255
                    c.setHsv(int(angle) % 360, 255, 255)
                    img.setPixelColor(x, y, c)
                # else leave transparent
        self._ring_image = img


    def paintEvent(self, event):
        p = QPainter(self)
        side = min(self.width(), self.height())
        if side <= 0:
            return

        # draw ring (scale if needed)
        if self._ring_image:
            if self._ring_image.width() != side:
                pix = QPixmap.fromImage(self._ring_image).scaled(side, side, Qt.IgnoreAspectRatio, Qt.SmoothTransformation)
                p.drawPixmap(0, 0, pix)
            else:
                p.drawImage(0, 0, self._ring_image)

        # draw the centered S/V square
        self._draw_square(p, side)

        # optional: draw outlines (for clarity)
        pen = QPen(Qt.black)
        pen.setWidth(1)
        p.setPen(pen)
        # draw outer circle outline
        p.drawEllipse(0, 0, side - 1, side - 1)

    def _draw_square(self, painter: QPainter, side: int):
        # compute ring width and inner radius to know max square
        ring_w = max(1, int(self.ring_ratio * side))
        inner_r = int(side / 2.0 - ring_w)
        # desired square size by ratio
        sq = int(self.square_ratio * side)
        max_square = max(0, int(2 * inner_r) - 2)
        if sq > max_square:
            sq = max_square if max_square > 0 else int(side * 0.5)
        if sq <= 0:
            return

        img = QImage(sq, sq, QImage.Format_RGB32)
        for y in range(sq):
            vy = 1.0 - (y / (sq - 1)) if sq > 1 else 1.0
            for x in range(sq):
                sx = x / (sq - 1) if sq > 1 else 0.0
                col = QColor()
                col.setHsvF(self.h / 360.0, sx, vy)
                img.setPixelColor(x, y, col)

        top_left_x = int((side - sq) / 2)
        top_left_y = int((side - sq) / 2)
        painter.drawImage(top_left_x, top_left_y, img)

        # draw a small indicator for current S/V position
        ind_x = int(top_left_x + (self.s * (sq - 1)))
        ind_y = int(top_left_y + ((1.0 - self.v) * (sq - 1)))
        pen = QPen(Qt.black)
        pen.setWidth(2)
        painter.setPen(pen)
        painter.drawEllipse(ind_x - 4, ind_y - 4, 8, 8)

    def mousePressEvent(self, event):
        self._handle_mouse(event)

    def mouseMoveEvent(self, event):
        if event.buttons() & Qt.LeftButton:
            self._handle_mouse(event)

    def _handle_mouse(self, event):
        side = min(self.width(), self.height())
        if side <= 0:
            return

        cx = (side - 1) / 2.0
        cy = cx
        x = event.x()
        y = event.y()
        dx = x - cx
        dy = y - cy
        dist = math.hypot(dx, dy)

        outer_r = side / 2.0
        ring_w = max(1, int(self.ring_ratio * side))
        inner_r = outer_r - ring_w

        # If clicked on ring -> update hue
        if inner_r <= dist <= outer_r:
            new_h = (math.degrees(math.atan2(dy, dx)) + 360.0) % 360.0
            self.h = new_h
            # redraw square and ring indicator; emit current color (optionally emit hue-only color)
            col = QColor()
            col.setHsvF(self.h / 360.0, self.s, self.v)
            self.colorChanged.emit(col)
            self.update()
            return

        # Otherwise check if clicked inside square
        # compute square position consistent with draw_square
        sq = int(self.square_ratio * side)
        inner_r_int = int(side / 2.0 - ring_w)
        max_square = max(0, int(2 * inner_r_int) - 2)
        if sq > max_square:
            sq = max_square if max_square > 0 else int(side * 0.5)
        top_left_x = cx - sq / 2.0
        top_left_y = cy - sq / 2.0

        rx = x - top_left_x
        ry = y - top_left_y

        if 0 <= rx < sq and 0 <= ry < sq:
            # calculate s and v
            s = (rx) / (sq - 1) if sq > 1 else 0.0
            v = 1.0 - (ry) / (sq - 1) if sq > 1 else 1.0
            self.s = min(1.0, max(0.0, s))
            self.v = min(1.0, max(0.0, v))
            col = QColor()
            col.setHsvF(self.h / 360.0, self.s, self.v)
            self.colorChanged.emit(col)
            self.update()
            return

    # ---------------------
    # External setters/getters
    # ---------------------
    def set_hsv(self, h: float, s: float, v: float, emit: bool = False):
        """h in 0..360, s/v in 0..1"""
        self.h = (h % 360.0)
        self.s = min(1.0, max(0.0, s))
        self.v = min(1.0, max(0.0, v))
        # regenerate ring only when side changed (h change doesn't need new ring)
        self.update()
        if emit:
            col = QColor()
            col.setHsvF(self.h / 360.0, self.s, self.v)
            self.colorChanged.emit(col)

    def set_rgb(self, r: int, g: int, b: int, emit: bool = False):
        """r,g,b in 0..255"""
        c = QColor(r, g, b)
        # QColor.hue() returns -1 for achromatic colors (s==0). handle that.
        hue = c.hue()
        sat = c.saturationF()
        val = c.valueF()
        if hue < 0:
            # choose to keep existing hue when s==0 (gray); but set s/v according to color
            # we keep h unchanged
            h = self.h
        else:
            h = float(hue)
        self.h = h
        self.s = sat
        self.v = val
        self.update()
        if emit:
            self.colorChanged.emit(c)

    # def get_qcolor(self) -> QColor:
    #     col = QColor()
    #     col.setHsvF(self.h / 360.0, self.s, self.v)
    #     return col
            