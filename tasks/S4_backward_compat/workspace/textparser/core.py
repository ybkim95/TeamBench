"""
Core implementation of TextParser.

IMPORTANT: This is a stable v1 library. Backward compatibility is critical.
Do NOT change any existing public method signatures or return value shapes.
"""
import warnings


class TextParser:
    """
    Main class for the library. v1 stable API.

    Args:
        config: Optional configuration. Accepts None (default), str, or dict.
    """

    __version__ = "1.8.3"

    def __init__(self, config=None):
        self._config = self._parse_config(config)
        self._initialized = True

    def _parse_config(self, config):
        """Parse config accepting None, str, or dict (all legacy formats)."""
        if config is None:
            return {}
        if isinstance(config, str):
            # Legacy string config: "key=value,key2=value2"
            result = {}
            for part in config.split(","):
                part = part.strip()
                if "=" in part:
                    k, v = part.split("=", 1)
                    result[k.strip()] = v.strip()
            return result
        if isinstance(config, dict):
            return dict(config)
        raise ValueError("Invalid input: config must be None, str, or dict")

    def process(self, data):
        """
        Process the given data and return a result dict.

        Returns:
            dict with keys: 'result', 'status', 'version'
        """
        if data is None:
            raise ValueError("Invalid input: data cannot be None")
        if not isinstance(data, (str, int, float, list, dict)):
            raise RuntimeError(f"Unsupported data type: {type(data).__name__}")

        processed = self._do_process(data)
        return {
            "result": processed,
            "status": "ok",
            "version": "1",
        }

    def _do_process(self, data):
        """Internal processing logic."""
        if isinstance(data, str):
            return data.strip()
        if isinstance(data, (int, float)):
            return data
        if isinstance(data, list):
            return [self._do_process(item) for item in data]
        if isinstance(data, dict):
            return {k: self._do_process(v) for k, v in data.items()}
        return data

    def run(self, data):
        """
        Deprecated alias for process(). Kept for backward compatibility.

        .. deprecated::
            Use process() instead. This alias will be removed in v2.0.
        """
        warnings.warn(
            "run() is deprecated, use process() instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        return self.process(data)

    def get_config(self):
        """Return current configuration dict."""
        return dict(self._config)

    def reset(self):
        """Reset to default configuration."""
        self._config = {}
