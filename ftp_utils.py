from ftplib import FTP, error_perm
import os

def upload_file_via_ftp(server, port, username, password, local_filepath, remote_filepath, progress_callback=None):
    try:
        with FTP() as ftp:
            ftp.connect(server, port, timeout=10)
            ftp.login(user=username, passwd=password)
            total_size = os.path.getsize(local_filepath)
            sent = 0

            def handle(block):
                nonlocal sent
                sent += len(block)
                if progress_callback:
                    progress_callback(sent, total_size)

            with open(local_filepath, 'rb') as f:
                ftp.storbinary(f'STOR ' + remote_filepath, f, 1024, callback=handle)
        return True, "Файл успешно загружен!"
    except error_perm as e:
        return False, f"Ошибка FTP: {e}"
    except Exception as e:
        return False, str(e)