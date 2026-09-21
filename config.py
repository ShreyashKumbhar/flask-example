import os

SECRET_KEY = os.environ.get("SECRET_KEY", "fdsafasd")
UPLOAD_FOLDER = os.environ.get("UPLOAD_FOLDER", "image_pool")
MAX_CONTENT_LENGTH = 16 * 1024 * 1024