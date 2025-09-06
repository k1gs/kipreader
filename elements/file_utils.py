import os
import json

def edit_bytes_in_file(filename, offset, new_bytes):
    with open(filename, 'rb+') as f:
        f.seek(0)
        data = bytearray(f.read())
        data[offset:offset+len(new_bytes)] = new_bytes
        f.seek(0)
        f.write(data)

def load_material_options(material_filename):
    json_path = os.path.join("materials", material_filename)
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return [(item["name"], item["hex"]) for item in data]