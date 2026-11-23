"""
Threat Tracker Module for 5G Assistive Wearable
================================================
Follows each obstacle across consecutive frames using bounding box IoU matching,
calculates closing velocity (m/s), estimates Time-To-Collision (TTC),
and manages per-object alert cooldowns.
"""

import time

def _iou(a, b):
    x1, y1 = max(a[0], b[0]), max(a[1], b[1])
    x2, y2 = min(a[2], b[2]), min(a[3], b[3])
    inter = max(0, x2 - x1) * max(0, y2 - y1)
    ua = (a[2] - a[0]) * (a[3] - a[1]) + (b[2] - b[0]) * (b[3] - b[1]) - inter
    return inter / ua if ua > 0 else 0.0

class ThreatTracker:
    """Follows each obstacle across frames and works out how fast it is getting closer."""
    def __init__(self, keep_s=1.5, drop_s=1.0):
        self.tracks = {}
        self.next_id = 0
        self.keep_s = keep_s
        self.drop_s = drop_s

    def update(self, threats, now=None):
        now = now or time.time()
        for t in threats:
            best, best_iou = None, 0.3
            for tid, tr in self.tracks.items():
                if tr['name'] == t['name']:
                    iou = _iou(tr['bbox'], t['bbox'])
                    if iou > best_iou:
                        best, best_iou = tid, iou
            if best is None:
                best = self.next_id
                self.next_id += 1
                self.tracks[best] = {'name': t['name'], 'hist': [], 'last_alert': 0.0, 'last_alert_dist': 99.0}
            tr = self.tracks[best]
            tr['bbox'], tr['seen'] = t['bbox'], now
            tr['hist'] = [(ts, d) for ts, d in tr['hist'] if now - ts <= self.keep_s] + [(now, t['distance'])]
            tr['hits'] = tr.get('hits', 0) + 1
            t['hits'] = tr['hits']
            t['track_id'] = best
            t['closing_mps'], t['ttc_s'] = self._ttc(tr['hist'])
        self.tracks = {k: v for k, v in self.tracks.items() if now - v.get('seen', 0) <= self.drop_s}
        return threats

    @staticmethod
    def _ttc(hist):
        if len(hist) < 4 or hist[-1][0] - hist[0][0] < 0.5:
            return 0.0, float('inf')
        n = len(hist)
        mt = sum(t for t, _ in hist) / n
        md = sum(d for _, d in hist) / n
        den = sum((t - mt) ** 2 for t, _ in hist)
        speed = -sum((t - mt) * (d - md) for t, d in hist) / den if den > 0 else 0.0   # + means closing
        d_now = hist[-1][1]
        return speed, (d_now / speed if speed > 0.2 else float('inf'))

    def should_alert(self, t, now, cooldown_s=3.0):
        """Speak again for the same object only if it is clearly worse or the cooldown has passed."""
        tr = self.tracks.get(t.get('track_id'))
        if not tr:
            return True
        worse = t['distance'] < tr['last_alert_dist'] * 0.7
        if worse or now - tr['last_alert'] > cooldown_s:
            tr['last_alert'], tr['last_alert_dist'] = now, t['distance']
            return True
        return False
