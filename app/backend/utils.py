import hashlib
import qrcode
import json
from io import BytesIO
from typing import BinaryIO


def calculate_file_hash(file_content: bytes) -> str:
    sha256_hash = hashlib.sha256()
    sha256_hash.update(file_content)
    return sha256_hash.hexdigest()


def generate_qr_code(record_id: str, tx_hash: str, frontend_url: str) -> bytes:
    verify_url = f"{frontend_url}/verify/{record_id}"
    qr_data = {"record_id": record_id, "tx_hash": tx_hash, "verify_url": verify_url}
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(json.dumps(qr_data))
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    img_byte_arr = BytesIO()
    img.save(img_byte_arr, format="PNG")
    img_byte_arr.seek(0)
    return img_byte_arr.getvalue()