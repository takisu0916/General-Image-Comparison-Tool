import sys
import os
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *


class ImageWidget(QWidget):
    """单个图像显示组件"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.image_path = ""
        self.original_pixmap = None
        self.display_pixmap = None
        self.scale_factor = 1.0

        # 矩形框数据
        self.primary_rect = QRect()
        self.secondary_rect = QRect()
        self.is_drawing_primary = False
        self.is_drawing_secondary = False
        self.start_point = QPoint()

        # 设置参数（从主窗口同步）
        self.settings = {
            'line_width': 4,
            'margin': 10,
            'primary_color': QColor(255, 0, 0),
            'primary_scale': 1.0,
            'primary_position': 0,  # 0:左上, 1:右上, 2:左下, 3:右下
            'secondary_enabled': False,
            'secondary_color': QColor(0, 255, 0),
            'secondary_scale': 1.0,
            'secondary_position': 1
        }

        self.setMinimumSize(200, 200)

    def set_image(self, image_path):
        """设置图像"""
        self.image_path = image_path
        self.original_pixmap = QPixmap(image_path)
        if not self.original_pixmap.isNull():
            self.update_display()

    def update_display(self):
        """更新显示"""
        if self.original_pixmap:
            # 计算缩放比例以适应控件大小
            widget_size = self.size()
            pixmap_size = self.original_pixmap.size()

            scale_x = widget_size.width() / pixmap_size.width()
            scale_y = widget_size.height() / pixmap_size.height()
            self.scale_factor = min(scale_x, scale_y, 1.0)

            new_size = pixmap_size * self.scale_factor
            self.display_pixmap = self.original_pixmap.scaled(
                new_size, Qt.KeepAspectRatio, Qt.SmoothTransformation)

        self.update()

    def resizeEvent(self, event):
        """窗口大小改变事件"""
        super().resizeEvent(event)
        if self.original_pixmap:
            self.update_display()

    def mousePressEvent(self, event):
        """鼠标按下事件"""
        if not self.display_pixmap:
            return

        if event.button() == Qt.LeftButton:
            pos = self.map_to_image_coords(event.pos())
            if pos:
                self.start_point = pos
                if event.modifiers() & Qt.ShiftModifier and self.settings['secondary_enabled']:
                    self.is_drawing_secondary = True
                else:
                    self.is_drawing_primary = True

    def mouseMoveEvent(self, event):
        """鼠标移动事件"""
        if not self.display_pixmap:
            return

        pos = self.map_to_image_coords(event.pos())
        if pos and (self.is_drawing_primary or self.is_drawing_secondary):
            rect = QRect(self.start_point, pos).normalized()
            if self.is_drawing_primary:
                self.primary_rect = rect
            elif self.is_drawing_secondary:
                self.secondary_rect = rect
            self.update()

    def mouseReleaseEvent(self, event):
        """鼠标释放事件"""
        self.is_drawing_primary = False
        self.is_drawing_secondary = False

    def map_to_image_coords(self, widget_pos):
        """将控件坐标转换为图像坐标"""
        if not self.display_pixmap:
            return None

        # 计算图像在控件中的位置
        widget_size = self.size()
        pixmap_size = self.display_pixmap.size()

        x_offset = (widget_size.width() - pixmap_size.width()) // 2
        y_offset = (widget_size.height() - pixmap_size.height()) // 2

        # 转换为图像坐标
        image_x = (widget_pos.x() - x_offset) / self.scale_factor
        image_y = (widget_pos.y() - y_offset) / self.scale_factor

        # 检查是否在图像范围内
        if (0 <= image_x <= self.original_pixmap.width() and
                0 <= image_y <= self.original_pixmap.height()):
            return QPoint(int(image_x), int(image_y))
        return None

    def map_to_widget_coords(self, image_pos):
        """将图像坐标转换为控件坐标"""
        if not self.display_pixmap:
            return None

        widget_size = self.size()
        pixmap_size = self.display_pixmap.size()

        x_offset = (widget_size.width() - pixmap_size.width()) // 2
        y_offset = (widget_size.height() - pixmap_size.height()) // 2

        widget_x = image_pos.x() * self.scale_factor + x_offset
        widget_y = image_pos.y() * self.scale_factor + y_offset

        return QPoint(int(widget_x), int(widget_y))

    def paintEvent(self, event):
        """绘制事件"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        if not self.display_pixmap:
            return

        # 绘制图像
        widget_size = self.size()
        pixmap_size = self.display_pixmap.size()

        x_offset = (widget_size.width() - pixmap_size.width()) // 2
        y_offset = (widget_size.height() - pixmap_size.height()) // 2

        painter.drawPixmap(x_offset, y_offset, self.display_pixmap)

        # 绘制矩形框
        pen = QPen()
        pen.setWidth(max(1, int(self.settings['line_width'] * self.scale_factor)))

        # 绘制主矩形框
        if not self.primary_rect.isEmpty():
            pen.setColor(self.settings['primary_color'])
            painter.setPen(pen)
            widget_rect = self.map_rect_to_widget(self.primary_rect)
            if widget_rect:
                painter.drawRect(widget_rect)

        # 绘制次矩形框
        if self.settings['secondary_enabled'] and not self.secondary_rect.isEmpty():
            pen.setColor(self.settings['secondary_color'])
            painter.setPen(pen)
            widget_rect = self.map_rect_to_widget(self.secondary_rect)
            if widget_rect:
                painter.drawRect(widget_rect)

        # 绘制放大图
        if self.settings.get('show_magnified', True):
            self.draw_magnified_regions(painter)

    def map_rect_to_widget(self, image_rect):
        """将图像矩形转换为控件矩形"""
        top_left = self.map_to_widget_coords(image_rect.topLeft())
        bottom_right = self.map_to_widget_coords(image_rect.bottomRight())
        if top_left and bottom_right:
            return QRect(top_left, bottom_right)
        return None

    def draw_magnified_regions(self, painter):
        """绘制放大区域"""
        if not self.original_pixmap:
            return

        # 绘制主放大区域
        if not self.primary_rect.isEmpty():
            self.draw_magnified_region(
                painter, self.primary_rect,
                self.settings['primary_color'],
                self.settings['primary_scale'],
                self.settings['primary_position']
            )

        # 绘制次放大区域
        if (self.settings['secondary_enabled'] and
                not self.secondary_rect.isEmpty()):
            self.draw_magnified_region(
                painter, self.secondary_rect,
                self.settings['secondary_color'],
                self.settings['secondary_scale'],
                self.settings['secondary_position']
            )

    def draw_magnified_region(self, painter, rect, color, scale, position):
        """绘制单个放大区域"""
        # 从原图提取区域
        source_rect = rect.intersected(QRect(0, 0,
                                             self.original_pixmap.width(),
                                             self.original_pixmap.height()))
        if source_rect.isEmpty():
            return

        cropped = self.original_pixmap.copy(source_rect)

        # 计算放大后的尺寸
        scaled_size = QSize(int(source_rect.width() * scale),
                            int(source_rect.height() * scale))
        magnified = cropped.scaled(scaled_size, Qt.KeepAspectRatio,
                                   Qt.SmoothTransformation)

        # 计算放大图的位置
        margin = self.settings['margin']
        widget_size = self.size()
        pixmap_size = self.display_pixmap.size()

        x_offset = (widget_size.width() - pixmap_size.width()) // 2
        y_offset = (widget_size.height() - pixmap_size.height()) // 2

        # 根据位置设置计算坐标
        if position == 0:  # 左上
            mag_x = x_offset + margin
            mag_y = y_offset + margin
        elif position == 1:  # 右上
            mag_x = x_offset + pixmap_size.width() - magnified.width() - margin
            mag_y = y_offset + margin
        elif position == 2:  # 左下
            mag_x = x_offset + margin
            mag_y = y_offset + pixmap_size.height() - magnified.height() - margin
        else:  # 右下
            mag_x = x_offset + pixmap_size.width() - magnified.width() - margin
            mag_y = y_offset + pixmap_size.height() - magnified.height() - margin

        # 确保不超出图像边界
        mag_x = max(x_offset + margin,
                    min(mag_x, x_offset + pixmap_size.width() - magnified.width() - margin))
        mag_y = max(y_offset + margin,
                    min(mag_y, y_offset + pixmap_size.height() - magnified.height() - margin))

        # 绘制放大图
        painter.drawPixmap(mag_x, mag_y, magnified)

        # 绘制边框
        pen = QPen(color, max(1, int(self.settings['line_width'] * self.scale_factor)))
        painter.setPen(pen)
        painter.drawRect(mag_x, mag_y, magnified.width(), magnified.height())

    def update_settings(self, settings):
        """更新设置"""
        self.settings.update(settings)
        self.update()

    def set_primary_rect(self, rect):
        """设置主矩形框"""
        self.primary_rect = rect
        self.update()

    def set_secondary_rect(self, rect):
        """设置次矩形框"""
        self.secondary_rect = rect
        self.update()


class SettingsPanel(QWidget):
    """设置面板"""
    settings_changed = pyqtSignal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)

        # 通用设置
        general_group = QGroupBox("通用设置")
        general_layout = QFormLayout(general_group)

        self.line_width_spin = QSpinBox()
        self.line_width_spin.setRange(1, 20)
        self.line_width_spin.setValue(4)
        self.line_width_spin.valueChanged.connect(self.emit_settings)
        general_layout.addRow("线宽:", self.line_width_spin)

        self.margin_spin = QSpinBox()
        self.margin_spin.setRange(0, 100)
        self.margin_spin.setValue(10)
        self.margin_spin.valueChanged.connect(self.emit_settings)
        general_layout.addRow("边距:", self.margin_spin)

        layout.addWidget(general_group)

        self.magnified_check = QCheckBox("")
        self.magnified_check.setChecked(True)  # 默认开启
        self.magnified_check.stateChanged.connect(self.emit_settings)  # 添加这行
        general_layout.addRow("显示放大图: ", self.magnified_check)  # 新增行

        # 主矩形设置
        primary_group = QGroupBox("主矩形设置")
        primary_layout = QFormLayout(primary_group)

        self.primary_color_btn = QPushButton()
        self.primary_color_btn.setStyleSheet("background-color: red")
        self.primary_color_btn.clicked.connect(lambda: self.choose_color('primary'))
        primary_layout.addRow("颜色:", self.primary_color_btn)

        self.primary_scale_spin = QDoubleSpinBox()
        self.primary_scale_spin.setRange(0.1, 10.0)
        self.primary_scale_spin.setValue(1.0)
        self.primary_scale_spin.setSingleStep(0.1)
        self.primary_scale_spin.valueChanged.connect(self.emit_settings)
        primary_layout.addRow("放大比例:", self.primary_scale_spin)

        self.primary_position_combo = QComboBox()
        self.primary_position_combo.addItems(["左上", "右上", "左下", "右下"])
        self.primary_position_combo.currentIndexChanged.connect(self.emit_settings)
        primary_layout.addRow("位置:", self.primary_position_combo)

        layout.addWidget(primary_group)

        # 次矩形设置
        secondary_group = QGroupBox("次矩形设置")
        secondary_layout = QFormLayout(secondary_group)

        self.secondary_enabled_check = QCheckBox("启用次矩形")
        self.secondary_enabled_check.stateChanged.connect(self.emit_settings)
        secondary_layout.addRow(self.secondary_enabled_check)

        self.secondary_color_btn = QPushButton()
        self.secondary_color_btn.setStyleSheet("background-color: green")
        self.secondary_color_btn.clicked.connect(lambda: self.choose_color('secondary'))
        secondary_layout.addRow("颜色:", self.secondary_color_btn)

        self.secondary_scale_spin = QDoubleSpinBox()
        self.secondary_scale_spin.setRange(0.1, 10.0)
        self.secondary_scale_spin.setValue(1.0)
        self.secondary_scale_spin.setSingleStep(0.1)
        self.secondary_scale_spin.valueChanged.connect(self.emit_settings)
        secondary_layout.addRow("放大比例:", self.secondary_scale_spin)

        self.secondary_position_combo = QComboBox()
        self.secondary_position_combo.addItems(["左上", "右上", "左下", "右下"])
        self.secondary_position_combo.setCurrentIndex(1)
        self.secondary_position_combo.currentIndexChanged.connect(self.emit_settings)
        secondary_layout.addRow("位置:", self.secondary_position_combo)

        layout.addWidget(secondary_group)

        # 文件操作
        file_group = QGroupBox("文件操作")
        file_layout = QVBoxLayout(file_group)

        self.load_btn = QPushButton("载入图片")
        self.load_btn.clicked.connect(self.load_images)
        file_layout.addWidget(self.load_btn)

        ##保存整张图片
        self.save_btn = QPushButton("保存整张图片")
        self.save_btn.clicked.connect(self.save_images)
        file_layout.addWidget(self.save_btn)

        ##保存局部图片
        self.save_local_btn = QPushButton("保存局部放大图")
        self.save_local_btn.clicked.connect(self.save_local_images)
        file_layout.addWidget(self.save_local_btn)



        layout.addWidget(file_group)
        layout.addStretch()

        # 存储颜色
        self.primary_color = QColor(255, 0, 0)
        self.secondary_color = QColor(0, 255, 0)










    def choose_color(self, color_type):
        """选择颜色"""
        current_color = self.primary_color if color_type == 'primary' else self.secondary_color
        color = QColorDialog.getColor(current_color, self)
        if color.isValid():
            if color_type == 'primary':
                self.primary_color = color
                self.primary_color_btn.setStyleSheet(f"background-color: {color.name()}")
            else:
                self.secondary_color = color
                self.secondary_color_btn.setStyleSheet(f"background-color: {color.name()}")
            self.emit_settings()

    def emit_settings(self):
        """发送设置变化信号"""
        settings = {
            'line_width': self.line_width_spin.value(),
            'margin': self.margin_spin.value(),
            'primary_color': self.primary_color,
            'primary_scale': self.primary_scale_spin.value(),
            'primary_position': self.primary_position_combo.currentIndex(),
            'secondary_enabled': self.secondary_enabled_check.isChecked(),
            'secondary_color': self.secondary_color,
            'secondary_scale': self.secondary_scale_spin.value(),
            'secondary_position': self.secondary_position_combo.currentIndex(),
            'show_magnified': self.magnified_check.isChecked()  # 新增选项
        }
        self.settings_changed.emit(settings)

    def load_images(self):
        """加载图片"""
        files, _ = QFileDialog.getOpenFileNames(
            self, "选择图片", "",
            "Image Files (*.png *.jpg *.jpeg *.bmp *.tiff)")
        if files:
            self.window().load_images(files)

    def save_images(self):
        """保存图片"""
        self.window().save_images()

    def save_local_images(self):
        """触发保存局部放大图"""
        self.window().save_local_images()


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.image_widgets = []
        self.current_settings = {}
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("General Image Comparison Tool")
        self.setGeometry(500, 500, 2500, 800)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QHBoxLayout(central_widget)

        # 左侧图像区域
        self.image_area = QScrollArea()
        self.image_container = QWidget()
        self.image_layout = QGridLayout(self.image_container)
        self.image_layout.setSpacing(5)

        self.image_area.setWidget(self.image_container)
        self.image_area.setWidgetResizable(True)
        main_layout.addWidget(self.image_area, 3)

        # 右侧设置面板
        self.settings_panel = SettingsPanel(self)
        self.settings_panel.settings_changed.connect(self.update_all_settings)
        main_layout.addWidget(self.settings_panel, 1)

        # 初始化设置
        self.settings_panel.emit_settings()

    def load_images(self, file_paths):
        """加载图片"""
        # 清除现有图片
        for widget in self.image_widgets:
            widget.setParent(None)
        self.image_widgets.clear()

        # 计算网格布局
        count = len(file_paths)
        if count == 0:
            return

        cols = min(3, count)  # 最多3列
        rows = (count + cols - 1) // cols

        # 创建图像控件
        for i, file_path in enumerate(file_paths):
            row = i // cols
            col = i % cols

            # 创建容器
            container = QWidget()
            container_layout = QVBoxLayout(container)
            container_layout.setContentsMargins(2, 2, 2, 2)
            container_layout.setSpacing(2)

            # 文件名标签
            filename = os.path.basename(file_path)
            label = QLabel(filename)
            label.setAlignment(Qt.AlignCenter)
            label.setStyleSheet("font-weight: bold; padding: 2px;")
            container_layout.addWidget(label)

            # 图像控件
            image_widget = ImageWidget()
            image_widget.set_image(file_path)
            image_widget.update_settings(self.current_settings)

            # 连接鼠标事件以同步矩形框
            image_widget.mousePressEvent = self.create_mouse_press_handler(image_widget)
            image_widget.mouseMoveEvent = self.create_mouse_move_handler(image_widget)
            image_widget.mouseReleaseEvent = self.create_mouse_release_handler(image_widget)

            container_layout.addWidget(image_widget, 1)

            self.image_layout.addWidget(container, row, col)
            self.image_widgets.append(image_widget)

    def create_mouse_press_handler(self, source_widget):
        """创建鼠标按下事件处理器"""
        original_handler = source_widget.mousePressEvent

        def handler(event):
            original_handler(event)
            # 同步到其他控件
            for widget in self.image_widgets:
                if widget != source_widget:
                    widget.start_point = source_widget.start_point
                    widget.is_drawing_primary = source_widget.is_drawing_primary
                    widget.is_drawing_secondary = source_widget.is_drawing_secondary

        return handler

    def create_mouse_move_handler(self, source_widget):
        """创建鼠标移动事件处理器"""
        original_handler = source_widget.mouseMoveEvent

        def handler(event):
            original_handler(event)
            # 同步矩形框到其他控件
            for widget in self.image_widgets:
                if widget != source_widget:
                    if source_widget.is_drawing_primary:
                        widget.primary_rect = source_widget.primary_rect
                    elif source_widget.is_drawing_secondary:
                        widget.secondary_rect = source_widget.secondary_rect
                    widget.update()

        return handler

    def create_mouse_release_handler(self, source_widget):
        """创建鼠标释放事件处理器"""
        original_handler = source_widget.mouseReleaseEvent

        def handler(event):
            original_handler(event)
            # 同步状态到其他控件
            for widget in self.image_widgets:
                if widget != source_widget:
                    widget.is_drawing_primary = False
                    widget.is_drawing_secondary = False

        return handler

    def update_all_settings(self, settings):
        """更新所有图像控件的设置"""
        self.current_settings = settings
        for widget in self.image_widgets:
            widget.update_settings(settings)

    def save_images(self):
        """保存图片"""
        if not self.image_widgets:
            QMessageBox.warning(self, "警告", "没有加载的图片")
            return

        folder = QFileDialog.getExistingDirectory(self, "选择保存文件夹")
        if not folder:
            return

        for i, widget in enumerate(self.image_widgets):
            if widget.original_pixmap:
                # 创建保存用的图像
                save_pixmap = widget.original_pixmap.copy()
                painter = QPainter(save_pixmap)
                painter.setRenderHint(QPainter.Antialiasing)

                # 绘制矩形框和放大图（使用原始尺寸）
                self.draw_annotations_for_save(painter, widget, save_pixmap.size())

                painter.end()

                # 保存文件
                base_name = os.path.splitext(os.path.basename(widget.image_path))[0]
                save_path = os.path.join(folder, f"{base_name}_processed.png")
                save_pixmap.save(save_path)

        QMessageBox.information(self, "保存完成", f"已保存 {len(self.image_widgets)} 张图片到 {folder}")

    def save_local_images(self):
        """保存所有局部放大图"""
        if not self.image_widgets:
            QMessageBox.warning(self, "警告", "没有加载的图片")
            return

        folder = QFileDialog.getExistingDirectory(self, "选择保存文件夹")
        if not folder:
            return

        for widget in self.image_widgets:
            if not widget.original_pixmap:
                continue

            # 保存主矩形放大图
            if not widget.primary_rect.isEmpty():
                self.save_single_magnified(
                    widget,
                    widget.primary_rect,
                    widget.settings['primary_scale'],
                    folder,
                    "primary"
                )

            # 保存次矩形放大图
            if widget.settings['secondary_enabled'] and not widget.secondary_rect.isEmpty():
                self.save_single_magnified(
                    widget,
                    widget.secondary_rect,
                    widget.settings['secondary_scale'],
                    folder,
                    "secondary"
                )
            #消息
        if widget.settings['secondary_enabled'] and not widget.secondary_rect.isEmpty():
            QMessageBox.information(self, "保存完成", f"已保存 {len(self.image_widgets)*2} 张图片到 {folder}")
        else:
            QMessageBox.information(self, "保存完成", f"已保存 {len(self.image_widgets)} 张图片到 {folder}")




    def save_single_magnified(self, widget, rect, scale, folder, prefix):
        """保存单个放大区域"""
        # 获取原图区域
        source_rect = rect.intersected(QRect(0, 0,
                                             widget.original_pixmap.width(),
                                             widget.original_pixmap.height()))
        if source_rect.isEmpty():
            return

        # 截取并缩放图像
        cropped = widget.original_pixmap.copy(source_rect)
        scaled_size = QSize(
            int(source_rect.width() * scale),
            int(source_rect.height() * scale)
        )

        # 使用SmoothTransformation保持质量
        magnified = cropped.scaled(scaled_size, Qt.KeepAspectRatio, Qt.SmoothTransformation)

        # 生成文件名
        base_name = os.path.splitext(os.path.basename(widget.image_path))[0]
        save_path = os.path.join(folder, f"{base_name}_{prefix}.png")

        # 保存图片
        magnified.save(save_path)

    def draw_annotations_for_save(self, painter, widget, image_size):
        """为保存绘制标注（原始尺寸）"""
        settings = widget.settings

        # 绘制矩形框
        pen = QPen()
        pen.setWidth(settings['line_width'])

        # 主矩形框
        if not widget.primary_rect.isEmpty():
            pen.setColor(settings['primary_color'])
            painter.setPen(pen)
            painter.drawRect(widget.primary_rect)

        # 次矩形框
        if settings['secondary_enabled'] and not widget.secondary_rect.isEmpty():
            pen.setColor(settings['secondary_color'])
            painter.setPen(pen)
            painter.drawRect(widget.secondary_rect)

        # 绘制放大图
        if not widget.primary_rect.isEmpty():
            if widget.settings.get('show_magnified', True):
                self.draw_magnified_for_save(
                    painter, widget, widget.primary_rect,
                    settings['primary_color'], settings['primary_scale'],
                    settings['primary_position'], image_size
                )

        if (settings['secondary_enabled'] and not widget.secondary_rect.isEmpty()):
            if widget.settings.get('show_magnified', True):
                self.draw_magnified_for_save(
                    painter, widget, widget.secondary_rect,
                    settings['secondary_color'], settings['secondary_scale'],
                    settings['secondary_position'], image_size
                )

    def draw_magnified_for_save(self, painter, widget, rect, color, scale, position, image_size):
        """为保存绘制放大区域"""
        # 提取区域
        source_rect = rect.intersected(QRect(0, 0, image_size.width(), image_size.height()))
        if source_rect.isEmpty():
            return

        cropped = widget.original_pixmap.copy(source_rect)

        # 关键修改：使用IgnoreAspectRatio确保严格缩放
        scaled_size = QSize(
            int(source_rect.width() * scale),
            int(source_rect.height() * scale)
        )
        magnified = cropped.scaled(
            scaled_size,
            Qt.IgnoreAspectRatio,  # 改为不保持宽高比
            Qt.SmoothTransformation
        )

        margin = widget.settings['margin']

        # 位置计算保持不变
        if position == 0:  # 左上
            mag_x = margin
            mag_y = margin
        elif position == 1:  # 右上
            mag_x = image_size.width() - magnified.width() - margin
            mag_y = margin
        elif position == 2:  # 左下
            mag_x = margin
            mag_y = image_size.height() - magnified.height() - margin
        else:  # 右下
            mag_x = image_size.width() - magnified.width() - margin
            mag_y = image_size.height() - magnified.height() - margin

        # 边界检查
        mag_x = max(margin, min(mag_x, image_size.width() - magnified.width() - margin))
        mag_y = max(margin, min(mag_y, image_size.height() - magnified.height() - margin))

        # 绘制放大图
        painter.drawPixmap(mag_x, mag_y, magnified)

        # 绘制边框
        pen = QPen(color, widget.settings['line_width'])
        painter.setPen(pen)
        painter.drawRect(mag_x, mag_y, magnified.width(), magnified.height())


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
