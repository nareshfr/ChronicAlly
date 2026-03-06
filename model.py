def predict_severity(description):

    desc = description.lower()

    if "toxicity" in desc or "fatal" in desc:
        return "Severe"

    elif "increase risk" in desc or "bleeding" in desc:
        return "Moderate"

    elif "decrease" in desc:
        return "Mild"

    else:
        return "Unknown"