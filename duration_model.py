"""A small decision tree learns appointment durations from historical rows.

The included history is SIMULATED. The model uses ward, room, and doctor IDs,
not patient names, phone numbers, or medical notes. It predicts minutes, not
clinical suitability. assignment.py checks eligibility separately.
"""

import csv
import math
from pathlib import Path
from statistics import median
from datetime import date

DATA_PATH = Path(__file__).resolve().parent / 'data' / 'simulated_appointments.csv'


def features(row):
    """Allowlist the three inputs known BEFORE an appointment finishes."""
    # Actual duration is our TARGET (the answer to learn), never an input.
    return {key: row[key] for key in ('ward', 'room_id', 'doctor_id')}


def train_duration_model(rows):
    """Fit an encoder and decision tree; also retain a simple fallback baseline."""
    # Imports stay here so the GUI can explain a missing dependency and run its
    # original fallback when started with a Python outside the virtual environment.
    from sklearn.feature_extraction import DictVectorizer
    from sklearn.pipeline import make_pipeline
    from sklearn.tree import DecisionTreeRegressor

    if len(rows) < 10:
        raise ValueError('At least 10 historical rows are needed for this demo.')
    x = [features(row) for row in rows]
    y = [float(row['duration_minutes']) for row in rows]
    if any(not math.isfinite(value) or value <= 0 for value in y):
        raise ValueError('Historical durations must be finite, positive minutes.')

    # DictVectorizer converts category names into numeric indicator columns.
    # IDs remain categories: D01-2 is not numerically twice as much as D01-1.
    # Pipeline applies the SAME encoding during fitting and prediction.
    # fit learns the tree's splits and leaf values from x/y. These rules are
    # learned, unlike the old hand-written choice of the first available pair.
    pipeline = make_pipeline(
        DictVectorizer(sparse=False),
        DecisionTreeRegressor(max_depth=6, min_samples_leaf=5, random_state=42),
    )
    pipeline.fit(x, y)
    ward_medians = {}
    for row, duration in zip(rows, y):
        ward_medians.setdefault(row['ward'], []).append(duration)
    return {
        'pipeline': pipeline,
        'known_pairs': {(row['ward'], row['room_id'], row['doctor_id']) for row in rows},
        'ward_medians': {ward: median(values) for ward, values in ward_medians.items()},
        'global_median': median(y),
    }


def load_duration_model(path=DATA_PATH):
    """Train on earlier dates and evaluate on later dates, without refitting."""
    with Path(path).open(encoding='utf-8', newline='') as source:
        rows = list(csv.DictReader(source))
    required = {'appointment_id', 'date', 'ward', 'room_id', 'doctor_id', 'duration_minutes', 'source'}
    if not rows or not required.issubset(rows[0]):
        raise ValueError('History is empty or missing required columns.')
    if any(row['source'] != 'simulated' for row in rows):
        raise ValueError('This classroom loader expects explicitly simulated rows.')
    if len({row['appointment_id'] for row in rows}) != len(rows):
        raise ValueError('Historical appointment IDs must be unique.')
    for row in rows:
        date.fromisoformat(row['date'])
        if not math.isfinite(float(row['duration_minutes'])) or float(row['duration_minutes']) <= 0:
            raise ValueError('Historical durations must be finite and positive.')
    dates = sorted({row['date'] for row in rows})
    if len(dates) < 5:
        raise ValueError('At least five distinct dates are needed for a time split.')
    # Split WHOLE dates, not random rows. Repeated pair features are legitimate
    # here: the test asks about later appointments for the same resources.
    cut = dates[int(len(dates) * 0.8)]
    training = [row for row in rows if row['date'] < cut]
    testing = [row for row in rows if row['date'] >= cut]
    model = train_duration_model(training)
    errors, baseline_errors = [], []
    for row in testing:
        predicted, _ = estimate_duration(model, row['ward'], row['room_id'], row['doctor_id'])
        baseline = model['ward_medians'].get(row['ward'], model['global_median'])
        actual = float(row['duration_minutes'])
        errors.append(abs(predicted - actual))
        baseline_errors.append(abs(baseline - actual))
    # Mean absolute error (MAE) is average distance from actual duration, in minutes.
    # These scores measure the simulated pattern only, not hospital effectiveness.
    model['report'] = {
        'source': 'SIMULATED DATA ONLY',
        'training_rows': len(training), 'test_rows': len(testing),
        'first_test_date': cut,
        'tree_mae_minutes': sum(errors) / len(errors),
        'ward_median_mae_minutes': sum(baseline_errors) / len(baseline_errors),
    }
    return model


def estimate_duration(model, ward, room_id, doctor_id):
    """Predict a known resource combination; label baseline estimates explicitly."""
    if (ward, room_id, doctor_id) not in model['known_pairs']:
        # Do not silently pretend an unseen room/doctor pair has been validated.
        return model['ward_medians'].get(ward, model['global_median']), 'Median fallback: unseen pair'
    example = {'ward': ward, 'room_id': room_id, 'doctor_id': doctor_id}
    minutes = float(model['pipeline'].predict([example])[0])
    return minutes, 'Decision tree (simulated)'
