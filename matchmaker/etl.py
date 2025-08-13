import requests, pandas as pd, time
V2 = "https://clinicaltrials.gov/api/v2/studies"

def _flatten(study):
    p = (study or {}).get("protocolSection", {})
    idm = p.get("identificationModule", {})
    cond = p.get("conditionsModule", {})
    elig = p.get("eligibilityModule", {})
    stat = p.get("statusModule", {})
    des  = p.get("designModule", {})
    cloc = p.get("contactsLocationsModule", {})
    countries = sorted({(loc.get("country") or "") for loc in (cloc.get("locations") or [])} - {""})
    phases = des.get("phases") if isinstance(des.get("phases"), list) else [des.get("phases")] if des.get("phases") else []
    return {
        "NCTId": idm.get("nctId"),
        "BriefTitle": idm.get("briefTitle") or idm.get("officialTitle"),
        "Condition": "; ".join(cond.get("conditions", []) or []),
        "EligibilityCriteria": (elig.get("eligibilityCriteria") or "").strip(),
        "StudyType": des.get("studyType"),
        "Phase": phases[0] if phases else None,
        "EnrollmentCount": (stat.get("enrollmentInfo") or {}).get("count"),
        "LocationCountry": "; ".join(countries),
        "StartDate": (stat.get("startDateStruct") or {}).get("date"),
        "PrimaryCompletionDate": (stat.get("primaryCompletionDateStruct") or {}).get("date"),
        "OverallStatus": stat.get("overallStatus"),
    }

def fetch_trials_v2(cond_query='("type 2 diabetes" OR diabetes OR "heart failure" OR cancer)',
                    statuses=("RECRUITING",), page_size=200, max_pages=3):
    params = {
        "query.cond": cond_query,
        "filter.overallStatus": ",".join(statuses),
        "pageSize": page_size,
        "format": "json",
        "countTotal": "true",
    }
    studies, token = [], None
    for _ in range(max_pages):
        if token: params["pageToken"] = token
        for attempt in range(3):
            try:
                r = requests.get(V2, params=params, timeout=60)
                r.raise_for_status()
                break
            except requests.RequestException:
                if attempt == 2: raise
                time.sleep(1.5 * (attempt + 1))
        data = r.json()
        studies.extend(data.get("studies", []))
        token = data.get("nextPageToken")
        if not token: break
    rows = [_flatten(s) for s in studies]
    df = pd.DataFrame(rows).dropna(subset=["NCTId"]).drop_duplicates(subset=["NCTId"]).reset_index(drop=True)
    df["EligibilityCriteria"] = df["EligibilityCriteria"].fillna("")
    df["Condition"] = df["Condition"].fillna("")
    return df