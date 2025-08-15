import cloudinary
import cloudinary.uploader
import cloudinary.api
from flask import current_app

def init_cloudinary():
    """
    No necesitas pasar credenciales si ya tienes CLOUDINARY_URL en variables
    de entorno (Render/tu .env). Cloudinary lo detecta automáticamente.
    """
    cloudinary.config(secure=True)  # URLs https

def upload_image(file_or_bytes, public_id_prefix: str):
    """
    Sube una imagen/bytes a Cloudinary.
    file_or_bytes: archivo de Flask (FileStorage) o bytes (io.BytesIO.getvalue()).
    public_id_prefix: ej. 'productos/1234'  (Cloudinary agregará extensión)
    """
    init_cloudinary()
    res = cloudinary.uploader.upload(
        file_or_bytes,
        public_id=public_id_prefix,
        overwrite=True,
        unique_filename=False,
        resource_type="image",
        folder=""  # opcional si ya pasas public_id con prefijo de carpeta
    )
    # Respuesta típica: {public_id, secure_url, ...}
    return res["public_id"], res["secure_url"]

def delete_image(public_id: str):
    if not public_id:
        return
    init_cloudinary()
    try:
        cloudinary.uploader.destroy(public_id, resource_type="image")
    except Exception:
        pass
