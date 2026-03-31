import os
import sys
import logging

# Add project root to path
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from matching_engine_wrapper import gearboxNLP

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODELS_DIR = os.path.join(BASE_DIR, "trained_ML_models")
FT_MODEL_PATH = os.path.join(MODELS_DIR, "fasttext", "ft_embedding_size256_window5.model")
SVM_MODELS_DIR = os.path.join(MODELS_DIR, "SVMs", "classifier_models")

print(f"FT_MODEL_PATH: {FT_MODEL_PATH}")
print(f"File exists: {os.path.exists(FT_MODEL_PATH)}")

try:
    print("Initializing matching engine...")
    engine = gearboxNLP(FT_MODEL_PATH, SVM_MODELS_DIR)
    print("Matching engine initialized successfully.")
    
    patient = {"Age (Days)": 5000, "Diagnosis": "ALL"}
    results = engine.Match(patient, docx_trials=[], ctgov_trials=["NCT03817320"])
    print("Match successful!")
    print(results)
except Exception as e:
    import traceback
    print("Failed to initialize or match:")
    traceback.print_exc()
