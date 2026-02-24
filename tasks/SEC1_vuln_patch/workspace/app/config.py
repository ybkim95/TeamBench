"""Application configuration."""

# CORS settings
CORS_ORIGINS = ["https://example.com"]
CORS_METHODS = ["GET", "POST"]
CORS_HEADERS = ["Content-Type", "Authorization"]

# General settings
MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB
UPLOAD_FOLDER = "uploads"
