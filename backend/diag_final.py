import os
import sys
import logging
from matching_engine_wrapper import gearboxNLP

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODELS_DIR = os.path.join(BASE_DIR, "trained_ML_models")
FT_MODEL_PATH = os.path.join(MODELS_DIR, "fasttext", "ft_embedding_size256_window5.model")
SVM_MODELS_DIR = os.path.join(MODELS_DIR, "SVMs", "classifier_models")

print(f"FT Path: {FT_MODEL_PATH}")
print(f"SVM Dir: {SVM_MODELS_DIR}")

try:
    print("Instantiating gearboxNLP...")
    engine = gearboxNLP(FT_MODEL_PATH, SVM_MODELS_DIR)
    print("Success!")
except Exception as e:
    print(f"CRITICAL ERROR: {e}")
    import traceback
    traceback.print_exc()
