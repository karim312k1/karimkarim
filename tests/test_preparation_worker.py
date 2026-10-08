"""Preparation must discard warmup evidence and require fresh successful analysis."""
import os
import time
import unittest
from unittest.mock import Mock
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
from PySide6.QtWidgets import QApplication
from config import AppConfig
from core.preparation import PreparationStatus
from events import ProctorEvent
from ui.camera_worker import CameraWorker


class PreparationWorkerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def run_case(self, *, stale=False, error=False, cancel=False):
        detectors = Mock()
        detectors.load.return_value = []
        detectors.prepare.return_value = PreparationStatus(True, 1, 'ready')
        pipeline = Mock()
        worker = CameraWorker(AppConfig.from_env(), detectors, pipeline)
        worker._frame_number = 1
        worker._captured_at = time.monotonic() - (10 if stale else 0)
        worker._latest_frame = object()
        emitted = []
        def observe(status):
            emitted.append(status)
            worker.stop()
        worker.preparation_status.connect(observe)
        def analyze(frame):
            if cancel:
                worker.stop()
            return [ProctorEvent.create('gaze_down', source='test')], ['bad frame'] if error else []
        detectors.analyze.side_effect = analyze
        worker._run_analysis()
        pipeline.submit.assert_not_called()
        detectors.close.assert_called_once()
        return detectors, pipeline, emitted

    def test_preparation_movements_are_not_violations(self):
        detectors, pipeline, emitted = self.run_case()
        self.assertTrue(emitted[0].ready)
        pipeline.offer_reference_frame.assert_called_once()

    def test_stale_warmup_frame_cannot_unlock_test(self):
        detectors, pipeline, emitted = self.run_case(stale=True)
        detectors.prepare.assert_not_called()
        self.assertFalse(emitted[0].ready)

    def test_errors_cannot_unlock_test(self):
        detectors, pipeline, emitted = self.run_case(error=True)
        detectors.prepare.assert_not_called()
        self.assertTrue(emitted[0].error)

    def test_late_result_after_cancel_cannot_unlock_test(self):
        detectors, pipeline, emitted = self.run_case(cancel=True)
        self.assertEqual(emitted, [])
        detectors.prepare.assert_not_called()
