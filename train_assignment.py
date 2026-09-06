"""Create fictional history on request, then train/evaluate the classroom model.

Run with --generate-demo once to create data; normal runs preserve CSV edits.
The GUI fits the same small model at startup, before opening its event loop.
"""

import argparse
import csv
import json
import random
from datetime import date, timedelta
from pathlib import Path
from duration_model import DATA_PATH, load_duration_model
from registration import WARD_CODES


def generate_demo(path):
    # Exclusive file creation protects edits: generating again does not overwrite
    # an existing CSV. These base values and noise are INVENTED teaching data.
    # They demonstrate learning, not evidence that any doctor is better/faster.
    path.parent.mkdir(exist_ok=True)
    rng = random.Random(42)
    pair_minutes = {
        '01': [34, 28, 25, 18],
        '02': [27, 19, 35, 29],
        '03': [38, 43, 24, 32],
        '04': [16, 25, 29, 34],
    }
    with path.open('x', encoding='utf-8', newline='') as target:
        fields = ['appointment_id', 'date', 'ward', 'room_id', 'doctor_id', 'duration_minutes', 'source']
        writer = csv.DictWriter(target, fieldnames=fields)
        writer.writeheader()
        sequence = 0
        for day in range(25):
            for ward, code in WARD_CODES.items():
                for room in (1, 2):
                    for doctor in (1, 2):
                        sequence += 1
                        base = pair_minutes[code][(room - 1)*2 + doctor - 1]
                        writer.writerow({
                            'appointment_id': f'SIM-{sequence:04d}',
                            'date': (date(2026, 8, 1) + timedelta(days=day)).isoformat(),
                            'ward': ward, 'room_id': f'R{code}-{room}', 'doctor_id': f'D{code}-{doctor}',
                            'duration_minutes': round(max(5, base + rng.gauss(0, 2)), 2),
                            'source': 'simulated',
                        })


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--generate-demo', action='store_true')
    args = parser.parse_args()
    if args.generate_demo:
        generate_demo(DATA_PATH)
    model = load_duration_model()
    report = model['report']
    output = Path(__file__).resolve().parent / 'artifacts'
    output.mkdir(exist_ok=True)
    (output / 'assignment_evaluation.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(json.dumps(report, indent=2))
