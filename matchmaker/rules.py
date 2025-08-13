import re
from typing import Dict, List

def extract_age_bounds(eligibility: str):
    m = re.search(r"ages?\s+(\d+)\s+to\s+(\d+)", eligibility, re.I)
    if m: return int(m.group(1)), int(m.group(2))
    m = re.search(r"older than\s+(\d+)", eligibility, re.I)
    if m: return int(m.group(1)), 200
    return None, None

def requires_sex(eligibility: str):
    if re.search(r"\b(male[s]? only)\b", eligibility, re.I): return "male"
    if re.search(r"\b(female[s]? only)\b", eligibility, re.I): return "female"
    return None

def keyword_hits(text: str, terms: List[str]) -> List[str]:
    hits = []
    low = text.lower()
    for t in terms:
        if re.search(rf"\b{re.escape(t.lower())}\b", low):
            hits.append(t)
    return hits

def rule_check(patient, trial_elig: str) -> Dict:
    reasons_in, reasons_out = [], []

    lb, ub = extract_age_bounds(trial_elig)
    if lb is not None and (patient.age < lb or patient.age > ub):
        reasons_out.append(f"Age outside range ({lb}-{ub})")
    elif lb is not None:
        reasons_in.append(f"Age within range ({lb}-{ub})")

    sex_req = requires_sex(trial_elig)
    if sex_req and patient.sex.lower() != sex_req:
        reasons_out.append(f"Sex required: {sex_req}")
    elif sex_req:
        reasons_in.append(f"Sex matches: {sex_req}")

    cond_hits = keyword_hits(trial_elig, [c.lower() for c in patient.conditions])
    if cond_hits: reasons_in.append("Condition match: " + ", ".join(cond_hits))

    med_conflicts = keyword_hits(trial_elig, [m.lower() for m in patient.medications])
    if med_conflicts: reasons_out.append("Medication mentioned: " + ", ".join(med_conflicts) + " (check exclusion)")

    return {"include_reasons": reasons_in, "exclude_reasons": reasons_out}