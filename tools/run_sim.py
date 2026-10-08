"""Portable local student/teacher simulation; never starts on module import."""
from __future__ import annotations

import argparse
from dataclasses import replace
from datetime import datetime
import os
from pathlib import Path
import sys

PROJECT = Path(__file__).resolve().parents[1]
if str(PROJECT) not in sys.path:
    sys.path.insert(0, str(PROJECT))

PROTECTION_SECONDS = 60


def simulation_directory() -> Path:
    return PROJECT / "data" / "simulation"


def run_student() -> int:
    import environment_protection
    from PySide6.QtCore import QTimer
    from PySide6.QtGui import QKeySequence, QShortcut
    from PySide6.QtWidgets import QApplication
    from main import main as run_application

    os.environ["PROCTOR_STUDENT_VIEW"] = "1"
    os.environ["PROCTOR_ALLOW_SCREEN_CAPTURE"] = "1"
    os.environ.pop("PROCTOR_STUDENT_NAME", None)
    app = QApplication.instance() or QApplication([])
    original_enable = environment_protection.enable

    def enable_for_demo(callback=None, *, hwnd=None, config=None):
        config = config or environment_protection.ProtectionConfig(protect_capture=False)
        result = original_enable(callback, hwnd=hwnd, config=replace(
            config, max_seconds=PROTECTION_SECONDS, protect_capture=False))
        # The protection module has its own watchdog; this UI timer is additional.
        QTimer.singleShot(PROTECTION_SECONDS * 1000, environment_protection.disable)
        return result

    def capture(widget):
        folder = simulation_directory() / "ui-captures"
        folder.mkdir(parents=True, exist_ok=True)
        path = folder / f"{datetime.now():%Y%m%d-%H%M%S-%f}.png"
        if widget.grab().save(str(path), "PNG"):
            print(f"Screenshot saved: {path}", flush=True)

    def attach_shortcuts():
        for widget in app.topLevelWidgets():
            if widget.isVisible() and not hasattr(widget, "_simulation_capture_shortcut"):
                shortcut = QShortcut(QKeySequence("F8"), widget)
                shortcut.activated.connect(lambda w=widget: capture(w))
                widget._simulation_capture_shortcut = shortcut

    timer = QTimer(app)
    timer.timeout.connect(attach_shortcuts)
    environment_protection.enable = enable_for_demo
    timer.start(250)
    try:
        return run_application()
    finally:
        timer.stop()
        environment_protection.disable()
        environment_protection.enable = original_enable


def run_teacher() -> int:
    from core.storage import EventStore
    from teacher.__main__ import main as run_panel

    directory = simulation_directory()
    database = directory / "proctoring.db"
    # Opening the panel before the first student should show an empty list.
    if not database.exists():
        EventStore(database, directory / "screenshots").close()
    return run_panel(["--db", str(database), "--reviews", str(directory / "reviews.db")])


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("role", choices=("student", "teacher"))
    parser.add_argument("--check", action="store_true", help="Check imports without opening windows")
    args = parser.parse_args(argv)
    os.chdir(PROJECT)
    os.environ["PROCTOR_DATA_DIR"] = str(simulation_directory())
    if args.check:
        import ui.main_window  # noqa: F401
        import teacher.ui  # noqa: F401
        import keyboard  # noqa: F401
        import psutil  # noqa: F401
        import win32gui  # noqa: F401
        print(f"{args.role}: OK; data={simulation_directory()}; protection={PROTECTION_SECONDS}s")
        return 0
    simulation_directory().mkdir(parents=True, exist_ok=True)
    return run_student() if args.role == "student" else run_teacher()


if __name__ == "__main__":
    raise SystemExit(main())
