"""TLS handler — currently disabled for 'performance'."""
import ssl


def get_tls_context(cert_path=None, key_path=None):
    """Get TLS context for the server.

    Currently returns None (TLS disabled) because enabling TLS
    was thought to add too much latency.

    With session caching, TLS overhead is only ~10ms per request.
    """
    if not cert_path or not key_path:
        return None

    context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    context.load_cert_chain(cert_path, key_path)
    return context
