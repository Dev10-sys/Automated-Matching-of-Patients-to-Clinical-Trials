import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import pandas as pd
import logging
from matching_engine_wrapper import gearboxNLP

from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import uvicorn

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="GEARBOx Clinical Trial Matching API")

# Setup folder paths
BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BACKEND_DIR, "static")
BASE_DIR = os.path.dirname(BACKEND_DIR)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Constants
MODELS_DIR = os.path.join(BASE_DIR, "trained_ML_models")
FT_MODEL_PATH = os.path.join(MODELS_DIR, "fasttext", "ft_embedding_size256_window5.model")
SVM_MODELS_DIR = os.path.join(MODELS_DIR, "SVMs", "classifier_models")
PROJECT_DATA_DIR = os.path.join(BASE_DIR, "project_data")
TRIAL_METADATA_PATH = os.path.join(PROJECT_DATA_DIR, "trial_metadata.csv")

# Initialize matching engine
engine = None
engine_initialization_error = None

def get_engine():
    global engine, engine_initialization_error
    if engine is not None:
        return engine
    
    try:
        logger.info("Initializing matching engine (lazy load)...")
        engine = gearboxNLP(FT_MODEL_PATH, SVM_MODELS_DIR)
        logger.info("Matching engine initialized successfully.")
        return engine
    except Exception as e:
        engine_initialization_error = str(e)
        logger.error(f"Failed to initialize matching engine: {e}")
        return None

@app.on_event("startup")
async def startup_event():
    # Initialize engine synchronously for better error capture
    get_engine()

class PatientData(BaseModel):
    filters: Dict[str, Any]

@app.get("/filters")
async def get_filters():
    """Returns available filter fields for patient data."""
    # Based on the fields identified in the matching engine logic
    return [
        {"id": "Age (Days)", "label": "Age (Days)", "type": "number"},
        {"id": "Height (cm)", "label": "Height (cm)", "type": "number"},
        {"id": "Performance Status (Lanksy/Karnofsky)", "label": "Performance Status (0-100)", "type": "number"},
        {"id": "Diagnosis", "label": "Diagnosis", "type": "text"},
        {"id": "African-American", "label": "African-American", "type": "boolean"},
        {"id": "Female", "label": "Female", "type": "boolean"},
        {"id": "Creatinine (mg/dL)", "label": "Creatinine (mg/dL)", "type": "number"},
        {"id": "CNS Involvement (1/2/3)", "label": "CNS Involvement (1/2/3)", "type": "number"},
        {"id": "Isolated CNS Disease", "label": "Isolated CNS Disease", "type": "boolean"},
        {"id": "Days Since Cytotoxic Chemotherapy", "label": "Days Since Chemotherapy", "type": "number"},
        {"id": "Days Since Biologic Therapy", "label": "Days Since Biologic Therapy", "type": "number"},
        {"id": "Days Since Growth Factor Therapy", "label": "Days Since Growth Factor Therapy", "type": "number"},
        {"id": "Days Since Prior Radiotherapy", "label": "Days Since Radiotherapy", "type": "number"},
        {"id": "Days Since Corticosteroids", "label": "Days Since Corticosteroids", "type": "number"},
        {"id": "Direct Bilirubin Times ULN", "label": "Direct Bilirubin Times ULN", "type": "number"},
        {"id": "AST/ALT Times ULN", "label": "AST/ALT Times ULN", "type": "number"},
        {"id": "Impaired Cardiovascular Function/Cardiotoxicity from Chemotherapy", "label": "Impaired Cardiac Function", "type": "boolean"},
        {"id": "Active and/or Uncontrolled Viral, Bacterial, or Fungal Infection", "label": "Active Infection", "type": "boolean"},
        {"id": "Pregnant, Nursing, or Fertile and Unwilling to Use Contraception", "label": "Pregnancy/Fertility/Contraception Issues", "type": "boolean"},
    ]

@app.post("/match")
async def match_trials(patient_data: PatientData):
    """Matches a patient to clinical trials using the engine."""
    current_engine = get_engine()
    if current_engine is None:
        raise HTTPException(status_code=503, detail=f"Matching engine is not initialized. Error: {engine_initialization_error}")
    
    try:
        # Load NCT IDs and metadata from local CSV
        df_trials = pd.read_csv(TRIAL_METADATA_PATH)
        
        # Use existing criteria from the CSV instead of downloading them
        # This is much faster and more reliable
        results = []

        for _, row in df_trials.iterrows():
            try:
                # Prepare trial info dict from local data
                trial_info = {
                    "NCT_id": row["nct_id"],
                    "condition": [str(row["condition"])],
                    "./eligibility/minimum_age": str(row["./eligibility/minimum_age"]),
                    "./eligibility/maximum_age": str(row["./eligibility/maximum_age"]),
                    "./eligibility/criteria/textblock": str(row["./eligibility/criteria/textblock"])
                }
                
                # Match using the engine's internal scoring but on pre-loaded data
                raw_text = trial_info["./eligibility/criteria/textblock"]
                ext_criteria = engine.ExtractCriteria(text=raw_text, mode='ctgov')
                
                # Split based on extraction logic
                if isinstance(ext_criteria, list) and len(ext_criteria) > 0 and isinstance(ext_criteria[0], list):
                    inclusion = ext_criteria[0]
                    exclusion = ext_criteria[1]
                else:
                    inclusion = ext_criteria
                    exclusion = []

                # Clean and Embed (Using engine methods)
                clean_in = engine.CleanCriteria(inclusion)
                clean_ex = engine.CleanCriteria(exclusion)
                
                if clean_in.empty and clean_ex.empty:
                    match_score = 0.0
                else:
                    embedded_in = engine.EmbedCriteria(CleanedCriteria=clean_in['Final']) if not clean_in.empty else pd.DataFrame()
                    embedded_ex = engine.EmbedCriteria(CleanedCriteria=clean_ex['Final']) if not clean_ex.empty else pd.DataFrame()
                    
                    classified_in = engine.ClassifyCriteria(criteria=clean_in['Original'], embeddings=embedded_in['Embedding'], model_folder_path=SVM_MODELS_DIR) if not embedded_in.empty else pd.DataFrame()
                    classified_ex = engine.ClassifyCriteria(criteria=clean_ex['Original'], embeddings=embedded_ex['Embedding'], model_folder_path=SVM_MODELS_DIR) if not embedded_ex.empty else pd.DataFrame()
                    
                    classified_df = pd.concat([classified_in, classified_ex])
                    match_score = engine.ComputeMatchScore(patient_data.filters, inclusion + exclusion, trial_info, classified_df)
                
                # Format for frontend
                results.append({
                    "trial_id": row["nct_id"],
                    "trial_name": row["nct_id"],
                    "match_score": match_score,
                    "criteria_summary": str(row["./eligibility/criteria/textblock"])[:200] + "...",
                    "trial_link": f"https://clinicaltrials.gov/ct2/show/{row['nct_id']}"
                })
            except Exception as inner_e:
                logger.warning(f"Error matching trial {row['nct_id']}: {inner_e}")
                continue

        # Sort by match score
        formatted_results = sorted(results, key=lambda x: x["match_score"], reverse=True)[:50]
        return {"results": formatted_results}
    except Exception as e:
        import traceback
        logger.error(f"Error during matching: {e}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))

# Serve Frontend
if os.path.exists(STATIC_DIR):
    # Specifically handle root to serve index.html
    @app.get("/")
    async def read_index():
        return FileResponse(os.path.join(STATIC_DIR, "index.html"))
    
    # Mount everything else (assets, etc.)
    app.mount("/", StaticFiles(directory=STATIC_DIR, html=True), name="static")

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
