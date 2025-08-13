from dataclasses import dataclass
from typing import List, Dict
import json, pathlib

@dataclass
class Patient:
    patient_id: str
    age: int
    sex: str
    conditions: List[str]
    medications: List[str]
    labs: Dict[str, float]
    notes: str = ""

def load_patient(patient_id: str):
    p = json.loads(pathlib.Path(f"data/patients/{patient_id}.json").read_text())
    return Patient(**p)