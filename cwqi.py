# =========================
# Centralized Water Quality Index (CWQI)
# =========================

def is_valid(x):
    return x is not None


# -------- Sub-score functions --------

def turbidity_score(T):
    if not is_valid(T):
        return None
    if T <= 1:
        return 100
    elif T <= 5:
        return max(0, 100 - 20 * (T - 1))
    else:
        return 0


def ph_score(ph):
    if not is_valid(ph):
        return None
    if 6.5 <= ph <= 8.5:
        return 100
    deviation = abs(ph - 7.0)
    return max(0, 100 - deviation * 50)


def fluoride_score(F):
    if not is_valid(F):
        return None
    if F <= 1.0:
        return 100
    elif F <= 1.5:
        return max(0, 100 - (F - 1.0) * 100)
    else:
        return 0


def coliform_score(C):
    if not is_valid(C):
        return None
    if C == 0:
        return 100
    elif C <= 10:
        return 50
    else:
        return 0


def conductivity_score(EC):
    if not is_valid(EC):
        return None
    if EC <= 500:
        return 100
    elif EC <= 1500:
        return max(0, 100 - (EC - 500) / 10)
    else:
        return 0


def temperature_score(T):
    if not is_valid(T):
        return None
    if 20 <= T <= 30:
        return 100
    elif T <= 35:
        return max(0, 100 - (T - 30) * 10)
    else:
        return 0


def do_score(DO):
    if not is_valid(DO):
        return None
    if DO >= 6:
        return 100
    elif DO >= 4:
        return (DO - 4) / 2 * 100
    else:
        return 0


def pressure_score(P):
    if not is_valid(P):
        return None
    if 2 <= P <= 5:
        return 100
    elif 1 <= P < 2 or 5 < P <= 6:
        return 50
    else:
        return 0


# -------- Weights --------

WEIGHTS = {
    "coliform": 0.25,
    "turbidity": 0.15,
    "ph": 0.15,
    "fluoride": 0.10,
    "conductivity": 0.10,
    "do": 0.10,
    "pressure": 0.10,
    "temperature": 0.05
}


# -------- CWQI Core --------

def compute_cwqi(reading: dict):
    """
    reading keys expected:
    turbidity, ph, fluoride, coliform,
    conductivity, temperature, dissolved_oxygen, pressure
    """

    scores = {
        "turbidity": turbidity_score(reading.get("turbidity")),
        "ph": ph_score(reading.get("ph")),
        "fluoride": fluoride_score(reading.get("fluoride")),
        "coliform": coliform_score(reading.get("coliform")),
        "conductivity": conductivity_score(reading.get("conductivity")),
        "temperature": temperature_score(reading.get("temperature")),
        "do": do_score(reading.get("dissolved_oxygen")),
        "pressure": pressure_score(reading.get("pressure")),
    }

    total = 0.0
    weight_sum = 0.0
    reasons = []

    for param, score in scores.items():
        if score is not None:
            total += score * WEIGHTS[param]
            weight_sum += WEIGHTS[param]
            if score < 50:
                reasons.append(f"{param} degraded")

    cwqi = total / weight_sum if weight_sum > 0 else 0

    # Hard safety override
    if scores["coliform"] == 0:
        return 0.0, "RED", "Critical coliform contamination"

    if cwqi >= 80:
        status = "GREEN"
    elif cwqi >= 50:
        status = "AMBER"
    else:
        status = "RED"

    reason = ", ".join(reasons) if reasons else "All parameters normal"

    return round(cwqi, 2), status, reason


# -------- Local test --------

if __name__ == "__main__":
    sample_reading = {
        "turbidity": 3.0,
        "ph": 7.2,
        "fluoride": 0.9,
        "coliform": 0,
        "conductivity": 800,
        "temperature": 31,
        "dissolved_oxygen": 5.0,
        "pressure": 1.5
    }

    cwqi, status, reason = compute_cwqi(sample_reading)
    print("CWQI:", cwqi)
    print("Status:", status)
    print("Reason:", reason)
