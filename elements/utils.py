import os
import subprocess
import json
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

def read_bytes_from_file(filename, offset, length):
    with open(filename, "rb") as f:
        f.seek(offset)
        return f.read(length)

