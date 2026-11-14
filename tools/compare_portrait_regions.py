"""Compare captured character regions, allowing 8-bit compositor rounding only."""
import json
from pathlib import Path
import cv2
import numpy as np

folder = Path(__file__).resolve().parents[1] / 'output/cover-portrait'
report = {}
for region in ['eyes', 'body', 'hair']:
    left = cv2.imread(str(folder / f'{region}-left.png')).astype(np.int16)
    right = cv2.imread(str(folder / f'{region}-right.png')).astype(np.int16)
    assert left.shape == right.shape
    delta = np.max(np.abs(left - right), axis=2)
    report[region] = {'maximum_channel_difference': int(delta.max()), 'pixels_above_rounding_tolerance': int(np.sum(delta > 3))}
    if region == 'eyes':
        assert np.sum(delta > 20) > 30, 'Eyes must visibly respond to pointer changes'
    elif region == 'hair':
        # The user now requests subtle hair motion; the roots sampled here are
        # permitted to vary slightly, while the body remains locked.
        assert np.mean(delta) < 12, 'Hair motion is too strong'
    else:
        assert delta.max() <= 3, f'{region}: unexpected character movement'
(folder / 'region-comparison.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
print(json.dumps(report))
