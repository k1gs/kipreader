import sys
import os
import subprocess
import json
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QLabel, QPushButton, QFileDialog, QMessageBox, QComboBox,
    QDialog, QLineEdit, QFormLayout, QDialogButtonBox, QProgressBar
)
from file_utils import edit_bytes_in_file, load_material_options
from ftp_utils import upload_file_via_ftp

from device_check import is_mtp_device_connected, is_hekate_usb_connected
from usb_utils import copy_file_to_switch

KUST_OFFSET = 0x41D87  # куст

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
        self.layout.addRow("Пользователь:", self.user_edit)
        self.layout.addRow("Пароль:", self.pass_edit)

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
        self.setWindowTitle("KIP Byte Editor")
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

        self.class_label = QLabel("Выберите класс параметров:")
        self.layout.addWidget(self.class_label)

        self.class_combo = QComboBox()
        self.class_combo.addItems(self.get_classes())
        self.class_combo.currentIndexChanged.connect(self.update_params)
        self.layout.addWidget(self.class_combo)

        self.param_widgets = []
        self.param_layout = QVBoxLayout()
        self.layout.addLayout(self.param_layout)

        self.btn = QPushButton("Изменить байт(ы)")
        self.btn.clicked.connect(self.edit_bytes)
        self.layout.addWidget(self.btn)

        self.open_btn = QPushButton("Открыть файл")
        self.open_btn.clicked.connect(self.open_file)
        self.layout.addWidget(self.open_btn)

        # check dev
        self.device_found = device_found

        # Ftp button 
        self.ftp_btn = QPushButton("Передать по FTP")
        self.ftp_btn.clicked.connect(self.upload_via_ftp)
        self.layout.addWidget(self.ftp_btn)

        # Кнопка "Передать готовый файл по FTP"
        self.send_ready_ftp_btn = QPushButton("Передать готовый файл по FTP")
        self.send_ready_ftp_btn.clicked.connect(self.send_ready_file_via_ftp)
        self.layout.addWidget(self.send_ready_ftp_btn)

        # Кнопка USB только если устройство найдено
        self.usb_btn = QPushButton("Отправить на Switch по USB")
        self.usb_btn.clicked.connect(self.send_to_switch_usb)
        self.layout.addWidget(self.usb_btn)

        self.progress = QProgressBar()
        self.progress.setValue(0)
        self.layout.addWidget(self.progress)

        self.filename = None
        self.update_params()

        # hide buttons если девайс не в усб
        if not device_found:
            self.usb_btn.hide()
            self.ftp_btn.show()
            self.send_ready_ftp_btn.show()
            QMessageBox.information(self, "Внимание", "Switch не обнаружен! Используйте передачу по FTP.")
        else:
            self.usb_btn.show()
            self.ftp_btn.hide()
            self.send_ready_ftp_btn.show()

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

        for param in self.kip_params:
            label = QLabel(param.get("name_of_param", "Параметр"))
            combo = QComboBox()
            # иишная поебень (переписать)
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
                # hex_by_cust_offset — смещение ОТ куста
                rel_offset = int(param.get("hex_by_cust_offset", 0))
                offset = KUST_OFFSET + rel_offset
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

if __name__ == "__main__":
    app = QApplication(sys.argv)
    try:
        device_found = is_hekate_usb_connected()
    except Exception:
        device_found = False

    window = ByteEditor(device_found)
    window.show()
    sys.exit(app.exec_())