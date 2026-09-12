"""Inference/serving script for image model — contains preprocessing bugs."""
import numpy as np
import json
import pickle


IMAGENET_MEAN = np.array([0.485, 0.456, 0.406], dtype=np.float32)
IMAGENET_STD = np.array([0.229, 0.224, 0.225], dtype=np.float32)


def preprocess_inference(images_hwc):
    """
    Inference preprocessing — BUGGY: inconsistent with training.
    """
    # BUG 1: Skipping channel transpose (sending HWC instead of CHW)
    images = images_hwc.astype(np.float32) / 255.0
    # Missing: images = (images - IMAGENET_MEAN) / IMAGENET_STD  (BUG 2: no ImageNet stats)
    # Missing: images = images.transpose(0, 3, 1, 2)  (BUG 1: no CHW transpose)
    return images.reshape(len(images), -1)  # Flattened HWC, not CHW


def predict(images_hwc):
    """Run inference on a batch."""
    with open("model.pkl", "rb") as f:
        model = pickle.load(f)

    # BUG 3: No batch dimension check — single images will have wrong shape
    if len(images_hwc.shape) == 3:
        # Should do: images_hwc = images_hwc[np.newaxis, ...]
        pass  # Bug: missing expand dims

    X = preprocess_inference(images_hwc)
    return model.predict(X)


def main():
    test_imgs = np.load("test_inputs.npy")
    ref_preds = np.load("test_predictions_reference.npy")

    preds = predict(test_imgs)

    try:
        agreement = (preds == ref_preds).mean()
    except Exception:
        agreement = 0.0

    results = {
        "n_samples": len(test_imgs),
        "agreement_with_training": float(agreement),
        "predictions_match": agreement > 0.95,
    }

    with open("serving_results.json", "w") as f:
        json.dump(results, f, indent=2)

    print(f"Agreement with training predictions: {agreement:.3f}")
    return results


if __name__ == "__main__":
    main()
