import os
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path
from unittest.mock import patch

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QCoreApplication, QEvent
from config import AppConfig
from ui.main_window import MainWindow
from core.preparation import PreparationStatus


class PreparationUiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_questions_cannot_advance_before_face_preparation(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            config = replace(AppConfig.from_env(), database_path=root/'events.db',
                             screenshots_dir=root/'shots')
            with patch.object(MainWindow, 'start_monitoring', lambda self: None):
                window = MainWindow(config)
                try:
                    self.app.processEvents()
                    self.assertFalse(window.next_button.isEnabled())
                    window.answer_group.button(0).setChecked(True)
                    window._next_question()
                    self.assertEqual(window.question_index, 0)
                finally:
                    window.pipeline.stop()
                    window.shutdown()
                    window.close()
                    window.deleteLater()
                    QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)

    def test_readiness_opens_questions_but_failure_and_cancel_cannot(self):
        for outcome in ('ready', 'camera_error', 'security_error', 'cancel'):
            with self.subTest(outcome=outcome), tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary)
                config = replace(AppConfig.from_env(), database_path=root/'events.db',
                                 screenshots_dir=root/'shots')
                with patch.object(MainWindow, 'start_monitoring', lambda self: None), \
                     patch('ui.main_window.SecurityAdapter') as security:
                    security.return_value.enable.return_value = (outcome != 'security_error', 'test')
                    window = MainWindow(config)
                    try:
                        self.app.processEvents()
                        if outcome == 'camera_error':
                            window._on_camera_status(False, 'Камера недоступна')
                        if outcome == 'cancel':
                            window.shutdown()
                        window._on_preparation_status(PreparationStatus(True, 1, 'ready'))
                        ready = outcome == 'ready'
                        self.assertEqual(window._monitoring_ready, ready)
                        self.assertEqual(window.content_stack.currentIndex(), int(ready))
                        self.assertEqual(window.next_button.isEnabled(), ready)
                        if outcome in ('cancel', 'camera_error'):
                            security.return_value.enable.assert_not_called()
                    finally:
                        window.pipeline.stop()
                        window.shutdown()
                        window.close()
                        window.deleteLater()
                        QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
