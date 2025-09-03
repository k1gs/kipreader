import subprocess
import os
import shutil

def find_switch_drive():
    """
    E: for mtp
    """
    try:
        output = subprocess.check_output(
            'wmic logicaldisk get DeviceID,VolumeName', shell=True, encoding='utf-8', errors='ignore'
        )
        for line in output.splitlines():
            if "Switch" in line:
                parts = line.split()
                if parts:
                    return parts[0]  # в теории должно возвращать букву диска, на деле хуйня
    except Exception:
        pass
    return None

def copy_file_to_switch(local_filepath):
    drive = find_switch_drive()
    if not drive:
        return False, "Switch не найден"
    dest_dir = os.path.join(drive + os.sep, "atmosphere", "kips")
    os.makedirs(dest_dir, exist_ok=True)
    dest_path = os.path.join(dest_dir, os.path.basename(local_filepath))
    try:
        shutil.copy2(local_filepath, dest_path)
        return True, f"Файл скопирован: {dest_path}"
    except Exception as e:
        return False, str(e)