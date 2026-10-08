import unittest
from unittest.mock import patch
import numpy as np
from gaze.analyzer import AnalyzerConfig, GazeAnalyzer, FaceMetrics, HeadPose
from gaze.tests.test_gaze_analyzer import FakeFaceMesh
from events import normalize_events
from config import RISK_WEIGHTS
from core.event_presentation import EVENT_LABELS


class GazeThreeSecondsTests(unittest.TestCase):
    def test_each_direction_emits_at_three_seconds_not_earlier(self):
        for name, pitch, yaw in [('gaze_down', 40, 0), ('gaze_up', -30, 0),
                                 ('gaze_side', 0, 35), ('gaze_side', 0, -35)]:
            with self.subTest(direction=name, yaw=yaw):
                analyzer = GazeAnalyzer(AnalyzerConfig(smoothing_window=1),
                                        face_mesh=FakeFaceMesh())
                frame = np.zeros((32, 32, 3), dtype=np.uint8)
                metric = FaceMetrics(HeadPose(pitch, yaw, 0), .5, .5)
                try:
                    with patch('gaze.analyzer.measure_face', return_value=metric):
                        for now in np.arange(0, 3, .25):
                            self.assertEqual(analyzer.analyze(frame, timestamp=float(now)), [])
                        events = analyzer.analyze(frame, timestamp=3)
                        self.assertEqual([e['type'] for e in events], [name])
                        self.assertEqual(events[0]['duration'], 3)
                        self.assertEqual(analyzer.analyze(frame, timestamp=3.25), [])
                        self.assertEqual(normalize_events(events, default_source='gaze')[0].type.value, name)
                finally:
                    analyzer.close()

    def test_up_is_named_and_scored_for_teacher(self):
        self.assertIn('gaze_up', EVENT_LABELS)
        self.assertEqual(RISK_WEIGHTS.get('gaze_up'), RISK_WEIGHTS['gaze_side'])

    def test_up_survives_storage_and_html_export(self):
        import tempfile
        from pathlib import Path
        from core.storage import EventStore
        from teacher.data import load_sessions
        from teacher.report import render_session_report
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            store = EventStore(root/'events.db', root/'shots')
            store.start_session('up', {})
            event = normalize_events({'type': 'gaze_up', 'duration': 3}, default_source='gaze')[0]
            store.record_event(event, session_id='up', weight=10, risk_total=10)
            store.finish_session('up', final_risk=10)
            store.close()
            session = load_sessions(root/'events.db')[0]
            self.assertEqual(session.events[0].event.type.value, 'gaze_up')
            html = render_session_report(session, None, root/'events.db')
            self.assertIn('Долгий взгляд вверх', html)
