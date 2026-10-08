"""Require a short, stable face sample before admitting the student to a test."""
from dataclasses import dataclass
import math
from typing import Any


@dataclass(frozen=True)
class PreparationStatus:
    ready: bool
    progress: float
    message: str
    error: bool = False


class FacePreparation:
    seconds = 3.0
    min_samples = 10
    max_gap = .8

    def __init__(self):
        self.samples: list[tuple[float, dict[str, Any]]] = []

    def reset(self):
        self.samples.clear()

    def update(self, diagnostics: dict[str, Any], now: float) -> PreparationStatus:
        if diagnostics.get('face_count') != 1:
            self.reset()
            return PreparationStatus(False, 0, 'В кадре должно быть одно лицо')
        raw = diagnostics.get('raw_metrics') or {}
        pose = raw.get('head_pose') or {}
        values = [pose.get(k) for k in ('pitch', 'yaw', 'roll')]
        values += [raw.get(k) for k in ('iris_x', 'iris_y', 'eye_open')]
        valid = all(isinstance(v, (int, float)) and math.isfinite(v) for v in values)
        if not valid or raw['eye_open'] < .12:
            # A brief blink does not invalidate an otherwise stable sample.
            if not self.samples or now - self.samples[-1][0] > .35:
                self.reset()
            return PreparationStatus(False, 0, 'Смотрите в центр экрана, держите глаза открытыми')
        if abs(pose['yaw']) > 25 or abs(pose['pitch']) > 30:
            self.reset()
            return PreparationStatus(False, 0, 'Повернитесь к экрану и держите голову прямо')
        if self.samples and (now - self.samples[-1][0] > self.max_gap
                             or now <= self.samples[-1][0]):
            self.reset()
        candidates = [sample for _, sample in self.samples] + [raw]
        stable = all(
            max(s['head_pose'][axis] for s in candidates)
            - min(s['head_pose'][axis] for s in candidates) <= 6
            for axis in ('pitch', 'yaw', 'roll')
        ) and all(max(s[axis] for s in candidates) - min(s[axis] for s in candidates) <= .12
                  for axis in ('iris_x', 'iris_y'))
        if not stable:
            self.reset()
        self.samples.append((now, raw))
        elapsed = now - self.samples[0][0]
        progress = min(1.0, elapsed / self.seconds, len(self.samples) / self.min_samples)
        ready = progress >= 1
        return PreparationStatus(ready, progress, 'Лицо настроено' if ready else
                                 'Смотрите в центр экрана и сохраняйте положение')
