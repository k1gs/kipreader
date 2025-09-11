import subprocess

def is_hekate_usb_connected():
    try:
        output = subprocess.check_output(
            'wmic diskdrive where "PNPDeviceID like \'%USB%\'" get PNPDeviceID,DeviceID,Caption /format:list',
            shell=True, encoding='utf-8', errors='ignore'
        )
        output_lower = output.lower()
        # Проверка на Hekate SD RAW USB Device по GUID
        hekate_guid = "{4d36e967-e325-11ce-bfc1-08002be10318}".lower()
        hekate_name = "hekate sd raw usb device"
        # fuck dont work sht.
        switch_name = "Switch"
        switch_guid = "{eec5ad98-8080-425f-922a-dabf3de3f69a}".lower()
        return (
            hekate_guid in output_lower or hekate_name in output_lower 
            (switch_name in output_lower and switch_guid in output_lower)
        )
    except Exception:
        return False

def is_wpd_device_connected():

    try:
        output = subprocess.check_output(
            'wmic path Win32_PnPEntity where "ClassGuid=\'{eec5ad98-8080-425f-922a-dabf3de3f69a}\'" get Name',
            shell=True, encoding='utf-8', errors='ignore'
        )
        lines = [line.strip() for line in output.splitlines() if line.strip()]
        return len(lines) > 1
    except Exception:
        return False

def is_mtp_device_connected():
    try:
        output = subprocess.check_output(
            'powershell "Get-WmiObject Win32_PnPEntity | Where-Object { $_.Service -eq \'WpdMtp\' } | Select-Object -ExpandProperty Name"',
            shell=True, encoding='utf-8', errors='ignore'
        )
        # иишная порверка девайса мтп
        return any(line.strip() for line in output.splitlines())
    except Exception:
        return False

def is_switch_mtp_connected():
    try:
        output = subprocess.check_output(
            'wmic path Win32_PnPEntity get Name', shell=True, encoding='utf-8', errors='ignore'
        )
        for line in output.splitlines():
            if "switch" in line.lower() or "mtp" in line.lower():
                return True
        return False
    except Exception:
        return False

