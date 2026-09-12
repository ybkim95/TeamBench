"""Training script for image model — saves normalization stats."""
import numpy as np
import json
import pickle
from sklearn.ensemble import RandomForestClassifier


N_CLASSES = 5
IMG_H, IMG_W, IMG_C = 8, 8, 3  # Small synthetic images
IMAGENET_MEAN = np.array([0.485, 0.456, 0.406], dtype=np.float32)
IMAGENET_STD = np.array([0.229, 0.224, 0.225], dtype=np.float32)


def preprocess_training(images_hwc):
    """Training preprocessing pipeline."""
    # images_hwc: (N, H, W, C) uint8
    # Step 1: Normalize to [0,1]
    images = images_hwc.astype(np.float32) / 255.0
    # Step 2: Apply ImageNet stats (per channel)
    images = (images - IMAGENET_MEAN) / IMAGENET_STD
    # Step 3: Transpose to CHW (N, C, H, W) for the model
    images = images.transpose(0, 3, 1, 2)
    # Step 4: Flatten for sklearn model
    return images.reshape(len(images), -1)


def train(seed=2):
    np.random.seed(seed)
    N = 989
    # Synthetic images: (N, H, W, C)
    images = np.random.randint(0, 256, (N, IMG_H, IMG_W, IMG_C), dtype=np.uint8)
    # Create labels based on mean brightness per class
    brightness = images.mean(axis=(1,2,3))
    y = (brightness / (255.0 / N_CLASSES)).astype(int).clip(0, N_CLASSES-1)

    X = preprocess_training(images)
    clf = RandomForestClassifier(n_estimators=30, random_state=seed)
    clf.fit(X, y)
    acc = clf.score(X, y)
    print(f"Training accuracy: {acc:.3f}")

    with open("model.pkl", "wb") as f:
        pickle.dump(clf, f)

    artifacts = {
        "imagenet_mean": IMAGENET_MEAN.tolist(),
        "imagenet_std": IMAGENET_STD.tolist(),
        "input_format": "CHW",
        "normalize_range": [0, 1],
        "img_size": [IMG_H, IMG_W, IMG_C],
    }
    with open("preprocessing_artifacts.json", "w") as f:
        json.dump(artifacts, f, indent=2)

    # Reference: save a few test images
    test_imgs = images[:10]
    np.save("test_inputs.npy", test_imgs)
    test_X = preprocess_training(test_imgs)
    np.save("test_predictions_reference.npy", clf.predict(test_X))
    print("Saved model.pkl, preprocessing_artifacts.json")
    return acc


if __name__ == "__main__":
    train()
