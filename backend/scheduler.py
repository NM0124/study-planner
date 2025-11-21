# backend/scheduler.py
from datetime import datetime, timedelta
import random, os, joblib
from typing import List, Dict, Any, Optional

MODEL_PATH = os.path.join(os.path.dirname(__file__), "ml_model.joblib")

def _to_date(dstr: Optional[str]):
    if not dstr: return None
    try:
        return datetime.fromisoformat(dstr).date()
    except Exception:
        try:
            return datetime.strptime(dstr, "%Y-%m-%d").date()
        except Exception:
            return None

def _round2(x: float) -> float:
    return round(x + 1e-9, 2)

def _load_model():
    if os.path.exists(MODEL_PATH):
        try:
            payload = joblib.load(MODEL_PATH)
            model = payload.get("model")
            columns = payload.get("columns", [])
            return model, columns
        except Exception:
            return None, None
    return None, None

def _featurize_for_model(subject: Dict[str, Any], days_to_deadline: int, task_types_columns: List[str]):
    """
    Build a feature vector dict for the ML model matching saved columns.
    """
    base = {
        "difficulty": subject.get("difficulty", 3),
        "importance": subject.get("importance", 3),
        "syllabus_size": subject.get("syllabus_size", 1.0),
        "days_to_deadline": days_to_deadline
    }
    # one-hot for task types
    for col in task_types_columns:
        base[col] = 1 if subject.get("task_type", "") == col.replace("task_", "") else 0
    return base

def create_timetable(
    subjects: List[Dict[str, Any]],
    daily_hours: float,
    schedule_type: str = "daily",
    unavailable_dates: Optional[List[str]] = None,
    variant: Optional[int] = None,
    limit_weekends: bool = False
) -> Dict[str, List[Dict[str, Any]]]:

    if unavailable_dates is None:
        unavailable_dates = []

    # variant seed
    if variant is None:
        variant = int(datetime.now().timestamp() * 1000)
    random.seed(int(variant))

    # load model if present
    model, model_columns = _load_model()
    # if model exists we need to know which task_* columns are expected
    task_columns = [c for c in (model_columns or []) if c.startswith("task_")] if model_columns else []

    # normalize subjects into units and remaining_units
    norm = []
    for s in subjects:
        name = str(s.get("name","")).strip()
        if not name:
            continue
        deadline = _to_date(s.get("deadline"))
        # syllabus_size is units (units: B). round to int >=1
        units = int(round(float(s.get("syllabus_size") or 1)))
        units = max(1, units)
        difficulty = int(s.get("difficulty") or 3)
        importance = int(s.get("importance") or 3)
        weight = units * max(1.0, float(importance))
        norm.append({
            "name": name,
            "deadline": deadline,
            "units_total": units,
            "units_left": float(units),  # use float to allow fractional consumption
            "difficulty": difficulty,
            "importance": importance,
            "task_type": s.get("task_type"),
            "weight": weight
        })

    if not norm:
        # still produce an empty timetable for the date range (optional), but return empty dict here
        return {}

    # unavailable set (date objects)
    unavailable_set = set(d for d in (_to_date(x) for x in unavailable_dates) if d is not None)

    today = datetime.now().date()
    deadlines = [s["deadline"] for s in norm if s["deadline"]]
    if deadlines:
        last_deadline = max(max(deadlines), today + timedelta(days=7))
    else:
        last_deadline = today + timedelta(days=30)

    timetable: Dict[str, List[Dict[str, Any]]] = {}
    current = today
    last_subject = None
    EPS = 1e-6

    # iterate every single day in the range (do NOT break early)
    while current <= last_deadline:
        iso = current.isoformat()

        # --- 1) If this date is unavailable, keep an empty list and skip scheduling ---
        if current in unavailable_set:
            timetable[iso] = []
            current += timedelta(days=1)
            continue

        # --- 2) Optionally skip weekends entirely (but keep the day empty) ---
        if limit_weekends and current.weekday() >= 5:
            # keep the day present but empty
            timetable[iso] = []
            current += timedelta(days=1)
            continue

        # --- 3) Build active list: subjects that still have units_left > EPS ---
        active = [s for s in norm if s["units_left"] > EPS]

        # We will keep iterating through the date range even if active is empty.
        # If no active subjects, record an empty day and continue.
        if not active:
            timetable[iso] = []
            current += timedelta(days=1)
            continue

        # Prepare this day's list
        timetable[iso] = []

        # compute days_to_deadline and predicted unit-hours for each active subject
        scored = []
        for s in active:
            days_to_deadline = (s["deadline"] - current).days if s["deadline"] else 30

            # ML prediction path
            predicted_unit_hours = None
            if model is not None:
                try:
                    feat = _featurize_for_model(s, days_to_deadline, task_columns)
                    x = [feat.get(col, 0.0) for col in model_columns]
                    predicted_unit_hours = float(model.predict([x])[0])
                    predicted_unit_hours = max(0.25, min(predicted_unit_hours, 4.0))
                except Exception:
                    predicted_unit_hours = None

            # fallback heuristic (U5)
            if predicted_unit_hours is None:
                base = 0.9 + (s["difficulty"] * 0.2) + (s["importance"] * 0.15)
                if s["deadline"]:
                    days_left = (s["deadline"] - current).days
                    if days_left <= 0:
                        urgency = 1.5
                    else:
                        urgency = 1.0 + max(0.0, (30 - min(30, days_left))) / 40.0
                else:
                    urgency = 1.0
                predicted_unit_hours = base * urgency * random.uniform(0.9, 1.15)
                predicted_unit_hours = max(0.25, min(predicted_unit_hours, 4.0))

            scored.append((s, predicted_unit_hours))

        # --- 4) Scheduling logic -- DAILY mode ---
        if schedule_type == "daily":
            # compute a simple priority for ordering
            scored_priority = []
            for s, unit_h in scored:
                days_to_deadline = (s["deadline"] - current).days if s["deadline"] else 30
                urgency = 1.0 + max(0.0, (30 - min(30, days_to_deadline))) / 30.0
                priority = s["weight"] * urgency * random.uniform(0.9, 1.1)
                scored_priority.append((s, unit_h, priority))

            # sort by priority descending (highest priority first)
            scored_priority.sort(key=lambda x: x[2], reverse=True)

            remaining_daily = float(daily_hours)

            # schedule through priority list, allocate fractional units if needed
            for s, unit_h, _ in scored_priority:
                if remaining_daily <= 0:
                    break
                if s["units_left"] <= EPS:
                    continue

                # If last_subject equals s, reduce allocation slightly to avoid back-to-back heavy repeat
                repeat_penalty = 1.0
                if s["name"] == last_subject:
                    repeat_penalty = random.uniform(0.4, 0.8)

                effective_unit_h = unit_h * repeat_penalty

                # Decide how many units (or fractions) we can allocate from this subject today.
                # We allocate at most one full unit at a time to encourage spreading, but allow partial unit consumption.
                # assign = min(effective_unit_h, remaining_daily)
                assign = min(effective_unit_h, remaining_daily)
                # do not assign extremely tiny amounts
                if assign < 0.25:
                    continue

                # record assignment
                assign_rounded = _round2(assign)
                timetable[iso].append({"subject": s["name"], "hours": assign_rounded})
                remaining_daily -= assign

                # decrement units_left proportionally
                fraction_consumed = assign / unit_h if unit_h > EPS else 1.0
                s["units_left"] = max(0.0, s["units_left"] - fraction_consumed)

                # update last_subject to the last assigned subject this loop (helps alternate logic)
                last_subject = s["name"]

        # --- 5) Scheduling logic -- ALTERNATE mode ---
        else:
            # Pick from top scored subjects but randomize a bit and avoid last_subject
            scored_sorted = sorted(scored, key=lambda x: x[1], reverse=True)
            pool = [pair for pair in scored_sorted[:4]]  # top4 pool
            random.shuffle(pool)
            picks = []
            for s, unit_h in pool:
                if s["units_left"] <= EPS:
                    continue
                if s["name"] == last_subject:
                    continue
                picks.append((s, unit_h))
                if len(picks) >= 2:
                    break
            if not picks and scored_sorted:
                picks = [scored_sorted[0]]

            if picks:
                per = float(daily_hours) / len(picks)
                for s, unit_h in picks:
                    assign = min(per, unit_h)
                    if assign < 0.25:
                        continue
                    timetable[iso].append({"subject": s["name"], "hours": _round2(assign)})
                    fraction_consumed = assign / unit_h if unit_h > EPS else 1.0
                    s["units_left"] = max(0.0, s["units_left"] - fraction_consumed)
                last_subject = picks[-1][0]["name"]

        # --- 6) Clean up today's entries: merge duplicates and round ---
        merged: Dict[str, float] = {}
        for slot in timetable[iso]:
            merged[slot["subject"]] = merged.get(slot["subject"], 0.0) + float(slot["hours"])
        day_list = []
        for name, hrs in merged.items():
            hrs = _round2(hrs)
            if hrs <= 0.0:
                continue
            day_list.append({"subject": name, "hours": hrs})
        # Overwrite with merged list (may be empty)
        timetable[iso] = day_list

        # advance date
        current += timedelta(days=1)

    # final: return timetable including empty days (unavailable/ weekends / after completion)
    return timetable
