import sys
from PyQt5.QtWidgets import QApplication
from elements.byte_editor import ByteEditor
from elements.utils import is_hekate_usb_connected

if __name__ == "__main__":
    app = QApplication(sys.argv)
    try:
        device_found = is_hekate_usb_connected()
    except Exception:
        device_found = False

    window = ByteEditor(device_found)
    window.show()
    sys.exit(app.exec_())