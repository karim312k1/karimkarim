import unittest
from core.preparation import FacePreparation


def observation(yaw=0, faces=1, iris=.5):
    return dict(face_count=faces, raw_metrics=dict(
        head_pose=dict(pitch=0, yaw=yaw, roll=0), iris_x=iris,
        iris_y=.5, eye_open=.22))


class FacePreparationTests(unittest.TestCase):
    def test_requires_three_seconds_of_stable_samples(self):
        gate = FacePreparation()
        for i in range(15):
            self.assertFalse(gate.update(observation(), i*.2).ready)
        self.assertTrue(gate.update(observation(), 3).ready)
        self.assertGreaterEqual(len(gate.samples), 10)

    def test_movement_and_missing_face_reset_progress(self):
        for invalid in (observation(yaw=35), observation(faces=0), observation(faces=2)):
            with self.subTest(invalid=invalid):
                gate = FacePreparation()
                for i in range(15):
                    gate.update(observation(), i*.2)
                self.assertEqual(gate.update(invalid, 3).progress, 0)
                self.assertFalse(gate.update(observation(), 3.2).ready)

    def test_long_sample_gap_does_not_count_as_stability(self):
        gate = FacePreparation()
        gate.update(observation(), 0)
        result = gate.update(observation(), 30)
        self.assertFalse(result.ready)
        self.assertEqual(result.progress, 0)

    def test_continuous_drift_cannot_calibrate(self):
        gate = FacePreparation()
        for i in range(30):
            self.assertFalse(gate.update(observation(yaw=i*.6), i*.2).ready)

    def test_invalid_measurement_cannot_calibrate(self):
        gate = FacePreparation()
        invalid = observation()
        invalid['raw_metrics']['iris_x'] = None
        for i in range(30):
            self.assertFalse(gate.update(invalid, i*.2).ready)
