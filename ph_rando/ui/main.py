import json
from pathlib import Path
import sys

from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)
import inflection

from ph_rando.settings import Settings

with open(Path(__file__).parents[1] / 'settings.json') as f:
    settings = Settings(**json.load(f)).settings


class RandomizerUi(QWidget):
    def __init__(self):
        QWidget.__init__(self)

        self.setWindowTitle('Phantom Hourglass Randomizer')
        layout = QFormLayout()
        self.setLayout(layout)

        self.render_file_open_ui()
        self.render_settings()

    def render_file_open_ui(self):
        layout = self.layout()
        groupbox = QGroupBox('ROM Selection')
        layout.addWidget(groupbox)
        vbox = QVBoxLayout()
        groupbox.setLayout(vbox)

        rom_input_widget = QWidget()
        vbox.addWidget(rom_input_widget)
        hbox = QHBoxLayout()
        rom_input_widget.setLayout(hbox)
        file_path = QLineEdit()
        browse_button = QPushButton(text='Browse')
        hbox.addWidget(QLabel('Input ROM'))
        hbox.addWidget(file_path)
        hbox.addWidget(browse_button)

        seed_input_widget = QWidget()
        vbox.addWidget(seed_input_widget)
        hbox = QHBoxLayout()
        seed_input_widget.setLayout(hbox)
        seed = QLineEdit()
        gen_seed_button = QPushButton(text='Random Seed')
        hbox.addWidget(QLabel('Seed'))
        hbox.addWidget(seed)
        hbox.addWidget(gen_seed_button)

    def render_settings(self):
        groupbox = QGroupBox('Randomizer Settings')
        self.layout().addWidget(groupbox)

        hbox = QHBoxLayout()
        groupbox.setLayout(hbox)

        for i, setting in enumerate(settings):
            if i % 2 == 0:
                current_widget = QWidget()
                vbox = QVBoxLayout()
                current_widget.setLayout(vbox)
                hbox.addWidget(current_widget)

            internal_widget = QWidget()
            internal_hbox = QHBoxLayout()
            internal_widget.setLayout(internal_hbox)
            if setting.flag:
                internal_hbox.addWidget(QCheckBox(inflection.titleize(setting.name)))
            else:
                comboxbox_label = QLabel(inflection.titleize(setting.name))
                comboxbox = QComboBox()
                comboxbox.addItems([inflection.titleize(s) for s in setting.options])
                internal_hbox.addWidget(comboxbox)
                internal_hbox.addWidget(comboxbox_label)
            vbox.addWidget(internal_widget)
            if setting.description:
                internal_widget.setToolTip(setting.description)


app = QApplication(sys.argv)
screen = RandomizerUi()
screen.show()
sys.exit(app.exec())
