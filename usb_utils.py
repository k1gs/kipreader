import os
import shutil

def copy_file_to_switch(local_filepath):
    drive = "E:"
    dest_dir = os.path.join(drive + os.sep, "atmosphere", "kips")
    os.makedirs(dest_dir, exist_ok=True)
    dest_path = os.path.join(dest_dir, os.path.basename(local_filepath))
    try:
        shutil.copy2(local_filepath, dest_path)
        # 支票 
        if os.path.exists(dest_path):
            orig_size = os.path.getsize(local_filepath)
            dest_size = os.path.getsize(dest_path)
            if orig_size == dest_size:
                return True, f"Файл успешно скопирован: {dest_path}\nРазмер: {dest_size} байт"
            else:
                return False, f"Размер файла не совпадает! Оригинал: {orig_size}, на Switch: {dest_size}"
        else:
            return False, "Файл не найден на целевом устройстве после копирования!"
    except Exception as e:
        return False, f"Ошибка копирования: {e}"