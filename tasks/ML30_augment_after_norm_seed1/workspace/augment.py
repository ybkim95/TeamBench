"""Image augmentation pipeline — contains augment-after-normalize bug."""
import numpy as np

# Normalization statistics
MEAN = np.array([0.485, 0.456, 0.406], dtype=np.float32).reshape(-1, 1, 1)
STD  = np.array([0.229, 0.224, 0.225],  dtype=np.float32).reshape(-1, 1, 1)

IMG_SIZE = 28
N_CHANNELS = 3


def normalize(x: np.ndarray) -> np.ndarray:
    """Normalize image: (x - mean) / std. Expects x in [0, 1]."""
    return (x - MEAN) / STD


def random_horizontal_flip(x: np.ndarray, p: float = 0.5, rng=None) -> np.ndarray:
    """Flip image horizontally with probability p."""
    if rng is None:
        rng = np.random.RandomState()
    if rng.rand() < p:
        return x[:, :, ::-1].copy()
    return x


def random_crop(x: np.ndarray, pad: int = 3, rng=None) -> np.ndarray:
    """Pad then random crop back to original size."""
    if rng is None:
        rng = np.random.RandomState()
    C, H, W = x.shape
    # BUG (secondary): padding fills with 0.0, which is correct for [0,1]
    # but after normalize, 0.0 != black pixel (it's (0 - mean)/std < 0)
    padded = np.pad(x, ((0, 0), (pad, pad), (pad, pad)), mode='constant', constant_values=0.0)
    top  = rng.randint(0, 2 * pad + 1)
    left = rng.randint(0, 2 * pad + 1)
    return padded[:, top:top + H, left:left + W]


def apply_color_jitter(x: np.ndarray, brightness: float = 0.3,
                       contrast: float = 0.2, rng=None) -> np.ndarray:
    """Apply color jitter. Designed for x in [0, 1]."""
    if rng is None:
        rng = np.random.RandomState()
    # Brightness: designed for [0, 1] range
    b = 1.0 + rng.uniform(-brightness, brightness)
    x = x * b
    # Contrast: designed for [0, 1] range
    c = 1.0 + rng.uniform(-contrast, contrast)
    mean_val = x.mean()
    x = (x - mean_val) * c + mean_val
    return x


def apply_brightness(x: np.ndarray, delta: float = 0.2, rng=None) -> np.ndarray:
    """Apply brightness shift. Designed for x in [0, 1]."""
    if rng is None:
        rng = np.random.RandomState()
    shift = rng.uniform(-delta, delta)
    return x + shift


def train_transform(x: np.ndarray, rng=None) -> np.ndarray:
    """
    Training augmentation pipeline.

    BUG: normalize() is called FIRST, then augmentation transforms.
    After normalization, pixel values are in ~[-2, 2], but color_jitter
    and brightness are designed for [0, 1] inputs.

    Correct order: augment (flip, crop, color) THEN normalize.
    """
    if rng is None:
        rng = np.random.RandomState()
    x = x.astype(np.float32)

    # BUG: normalize BEFORE augmentation
    x = normalize(x)              # → values now in ~[-2, 2]

    # These transforms now operate on out-of-range normalized values
    x = random_horizontal_flip(x, p=0.5, rng=rng)
    x = random_crop(x, pad=3, rng=rng)
    # apply_color_jitter: adjust brightness on normalized data
    x = apply_color_jitter(x, brightness=0.3, contrast=0.2)

    return x


def val_transform(x: np.ndarray) -> np.ndarray:
    """Validation transform: normalize only (no augmentation)."""
    x = x.astype(np.float32)
    x = normalize(x)
    return x


def get_pipeline_order() -> str:
    """Return the order of operations in train_transform."""
    return "normalize,flip,crop,color"  # BUG: should be "flip,crop,color,normalize"
