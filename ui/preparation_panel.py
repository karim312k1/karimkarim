"""Student-facing readiness screen; questions stay hidden until calibration."""
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame, QHBoxLayout, QLabel, QProgressBar, QPushButton, QVBoxLayout, QWidget,
)


class PreparationPanel(QWidget):
    def __init__(self, on_cancel, parent=None):
        super().__init__(parent)
        self.setObjectName('preparationPage')
        self.setStyleSheet('''
            QWidget#preparationPage { background: #f4f7fc; color: #182b50; }
            QFrame#preparationCard { background: white; border: 1px solid #dfe6f2;
                border-radius: 22px; }
            QLabel { background: transparent; color: #182b50; }
            QLabel#preparationEyebrow { color: #345cbb; font-size: 13px; font-weight: 700; }
            QLabel#preparationHeading { font-size: 30px; font-weight: 700; }
            QLabel#preparationHint { color: #65728c; font-size: 15px; }
            QLabel#preparationPreview { background: #eaf0fb; color: #5b719e;
                border: 2px solid #d4e0f7; border-radius: 18px; }
            QProgressBar { border: none; border-radius: 5px; background: #e9eef8;
                min-height: 10px; max-height: 10px; }
            QProgressBar::chunk { background: #3763d4; border-radius: 5px; }
            QPushButton { color: #334a75; background: white; border: 1px solid #ccd7eb;
                border-radius: 10px; padding: 12px 22px; font-weight: 600; }
            QPushButton:hover { background: #edf2fc; }
        ''')
        root = QVBoxLayout(self)
        root.setContentsMargins(40, 30, 40, 30)
        brand = QLabel('ARGUS  /  ПОДГОТОВКА К ТЕСТУ')
        brand.setObjectName('preparationEyebrow')
        root.addWidget(brand)
        root.addStretch()
        card = QFrame()
        card.setObjectName('preparationCard')
        row = QHBoxLayout(card)
        row.setContentsMargins(30, 32, 30, 32)
        row.setSpacing(32)
        left = QVBoxLayout()
        step = QLabel('ШАГ 1 ИЗ 2  ·  НАСТРОЙКА ЛИЦА')
        step.setObjectName('preparationEyebrow')
        left.addWidget(step)
        title = QLabel('Настраиваем\nраспознавание лица')
        title.setObjectName('preparationHeading')
        title.setWordWrap(True)
        left.addWidget(title)
        instructions = QLabel('Смотрите в центр экрана и держите голову прямо около 3 секунд. '
                              'В кадре должны быть видны лицо и глаза.')
        instructions.setObjectName('preparationHint')
        instructions.setWordWrap(True)
        left.addWidget(instructions)
        left.addSpacing(18)
        self.status = QLabel('Подключаем камеру и загружаем модели…')
        self.status.setWordWrap(True)
        left.addWidget(self.status)
        self.progress = QProgressBar()
        self.progress.setTextVisible(False)
        self.progress.setRange(0, 0)
        left.addWidget(self.progress)
        self.counter = QLabel('Подготовка может занять некоторое время при первом запуске')
        self.counter.setObjectName('preparationHint')
        self.counter.setWordWrap(True)
        left.addWidget(self.counter)
        left.addStretch()
        note = QLabel('Вопросы откроются автоматически после успешной настройки. '
                      'Движения на этом экране не считаются нарушениями.')
        note.setObjectName('preparationHint')
        note.setWordWrap(True)
        left.addWidget(note)
        row.addLayout(left, 1)
        right = QVBoxLayout()
        self.preview = QLabel('Изображение камеры появится здесь')
        self.preview.setObjectName('preparationPreview')
        self.preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview.setMinimumSize(440, 300)
        right.addWidget(self.preview, 1)
        caption = QLabel('Расположитесь по центру кадра · Лицо должно быть хорошо освещено')
        caption.setObjectName('preparationHint')
        caption.setAlignment(Qt.AlignmentFlag.AlignCenter)
        caption.setWordWrap(True)
        right.addWidget(caption)
        row.addLayout(right, 1)
        root.addWidget(card)
        root.addStretch()
        footer = QHBoxLayout()
        local = QLabel('Обработка на этом компьютере. Вы можете выйти в любой момент.')
        local.setObjectName('preparationHint')
        footer.addWidget(local, 1)
        self.cancel = QPushButton('Выйти')
        self.cancel.clicked.connect(on_cancel)
        footer.addWidget(self.cancel)
        root.addLayout(footer)

    def update_status(self, status):
        self.status.setText(status.message)
        self.progress.setRange(0, 100)
        self.progress.setValue(round(status.progress * 100))
        self.counter.setText('Подготовка остановлена. Выйдите и повторите запуск.' if status.error
                             else f'Настройка лица · {round(status.progress * 100)}%')
        self.status.setStyleSheet('color: #b13c48;' if status.error else '')
