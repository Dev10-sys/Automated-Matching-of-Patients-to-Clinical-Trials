import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import pandas as pd
import logging
from matching_engine_wrapper import gearboxNLP

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="GEARBOx Clinical Trial Matching API")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Constants
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODELS_DIR = os.path.join(BASE_DIR, "trained_ML_models")
FT_MODEL_PATH = os.path.join(MODELS_DIR, "fasttext", "ft_embedding_size256_window5.model")
SVM_MODELS_DIR = os.path.join(MODELS_DIR, "SVMs", "classifier_models")
PROJECT_DATA_DIR = os.path.join(BASE_DIR, "project_data")
TRIAL_METADATA_PATH = os.path.join(PROJECT_DATA_DIR, "trial_metadata.csv")

# Initialize matching engine
engine = None

@app.on_event("startup")
async def startup_event():
    global engine
    try:
        logger.info("Initializing matching engine...")
        engine = gearboxNLP(FT_MODEL_PATH, SVM_MODELS_DIR)
        logger.info("Matching engine initialized successfully.")
    except Exception as e:
        logger.error(f"Failed to initialize matching engine: {e}")

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
    if engine is None:
        raise HTTPException(status_code=503, detail="Matching engine is not initialized.")
    
    try:
        # Load NCT IDs from metadata
        df_trials = pd.read_csv(TRIAL_METADATA_PATH)
        # For performance, only match the top few for now (can be adjusted)
        nct_ids = df_trials['nct_id'].tolist()[:20]  # Just 20 for matching demo speed

        patient_dict = patient_data.filters
        # Provide some dummy values if fields are missing (though UI should handle this)
        # Actually, let's keep it robust
        results_df = engine.Match(patient_dict, docx_trials=[], ctgov_trials=nct_ids)
        
        # Merge with metadata for richer results
        results_full = pd.merge(results_df, df_trials, left_on='Trial ID', right_on='nct_id')
        
        # Format results for the frontend
        formatted_results = []
        for _, row in results_full.iterrows():
            formatted_results.append({
                "trial_id": row["Trial ID"],
                "trial_name": row["nct_id"], # or use a name column if available
                "match_score": row["Match Score"],
                "criteria_summary": row["./eligibility/criteria/textblock"][:200] + "...",
                "trial_link": f"https://clinicaltrials.gov/ct2/show/{row['Trial ID']}"
            })
            
        return {"results": formatted_results}
    except Exception as e:
        logger.error(f"Error during matching: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
