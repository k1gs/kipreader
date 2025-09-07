import sys
import os
import subprocess
import json
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QLabel, QPushButton, QFileDialog, QMessageBox, QComboBox,
    QDialog, QLineEdit, QFormLayout, QDialogButtonBox, QProgressBar, QScrollArea, QFrame
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPalette, QBrush, QPixmap
from elements.file_utils import edit_bytes_in_file, load_material_options
from elements.ftp_utils import upload_file_via_ftp
from elements.device_check import is_mtp_device_connected, is_hekate_usb_connected
from elements.usb_utils import copy_file_to_switch

CUST_OFFSET = 0x41D87  # куст

def is_hekate_usb_connected():
    try:
        output = subprocess.check_output(
            'wmic diskdrive get Caption', shell=True, encoding='utf-8', errors='ignore'
        )
        return any("hekate SD RAW USB Device".lower() in line.lower() for line in output.splitlines())
    except Exception:
        return False

def load_kips_by_class(class_name):
    with open("kips.json", "r", encoding="utf-8") as f:
        data = json.load(f)
    return [item for item in data if item.get("class") == class_name]

class FTPDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Загрузка по FTP")
        self.layout = QFormLayout(self)

        self.ip_edit = QLineEdit()
        self.port_edit = QLineEdit()
        self.port_edit.setText("21")
        self.user_edit = QLineEdit()
        self.user_edit.setText("anonymous")
        self.pass_edit = QLineEdit()
        self.pass_edit.setEchoMode(QLineEdit.Password)
        self.pass_edit.setText("")

        self.layout.addRow("IP адрес:", self.ip_edit)
        self.layout.addRow("Порт:", self.port_edit)

        self.buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)
        self.layout.addWidget(self.buttons)

    def get_data(self):
        return (
            self.ip_edit.text(),
            int(self.port_edit.text()),
            self.user_edit.text(),
            self.pass_edit.text()
        )

class ByteEditor(QWidget):
    def __init__(self, device_found):
        super().__init__()
        self.setObjectName("MainWindow")

        background_path = os.path.abspath("back1.png")
        if os.path.exists(background_path):
            palette = QPalette()
            pixmap = QPixmap(background_path).scaled(self.size(), Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
            palette.setBrush(QPalette.Window, QBrush(pixmap))
            self.setPalette(palette)
            self.setAutoFillBackground(True)

        content_frame = QFrame()
        content_frame.setObjectName("ContentFrame")
        content_frame.setMaximumWidth(600)
        content_frame.setMinimumWidth(400)
        main_layout = QVBoxLayout(content_frame)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(120, 80, 120, 80)  # большие отступы!
        layout.addWidget(content_frame, alignment=Qt.AlignCenter)

        title = QLabel("KIP Byte Editor")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 22px; font-weight: bold; margin-bottom: 10px;")
        main_layout.addWidget(title)

        self.class_label = QLabel("Выберите класс параметров:")
        main_layout.addWidget(self.class_label)

        self.class_combo = QComboBox()
        self.class_combo.addItems(self.get_classes())
        self.class_combo.currentIndexChanged.connect(self.update_params)
        main_layout.addWidget(self.class_combo)

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_content = QWidget()
        self.param_layout = QVBoxLayout(self.scroll_content)
        self.param_layout.setAlignment(Qt.AlignTop)
        self.scroll_area.setWidget(self.scroll_content)
        main_layout.addWidget(self.scroll_area, stretch=1)

        self.param_widgets = []

        btn_frame = QFrame()
        btn_layout = QVBoxLayout(btn_frame)
        btn_layout.setSpacing(10)

        self.btn = QPushButton("Изменить байт(ы)")
        self.btn.clicked.connect(self.edit_bytes)
        btn_layout.addWidget(self.btn)

        self.open_btn = QPushButton("Открыть файл")
        self.open_btn.clicked.connect(self.open_file)
        btn_layout.addWidget(self.open_btn)

        self.ftp_btn = QPushButton("Передать по FTP")
        self.ftp_btn.clicked.connect(self.upload_via_ftp)
        btn_layout.addWidget(self.ftp_btn)

        self.send_ready_ftp_btn = QPushButton("Передать готовый файл по FTP")
        self.send_ready_ftp_btn.clicked.connect(self.send_ready_file_via_ftp)
        btn_layout.addWidget(self.send_ready_ftp_btn)

        self.usb_btn = QPushButton("Отправить на Switch по USB")
        self.usb_btn.clicked.connect(self.send_to_switch_usb)
        btn_layout.addWidget(self.usb_btn)

        main_layout.addWidget(btn_frame)

        self.progress = QProgressBar()
        self.progress.setValue(0)
        main_layout.addWidget(self.progress)

        self.filename = None
        self.update_params()

        if not device_found:
            self.usb_btn.hide()
            self.ftp_btn.show()
            self.send_ready_ftp_btn.show()
            QMessageBox.information(self, "Внимание", "Switch не обнаружен! Используйте передачу по FTP.")
        else:
            self.usb_btn.show()
            self.ftp_btn.hide()
            self.send_ready_ftp_btn.show()

        self.setStyleSheet(f"""
            #MainWindow {{
                background-repeat: no-repeat;
                background-position: center;
            }}
            QFrame#ContentFrame {{
                background: rgba(255,255,255,0.5);
                border-radius: 16px;
            }}
        """)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowMaximizeButtonHint)
        self.setWindowTitle("KIPREADER")

    def get_classes(self):
        with open("kips.json", "r", encoding="utf-8") as f:
            data = json.load(f)
        return sorted(set(item.get("class", "") for item in data if "class" in item and item.get("class")))

    def update_params(self):
        for widget in self.param_widgets:
            self.param_layout.removeWidget(widget['label'])
            widget['label'].deleteLater()
            self.param_layout.removeWidget(widget['combo'])
            widget['combo'].deleteLater()
        self.param_widgets.clear()

        class_name = self.class_combo.currentText()
        self.kip_params = load_kips_by_class(class_name)
        self.kip_params.sort(key=lambda x: x.get("name_of_param", ""))

        for param in self.kip_params:
            label = QLabel(param.get("name_of_param", "Параметр"))
            label.setStyleSheet("font-size: 14px; margin-top: 8px;")
            combo = QComboBox()
            options = load_material_options(param["name"])
            for name, hex_value in options:
                combo.addItem(name, hex_value)
            self.param_layout.addWidget(label)
            self.param_layout.addWidget(combo)
            self.param_widgets.append({'label': label, 'combo': combo, 'param': param})

    def open_file(self):
        fname, _ = QFileDialog.getOpenFileName(self, "Выберите файл", "", "All Files (*)")
        if fname:
            self.filename = fname

    def edit_bytes(self):
        if not self.filename:
            QMessageBox.warning(self, "Внимание", "Сначала выберите файл!")
            return
        try:
            for widget in self.param_widgets:
                param = widget['param']
                rel_offset = int(param.get("hex_by_cust_offset", 0))
                offset = CUST_OFFSET + rel_offset
                hex_value = widget['combo'].currentData()
                new_bytes = bytes.fromhex(hex_value)
                edit_bytes_in_file(self.filename, offset, new_bytes)
            QMessageBox.information(self, "Успех", "Байт(ы) успешно изменён(ы)!")
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", str(e))

    def upload_via_ftp(self):
        if not self.filename:
            QMessageBox.warning(self, "Внимание", "Сначала выберите файл!")
            return
        dlg = FTPDialog(self)
        if dlg.exec_() == QDialog.Accepted:
            ip, port, user, pwd = dlg.get_data()
            remote_path = "/atmosphere/kips/" + os.path.basename(self.filename)
            self.progress.setValue(0)
            def progress_callback(sent, total):
                percent = int(sent * 100 / total)
                self.progress.setValue(percent)
            ok, msg = upload_file_via_ftp(
                ip, port, user, pwd, self.filename, remote_path, progress_callback
            )
            if ok:
                QMessageBox.information(self, "Успех", msg)
            else:
                QMessageBox.critical(self, "Ошибка", msg)
            self.progress.setValue(0)

    def send_to_switch_usb(self):
        if not self.filename:
            QMessageBox.warning(self, "Внимание", "Сначала выберите файл!")
            return
        ok, msg = copy_file_to_switch(self.filename)
        if ok:
            QMessageBox.information(self, "Успех", msg)
        else:
            QMessageBox.critical(self, "Ошибка", msg)

    def send_ready_file_via_ftp(self):
        fname, _ = QFileDialog.getOpenFileName(self, "Выберите файл для отправки", "", "All Files (*)")
        if not fname:
            return
        dlg = FTPDialog(self)
        if dlg.exec_() == QDialog.Accepted:
            ip, port, user, pwd = dlg.get_data()
            remote_path = "/atmosphere/kips/" + os.path.basename(fname)
            self.progress.setValue(0)
            def progress_callback(sent, total):
                percent = int(sent * 100 / total)
                self.progress.setValue(percent)
            ok, msg = upload_file_via_ftp(
                ip, port, user, pwd, fname, remote_path, progress_callback
            )
            if ok:
                QMessageBox.information(self, "Успех", msg)
            else:
                QMessageBox.critical(self, "Ошибка", msg)
            self.progress.setValue(0)

    def resizeEvent(self, event):
        background_path = os.path.abspath("back1.png")
        if os.path.exists(background_path):
            pixmap = QPixmap(background_path).scaled(self.size(), Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
            palette = self.palette()
            palette.setBrush(QPalette.Window, QBrush(pixmap))
            self.setPalette(palette)
        super().resizeEvent(event)

def resource_path(relative_path):
    """Возвращает абсолютный путь к ресурсу, работает и для PyInstaller, и для обычного запуска."""
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)

materials_dir = resource_path("materials")
if os.path.exists(materials_dir):
    for fname in os.listdir(materials_dir):
        fpath = os.path.join(materials_dir, fname)
        if os.path.isfile(fpath):
            with open(fpath, "r", encoding="utf-8") as f:
                # обработка файла
                ...
else:
    print("Папка materials не найдена!")

with open(resource_path("kips.json"), "r", encoding="utf-8") as f:
    data = json.load(f)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    try:
        device_found = is_hekate_usb_connected()
    except Exception:
        device_found = False

    window = ByteEditor(device_found)
    window.show()
    sys.exit(app.exec_())