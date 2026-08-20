import os
from django.core.exceptions import ValidationError

DANGEROUS_EXTENSIONS = {
    '.exe', '.dll', '.so', '.sh', '.bat', '.cmd', '.vbs', '.js', '.jsx',
    '.ts', '.tsx', '.php', '.phtml', '.php3', '.php4', '.php5', '.phps',
    '.cgi', '.pl', '.py', '.pyc', '.pyo', '.asp', '.aspx', '.jsp', '.html',
    '.htm', '.xhtml', '.htaccess', '.htpasswd', '.config'
}

ALLOWED_DOC_EXTENSIONS = {
    '.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx',
    '.txt', '.csv', '.rtf', '.odt', '.ods', '.odp', '.zip', '.rar',
    '.7z', '.png', '.jpg', '.jpeg', '.gif', '.webp', '.svg'
}

ALLOWED_IMAGE_EXTENSIONS = {
    '.png', '.jpg', '.jpeg', '.gif', '.webp'
}

MAX_FILE_SIZE_BYTES = 20 * 1024 * 1024  # 20 MB max limit

def validate_secure_file_extension(value):
    """
    Ensure uploaded files do not have executable or malicious script extensions.
    """
    ext = os.path.splitext(value.name)[1].lower()
    if ext in DANGEROUS_EXTENSIONS:
        raise ValidationError(
            f"Les fichiers de type '{ext}' sont strictement interdits pour des raisons de sécurité."
        )
    if ext not in ALLOWED_DOC_EXTENSIONS:
        raise ValidationError(
            f"Format de fichier '{ext}' non autorisé. Formats acceptés : PDF, DOCX, XLSX, PPTX, TXT, ZIP, Images."
        )

def validate_avatar_image(value):
    """
    Ensure uploaded avatars are valid images.
    """
    ext = os.path.splitext(value.name)[1].lower()
    if ext not in ALLOWED_IMAGE_EXTENSIONS:
        raise ValidationError(
            "L'avatar doit être une image au format PNG, JPG, JPEG, GIF ou WEBP."
        )

def validate_file_size(value):
    """
    Restrict maximum file size to 20MB.
    """
    if value.size > MAX_FILE_SIZE_BYTES:
        raise ValidationError(
            "La taille du fichier ne peut pas dépasser 20 Mo."
        )
