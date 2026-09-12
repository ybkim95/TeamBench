# DEPRECATED PIPELINE
# This script is no longer used. See augment_pipeline.py instead.
# Contains known bugs and linting errors.

import numpy as np

def bad_augmentation(X):
    print("Applying bad augmentation")
    return X + np.random.normal(0, 1, size=X.shape) # Missing random seed

if __name__ == '__main__':
    print('Done')
