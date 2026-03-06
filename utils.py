severity_order = ["Minor","Moderate","High Risk","Critical"]

def adjust_patient_risk(ai_severity,patient):

    try:
        idx = severity_order.index(ai_severity)
    except:
        idx = 0

    reasons = []

    if patient["age"] >= 65:
        idx = min(idx+1,3)
        reasons.append("Age above 65")

    if patient["is_pregnant"]:
        idx = max(idx,2)
        reasons.append("Pregnancy risk")

    if patient["diabetes"] and ai_severity == "Moderate":
        idx = 2
        reasons.append("Diabetes metabolic instability")

    if patient["heart"] and ai_severity == "High Risk":
        idx = 3
        reasons.append("Heart condition")

    if patient["renal"] != "Normal":
        idx = min(idx+1,3)
        reasons.append("Kidney impairment")

    if patient["liver"] != "Healthy":
        idx = min(idx+1,3)
        reasons.append("Liver dysfunction")

    return severity_order[idx],reasons