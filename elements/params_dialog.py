from PyQt5.QtWidgets import QDialog, QFormLayout, QLabel, QScrollArea, QWidget, QVBoxLayout
from PyQt5.QtCore import Qt

class ParamsDialog(QDialog):
    def __init__(self, params, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Параметры кипа")
        self.setMinimumWidth(400)
        self.setMinimumHeight(500)

        if parent is not None and hasattr(parent, 'palette'):
            self.setPalette(parent.palette())
            self.setAutoFillBackground(True)
        self.setStyleSheet("""
            QLabel {
                font-size: 14px;
                padding: 2px;
            }
        """)
        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)
        content = QWidget()
        layout = QFormLayout(content)
        layout.setLabelAlignment(Qt.AlignRight)
        layout.setFormAlignment(Qt.AlignTop)
        grouped = {}
        for name, value, group in params:
            if group not in grouped:
                grouped[group] = []
            grouped[group].append((name, value))
        for group, items in grouped.items():
            group_label = QLabel(f"<b>{group}</b>")
            layout.addRow(group_label)
            for name, value in items:
                try:
                    dec_value = str(int(value, 16))
                except Exception:
                    dec_value = value
                layout.addRow(QLabel(name), QLabel(dec_value))
        scroll.setWidget(content)
        main_layout = QVBoxLayout(self)
        main_layout.addWidget(scroll)
        self.setLayout(main_layout)
        self.setWindowModality(Qt.NonModal)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowStaysOnTopHint)

