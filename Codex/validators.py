import os
from django.core.exceptions import ValidationError
from PIL import Image

DANGEROUS_EXTENSIONS = {
    '.exe', '.dll', '.so', '.sh', '.bat', '.cmd', '.vbs', '.js', '.jsx',
    '.ts', '.tsx', '.php', '.phtml', '.php3', '.php4', '.php5', '.phps',
    '.phar', '.pht', '.cgi', '.pl', '.py', '.pyc', '.pyo', '.asp', '.aspx',
    '.jsp', '.jspx', '.html', '.htm', '.xhtml', '.shtml', '.svg', '.svgz',
    '.xml', '.htaccess', '.htpasswd', '.config', '.env', '.ini', '.wasm'
}

ALLOWED_DOC_EXTENSIONS = {
    '.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx',
    '.txt', '.csv', '.rtf', '.odt', '.ods', '.odp', '.zip', '.rar',
    '.7z', '.png', '.jpg', '.jpeg', '.gif', '.webp'
}

ALLOWED_IMAGE_EXTENSIONS = {
    '.png', '.jpg', '.jpeg', '.gif', '.webp'
}

ALLOWED_PIL_FORMATS = {'PNG', 'JPEG', 'GIF', 'WEBP'}

MAX_FILE_SIZE_BYTES = 20 * 1024 * 1024  # 20 MB max limit


def validate_secure_file_extension(value):
    """
    Ensure uploaded files do not have executable, script, or malicious extensions,
    and prevent null bytes and dangerous double extensions.
    """
    filename = getattr(value, 'name', '')
    if not filename:
        return

    # Check for null bytes or path traversal in filename
    if '\x00' in filename or '..' in filename:
        raise ValidationError("Nom de fichier invalide ou potentiellement malveillant.")

    # Check all extension segments (e.g. malicious.php.pdf or exploit.exe.png)
    name_parts = filename.lower().split('.')
    if len(name_parts) > 1:
        for part in name_parts[1:]:
            ext_part = f".{part}"
            if ext_part in DANGEROUS_EXTENSIONS:
                raise ValidationError(
                    f"Le fichier contient une extension non autorisée ('{ext_part}'). Téléversement refusé pour des raisons de sécurité."
                )

    # Check final extension
    final_ext = os.path.splitext(filename)[1].lower()
    if not final_ext or final_ext not in ALLOWED_DOC_EXTENSIONS:
        raise ValidationError(
            f"Format de fichier '{final_ext}' non autorisé. Formats acceptés : PDF, DOCX, XLSX, PPTX, TXT, ZIP, Images."
        )


def validate_avatar_image(value):
    """
    Ensure uploaded avatars are valid images both by extension and by inspecting
    image binary headers via Pillow (prevents file masquerading / polyglot attacks).
    """
    filename = getattr(value, 'name', '')
    if not filename:
        return

    if '\x00' in filename or '..' in filename:
        raise ValidationError("Nom de fichier invalide.")

    ext = os.path.splitext(filename)[1].lower()
    if ext not in ALLOWED_IMAGE_EXTENSIONS:
        raise ValidationError(
            "L'avatar doit être une image au format PNG, JPG, JPEG, GIF ou WEBP."
        )

    # Binary image header verification
    try:
        image = Image.open(value)
        image.verify()
        if image.format not in ALLOWED_PIL_FORMATS:
            raise ValidationError("Format d'image non supporté.")
    except Exception:
        raise ValidationError(
            "Le fichier téléversé n'est pas une image valide ou est corrompu."
        )
    finally:
        # Reset file pointer after Pillow verification
        if hasattr(value, 'seek'):
            value.seek(0)


def validate_file_size(value):
    """
    Restrict maximum file size to 20MB.
    """
    if getattr(value, 'size', 0) > MAX_FILE_SIZE_BYTES:
        raise ValidationError(
            "La taille du fichier ne peut pas dépasser 20 Mo."
        )
