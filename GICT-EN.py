import sys
import os
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *


class ImageWidget(QWidget):
    """Single image display widget"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.image_path = ""
        self.original_pixmap = None
        self.display_pixmap = None
        self.scale_factor = 1.0


        self.primary_rect = QRect()
        self.secondary_rect = QRect()
        self.is_drawing_primary = False
        self.is_drawing_secondary = False
        self.start_point = QPoint()

        # Parameters settings
        self.settings = {
            'line_width': 4,
            'margin': 10,
            'primary_color': QColor(255, 0, 0),
            'primary_scale': 1.0,
            'primary_position': 0,  # 0:Top Left, 1:Top Right, 2:Bottom Left, 3:Bottom Right
            'secondary_enabled': False,
            'secondary_color': QColor(0, 255, 0),
            'secondary_scale': 1.0,
            'secondary_position': 1
        }

        self.setMinimumSize(200, 200)

    def set_image(self, image_path):
        """Set the image"""
        self.image_path = image_path
        self.original_pixmap = QPixmap(image_path)
        if not self.original_pixmap.isNull():
            self.update_display()

    def update_display(self):
        if self.original_pixmap:
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
        super().resizeEvent(event)
        if self.original_pixmap:
            self.update_display()

    def mousePressEvent(self, event):
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
        self.is_drawing_primary = False
        self.is_drawing_secondary = False

    def map_to_image_coords(self, widget_pos):
        if not self.display_pixmap:
            return None


        widget_size = self.size()
        pixmap_size = self.display_pixmap.size()

        x_offset = (widget_size.width() - pixmap_size.width()) // 2
        y_offset = (widget_size.height() - pixmap_size.height()) // 2


        image_x = (widget_pos.x() - x_offset) / self.scale_factor
        image_y = (widget_pos.y() - y_offset) / self.scale_factor


        if (0 <= image_x <= self.original_pixmap.width() and
                0 <= image_y <= self.original_pixmap.height()):
            return QPoint(int(image_x), int(image_y))
        return None

    def map_to_widget_coords(self, image_pos):
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
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        if not self.display_pixmap:
            return


        widget_size = self.size()
        pixmap_size = self.display_pixmap.size()

        x_offset = (widget_size.width() - pixmap_size.width()) // 2
        y_offset = (widget_size.height() - pixmap_size.height()) // 2

        painter.drawPixmap(x_offset, y_offset, self.display_pixmap)


        pen = QPen()
        pen.setWidth(max(1, int(self.settings['line_width'] * self.scale_factor)))


        if not self.primary_rect.isEmpty():
            pen.setColor(self.settings['primary_color'])
            painter.setPen(pen)
            widget_rect = self.map_rect_to_widget(self.primary_rect)
            if widget_rect:
                painter.drawRect(widget_rect)


        if self.settings['secondary_enabled'] and not self.secondary_rect.isEmpty():
            pen.setColor(self.settings['secondary_color'])
            painter.setPen(pen)
            widget_rect = self.map_rect_to_widget(self.secondary_rect)
            if widget_rect:
                painter.drawRect(widget_rect)


        if self.settings.get('show_magnified', True):
            self.draw_magnified_regions(painter)

    def map_rect_to_widget(self, image_rect):

        top_left = self.map_to_widget_coords(image_rect.topLeft())
        bottom_right = self.map_to_widget_coords(image_rect.bottomRight())
        if top_left and bottom_right:
            return QRect(top_left, bottom_right)
        return None

    def draw_magnified_regions(self, painter):

        if not self.original_pixmap:
            return


        if not self.primary_rect.isEmpty():
            self.draw_magnified_region(
                painter, self.primary_rect,
                self.settings['primary_color'],
                self.settings['primary_scale'],
                self.settings['primary_position']
            )


        if (self.settings['secondary_enabled'] and
                not self.secondary_rect.isEmpty()):
            self.draw_magnified_region(
                painter, self.secondary_rect,
                self.settings['secondary_color'],
                self.settings['secondary_scale'],
                self.settings['secondary_position']
            )

    def draw_magnified_region(self, painter, rect, color, scale, position):
        source_rect = rect.intersected(QRect(0, 0,
                                             self.original_pixmap.width(),
                                             self.original_pixmap.height()))
        if source_rect.isEmpty():
            return

        cropped = self.original_pixmap.copy(source_rect)


        scaled_size = QSize(int(source_rect.width() * scale),
                            int(source_rect.height() * scale))
        magnified = cropped.scaled(scaled_size, Qt.KeepAspectRatio,
                                   Qt.SmoothTransformation)


        margin = self.settings['margin']
        widget_size = self.size()
        pixmap_size = self.display_pixmap.size()

        x_offset = (widget_size.width() - pixmap_size.width()) // 2
        y_offset = (widget_size.height() - pixmap_size.height()) // 2


        if position == 0:
            mag_x = x_offset + margin
            mag_y = y_offset + margin
        elif position == 1:
            mag_x = x_offset + pixmap_size.width() - magnified.width() - margin
            mag_y = y_offset + margin
        elif position == 2:
            mag_x = x_offset + margin
            mag_y = y_offset + pixmap_size.height() - magnified.height() - margin
        else:
            mag_x = x_offset + pixmap_size.width() - magnified.width() - margin
            mag_y = y_offset + pixmap_size.height() - magnified.height() - margin


        mag_x = max(x_offset + margin,
                    min(mag_x, x_offset + pixmap_size.width() - magnified.width() - margin))
        mag_y = max(y_offset + margin,
                    min(mag_y, y_offset + pixmap_size.height() - magnified.height() - margin))


        painter.drawPixmap(mag_x, mag_y, magnified)


        pen = QPen(color, max(1, int(self.settings['line_width'] * self.scale_factor)))
        painter.setPen(pen)
        painter.drawRect(mag_x, mag_y, magnified.width(), magnified.height())

    def update_settings(self, settings):

        self.settings.update(settings)
        self.update()

    def set_primary_rect(self, rect):

        self.primary_rect = rect
        self.update()

    def set_secondary_rect(self, rect):

        self.secondary_rect = rect
        self.update()


class SettingsPanel(QWidget):

    settings_changed = pyqtSignal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)

        # General Settings
        general_group = QGroupBox("General Settings")
        general_layout = QFormLayout(general_group)

        self.line_width_spin = QSpinBox()
        self.line_width_spin.setRange(1, 20)
        self.line_width_spin.setValue(4)
        self.line_width_spin.valueChanged.connect(self.emit_settings)
        general_layout.addRow("Line width (px):", self.line_width_spin)

        self.margin_spin = QSpinBox()
        self.margin_spin.setRange(0, 100)
        self.margin_spin.setValue(10)
        self.margin_spin.valueChanged.connect(self.emit_settings)
        general_layout.addRow("Margin (px):", self.margin_spin)

        layout.addWidget(general_group)

        self.magnified_check = QCheckBox("")
        self.magnified_check.setChecked(True)
        self.magnified_check.stateChanged.connect(self.emit_settings)
        general_layout.addRow("Display the enlarged image: ", self.magnified_check)

        # Primary Rectangle Settings
        primary_group = QGroupBox("Primary Rectangle Settings")
        primary_layout = QFormLayout(primary_group)

        self.primary_color_btn = QPushButton()
        self.primary_color_btn.setStyleSheet("background-color: red")
        self.primary_color_btn.clicked.connect(lambda: self.choose_color('primary'))
        primary_layout.addRow("Color:", self.primary_color_btn)

        self.primary_scale_spin = QDoubleSpinBox()
        self.primary_scale_spin.setRange(0.1, 10.0)
        self.primary_scale_spin.setValue(1.0)
        self.primary_scale_spin.setSingleStep(0.1)
        self.primary_scale_spin.valueChanged.connect(self.emit_settings)
        primary_layout.addRow("Zoom ratio:", self.primary_scale_spin)

        self.primary_position_combo = QComboBox()
        self.primary_position_combo.addItems(["Top Left", "Top Right", "Bottom Left", "Bottom Right"])
        self.primary_position_combo.currentIndexChanged.connect(self.emit_settings)
        primary_layout.addRow("Position:", self.primary_position_combo)

        layout.addWidget(primary_group)

        # Secondary Rectangle Settings
        secondary_group = QGroupBox("Secondary Rectangle Settings")
        secondary_layout = QFormLayout(secondary_group)

        self.secondary_enabled_check = QCheckBox("Active secondary rectangle")
        self.secondary_enabled_check.stateChanged.connect(self.emit_settings)
        secondary_layout.addRow(self.secondary_enabled_check)

        self.secondary_color_btn = QPushButton()
        self.secondary_color_btn.setStyleSheet("background-color: green")
        self.secondary_color_btn.clicked.connect(lambda: self.choose_color('secondary'))
        secondary_layout.addRow("Color:", self.secondary_color_btn)

        self.secondary_scale_spin = QDoubleSpinBox()
        self.secondary_scale_spin.setRange(0.1, 10.0)
        self.secondary_scale_spin.setValue(1.0)
        self.secondary_scale_spin.setSingleStep(0.1)
        self.secondary_scale_spin.valueChanged.connect(self.emit_settings)
        secondary_layout.addRow("Zoom ratio:", self.secondary_scale_spin)

        self.secondary_position_combo = QComboBox()
        self.secondary_position_combo.addItems(["Top Left", "Top Right", "Bottom Left", "Bottom Right"])
        self.secondary_position_combo.setCurrentIndex(1)
        self.secondary_position_combo.currentIndexChanged.connect(self.emit_settings)
        secondary_layout.addRow("Position:", self.secondary_position_combo)

        layout.addWidget(secondary_group)

        # File Operations
        file_group = QGroupBox("File Operations")
        file_layout = QVBoxLayout(file_group)

        self.load_btn = QPushButton("Load images")
        self.load_btn.clicked.connect(self.load_images)
        file_layout.addWidget(self.load_btn)

        self.save_btn = QPushButton("Save the entire image")
        self.save_btn.clicked.connect(self.save_images)
        file_layout.addWidget(self.save_btn)

        self.save_local_btn = QPushButton("Save the image of the region")
        self.save_local_btn.clicked.connect(self.save_local_images)
        file_layout.addWidget(self.save_local_btn)



        layout.addWidget(file_group)
        layout.addStretch()


        self.primary_color = QColor(255, 0, 0)
        self.secondary_color = QColor(0, 255, 0)










    def choose_color(self, color_type):
        """Select color"""
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
        """Send signal"""
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
            'show_magnified': self.magnified_check.isChecked()
        }
        self.settings_changed.emit(settings)

    def load_images(self):
        files, _ = QFileDialog.getOpenFileNames(
            self, "Select images", "",
            "Image Files (*.png *.jpg *.jpeg *.bmp *.tiff)")
        if files:
            self.window().load_images(files)

    def save_images(self):
        self.window().save_images()

    def save_local_images(self):
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

        self.image_area = QScrollArea()
        self.image_container = QWidget()
        self.image_layout = QGridLayout(self.image_container)
        self.image_layout.setSpacing(5)

        self.image_area.setWidget(self.image_container)
        self.image_area.setWidgetResizable(True)
        main_layout.addWidget(self.image_area, 3)

        self.settings_panel = SettingsPanel(self)
        self.settings_panel.settings_changed.connect(self.update_all_settings)
        main_layout.addWidget(self.settings_panel, 1)

        # init
        self.settings_panel.emit_settings()

    def load_images(self, file_paths):
        for widget in self.image_widgets:
            widget.setParent(None)
        self.image_widgets.clear()

        count = len(file_paths)
        if count == 0:
            return

        cols = min(3, count)
        rows = (count + cols - 1) // cols

        for i, file_path in enumerate(file_paths):
            row = i // cols
            col = i % cols

            container = QWidget()
            container_layout = QVBoxLayout(container)
            container_layout.setContentsMargins(2, 2, 2, 2)
            container_layout.setSpacing(2)

            filename = os.path.basename(file_path)
            label = QLabel(filename)
            label.setAlignment(Qt.AlignCenter)
            label.setStyleSheet("font-weight: bold; padding: 2px;")
            container_layout.addWidget(label)


            image_widget = ImageWidget()
            image_widget.set_image(file_path)
            image_widget.update_settings(self.current_settings)


            image_widget.mousePressEvent = self.create_mouse_press_handler(image_widget)
            image_widget.mouseMoveEvent = self.create_mouse_move_handler(image_widget)
            image_widget.mouseReleaseEvent = self.create_mouse_release_handler(image_widget)

            container_layout.addWidget(image_widget, 1)

            self.image_layout.addWidget(container, row, col)
            self.image_widgets.append(image_widget)

    def create_mouse_press_handler(self, source_widget):

        original_handler = source_widget.mousePressEvent

        def handler(event):
            original_handler(event)

            for widget in self.image_widgets:
                if widget != source_widget:
                    widget.start_point = source_widget.start_point
                    widget.is_drawing_primary = source_widget.is_drawing_primary
                    widget.is_drawing_secondary = source_widget.is_drawing_secondary

        return handler

    def create_mouse_move_handler(self, source_widget):

        original_handler = source_widget.mouseMoveEvent

        def handler(event):
            original_handler(event)

            for widget in self.image_widgets:
                if widget != source_widget:
                    if source_widget.is_drawing_primary:
                        widget.primary_rect = source_widget.primary_rect
                    elif source_widget.is_drawing_secondary:
                        widget.secondary_rect = source_widget.secondary_rect
                    widget.update()

        return handler

    def create_mouse_release_handler(self, source_widget):

        original_handler = source_widget.mouseReleaseEvent

        def handler(event):
            original_handler(event)

            for widget in self.image_widgets:
                if widget != source_widget:
                    widget.is_drawing_primary = False
                    widget.is_drawing_secondary = False

        return handler

    def update_all_settings(self, settings):

        self.current_settings = settings
        for widget in self.image_widgets:
            widget.update_settings(settings)

    def save_images(self):

        if not self.image_widgets:
            QMessageBox.warning(self, "Warning!", "Image not loaded")
            return

        folder = QFileDialog.getExistingDirectory(self, "Choose the save folder")
        if not folder:
            return

        for i, widget in enumerate(self.image_widgets):
            if widget.original_pixmap:

                save_pixmap = widget.original_pixmap.copy()
                painter = QPainter(save_pixmap)
                painter.setRenderHint(QPainter.Antialiasing)

                self.draw_annotations_for_save(painter, widget, save_pixmap.size())

                painter.end()

                base_name = os.path.splitext(os.path.basename(widget.image_path))[0]
                save_path = os.path.join(folder, f"{base_name}_processed.png")
                save_pixmap.save(save_path)

        QMessageBox.information(self, "Save completed", f"Saved {len(self.image_widgets)} images to {folder}")

    def save_local_images(self):
        if not self.image_widgets:
            QMessageBox.warning(self, "Warning!", "Image not loaded")
            return

        folder = QFileDialog.getExistingDirectory(self, "Choose the save folder")
        if not folder:
            return

        for widget in self.image_widgets:
            if not widget.original_pixmap:
                continue


            if not widget.primary_rect.isEmpty():
                self.save_single_magnified(
                    widget,
                    widget.primary_rect,
                    widget.settings['primary_scale'],
                    folder,
                    "primary"
                )


            if widget.settings['secondary_enabled'] and not widget.secondary_rect.isEmpty():
                self.save_single_magnified(
                    widget,
                    widget.secondary_rect,
                    widget.settings['secondary_scale'],
                    folder,
                    "secondary"
                )

        if widget.settings['secondary_enabled'] and not widget.secondary_rect.isEmpty():
            QMessageBox.information(self, "Save completed", f"Saved {len(self.image_widgets)*2} images to {folder}")
        else:
            QMessageBox.information(self, "Save completed", f"Saved {len(self.image_widgets)} images to {folder}")




    def save_single_magnified(self, widget, rect, scale, folder, prefix):

        source_rect = rect.intersected(QRect(0, 0,
                                             widget.original_pixmap.width(),
                                             widget.original_pixmap.height()))
        if source_rect.isEmpty():
            return


        cropped = widget.original_pixmap.copy(source_rect)
        scaled_size = QSize(
            int(source_rect.width() * scale),
            int(source_rect.height() * scale)
        )

        # SmoothTransformation
        magnified = cropped.scaled(scaled_size, Qt.KeepAspectRatio, Qt.SmoothTransformation)


        base_name = os.path.splitext(os.path.basename(widget.image_path))[0]
        save_path = os.path.join(folder, f"{base_name}_{prefix}.png")


        magnified.save(save_path)

    def draw_annotations_for_save(self, painter, widget, image_size):

        settings = widget.settings


        pen = QPen()
        pen.setWidth(settings['line_width'])


        if not widget.primary_rect.isEmpty():
            pen.setColor(settings['primary_color'])
            painter.setPen(pen)
            painter.drawRect(widget.primary_rect)


        if settings['secondary_enabled'] and not widget.secondary_rect.isEmpty():
            pen.setColor(settings['secondary_color'])
            painter.setPen(pen)
            painter.drawRect(widget.secondary_rect)


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
        source_rect = rect.intersected(QRect(0, 0, image_size.width(), image_size.height()))
        if source_rect.isEmpty():
            return

        cropped = widget.original_pixmap.copy(source_rect)


        scaled_size = QSize(
            int(source_rect.width() * scale),
            int(source_rect.height() * scale)
        )
        magnified = cropped.scaled(
            scaled_size,
            Qt.IgnoreAspectRatio,
            Qt.SmoothTransformation
        )

        margin = widget.settings['margin']


        if position == 0:  # 0:Top Left
            mag_x = margin
            mag_y = margin
        elif position == 1: #1:Top Right
            mag_x = image_size.width() - magnified.width() - margin
            mag_y = margin
        elif position == 2:  #2:Bottom Left
            mag_x = margin
            mag_y = image_size.height() - magnified.height() - margin
        else:  #3:Bottom Right
            mag_x = image_size.width() - magnified.width() - margin
            mag_y = image_size.height() - magnified.height() - margin


        mag_x = max(margin, min(mag_x, image_size.width() - magnified.width() - margin))
        mag_y = max(margin, min(mag_y, image_size.height() - magnified.height() - margin))


        painter.drawPixmap(mag_x, mag_y, magnified)


        pen = QPen(color, widget.settings['line_width'])
        painter.setPen(pen)
        painter.drawRect(mag_x, mag_y, magnified.width(), magnified.height())


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
