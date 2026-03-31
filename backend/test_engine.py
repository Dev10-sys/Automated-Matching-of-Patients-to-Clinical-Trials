import os
from matching_engine_wrapper import gearboxNLP

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODELS_DIR = os.path.join(BASE_DIR, "trained_ML_models")
FT_MODEL_PATH = os.path.join(MODELS_DIR, "fasttext", "ft_embedding_size256_window5.model")
SVM_MODELS_DIR = os.path.join(MODELS_DIR, "SVMs", "classifier_models")

print("Initializing engine...")
engine = gearboxNLP(FT_MODEL_PATH, SVM_MODELS_DIR)
print("Engine initialized.")

patient = {
    "Age (Days)": 5000,
    "Diagnosis": "ALL"
}

print("Running match...")
results = engine.Match(patient, docx_trials=[], ctgov_trials=["NCT00002547"])
print("Results:")
print(results)
