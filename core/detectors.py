"""Adapters that isolate teammate detector modules from the main loop."""

from __future__ import annotations

import importlib
import time
from dataclasses import dataclass
from types import ModuleType
from typing import Any, Callable

from events import ProctorEvent, normalize_events
from .preparation import FacePreparation, PreparationStatus


@dataclass(frozen=True, slots=True)
class ModuleStatus:
    name: str
    loaded: bool
    message: str


class DetectorAdapter:
    def __init__(
        self,
        name: str,
        module_name: str,
        function_name: str,
        reset_function_name: str,
    ) -> None:
        self.name = name
        self.module_name = module_name
        self.function_name = function_name
        self.reset_function_name = reset_function_name
        self._module: ModuleType | None = None
        self._function: Callable[[Any], Any] | None = None
        self.last_duration_ms = 0.0

    def load(self) -> ModuleStatus:
        try:
            self._module = importlib.import_module(self.module_name)
            function = getattr(self._module, self.function_name)
            if not callable(function):
                raise TypeError(f"{self.function_name} is not callable")
            self._function = function
        except Exception as exc:
            self._module = None
            self._function = None
            return ModuleStatus(self.name, False, f"{type(exc).__name__}: {exc}")
        return ModuleStatus(
            self.name,
            True,
            f"{self.module_name}.{self.function_name}",
        )

    @property
    def loaded(self) -> bool:
        return self._function is not None

    def analyze(self, frame: Any) -> list[ProctorEvent]:
        if self._function is None:
            return []
        started = time.perf_counter()
        try:
            raw_events = self._function(frame)
        finally:
            self.last_duration_ms = (time.perf_counter() - started) * 1000.0
        return normalize_events(raw_events, default_source=self.name)

    def close(self) -> None:
        if self._module is None:
            return
        reset = getattr(self._module, self.reset_function_name, None)
        if callable(reset):
            reset()


class DetectorCollection:
    def __init__(self, phone_module: str, gaze_module: str) -> None:
        self.adapters = (
            DetectorAdapter(
                "phone",
                phone_module,
                "detect",
                "reset_default_detector",
            ),
            DetectorAdapter(
                "gaze",
                gaze_module,
                "analyze",
                "reset_default_analyzer",
            ),
        )
        self.last_timings_ms: dict[str, float] = {}
        self.preparation = FacePreparation()

    def load(self) -> list[ModuleStatus]:
        return [adapter.load() for adapter in self.adapters]

    def analyze(self, frame: Any) -> tuple[list[ProctorEvent], list[str]]:
        events: list[ProctorEvent] = []
        errors: list[str] = []
        for adapter in self.adapters:
            if not adapter.loaded:
                continue
            try:
                events.extend(adapter.analyze(frame))
                self.last_timings_ms[adapter.name] = adapter.last_duration_ms
            except Exception as exc:
                errors.append(f"{adapter.name}: {type(exc).__name__}: {exc}")
        return events, errors

    def prepare(self, now: float) -> PreparationStatus:
        module = self.adapters[1]._module
        getter = getattr(module, 'get_diagnostics', None)
        calibrate = getattr(module, 'calibrate_default_analyzer', None)
        if not callable(getter) or not callable(calibrate):
            return PreparationStatus(False, 0, 'Модуль взгляда не поддерживает настройку лица', True)
        status = self.preparation.update(getter() or {}, now)
        if status.ready:
            samples = [module.FaceMetrics(
                module.HeadPose(**raw['head_pose']), raw['iris_x'], raw['iris_y'],
                eye_open=raw['eye_open']
            ) for _, raw in self.preparation.samples]
            calibrate(samples, target='screen')
            reset_phone = getattr(self.adapters[0]._module, 'reset_default_timers', None)
            if callable(reset_phone):
                reset_phone()
        return status

    def close(self) -> None:
        for adapter in self.adapters:
            try:
                adapter.close()
            except Exception:
                # A failed cleanup in one detector must not prevent the other
                # model and the camera from being released.
                pass

