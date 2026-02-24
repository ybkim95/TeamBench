"""Application constants — DO NOT MODIFY for requests migration."""

# Rate limiting
TIMEOUT = 60  # seconds — general timeout for rate limiter, NOT requests library config
MAX_RETRIES = 3
BATCH_SIZE = 100
PAGE_SIZE = 50

# API versioning
API_VERSION = "v2"
API_PREFIX = f"/api/{API_VERSION}"
