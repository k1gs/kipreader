from PyQt5.QtWidgets import QDialog, QFormLayout, QLineEdit, QDialogButtonBox

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

