from itertools import combinations


def generate_pairs(drugs):

    pairs = list(combinations(drugs, 2))

    return pairs


def adjust_for_patient(severity, age):

    if age > 65:

        if severity == "Moderate":
            return "Severe"

        if severity == "Mild":
            return "Moderate"

    return severity