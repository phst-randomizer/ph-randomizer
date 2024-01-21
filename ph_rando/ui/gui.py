from pathlib import Path
import sys
from typing import NoReturn

from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QFileDialog,
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

from ph_rando.common import RANDOMIZER_SETTINGS


class RandomizerUi(QWidget):
    rom_path: Path

    def __init__(self) -> None:
        super().__init__()

        self.setWindowTitle('Phantom Hourglass Randomizer')
        layout = QFormLayout()
        self.setLayout(layout)

        self.render_file_open_ui()
        self.render_settings()
        self.render_bottom_panel()

    def _get_rom_file_select_widget(self) -> None:
        rom_input_widget = QWidget()
        hbox = QHBoxLayout()
        rom_input_widget.setLayout(hbox)
        file_path = QLineEdit()
        browse_button = QPushButton(text='Browse')
        hbox.addWidget(QLabel('Input ROM'))
        hbox.addWidget(file_path)
        hbox.addWidget(browse_button)

        def on_rom_path_click() -> None:
            self.rom_path = Path(
                QFileDialog.getOpenFileName(
                    parent=self, caption='Open ROM', dir='.', filter='*.nds'
                )[0]
            )
            file_path.setText(str(self.rom_path))

        def on_rom_path_change(path: str) -> None:
            self.rom_path = Path(path)
            file_path.setText(str(self.rom_path))

        browse_button.clicked.connect(on_rom_path_click)
        file_path.textChanged.connect(on_rom_path_change)

        return rom_input_widget

    def render_file_open_ui(self) -> None:
        layout = self.layout()
        groupbox = QGroupBox('ROM Selection')
        layout.addWidget(groupbox)
        vbox = QVBoxLayout()
        groupbox.setLayout(vbox)

        vbox.addWidget(self._get_rom_file_select_widget())

        seed_input_widget = QWidget()
        vbox.addWidget(seed_input_widget)
        hbox = QHBoxLayout()
        seed_input_widget.setLayout(hbox)
        seed = QLineEdit()
        gen_seed_button = QPushButton(text='Random Seed')
        hbox.addWidget(QLabel('Seed'))
        hbox.addWidget(seed)
        hbox.addWidget(gen_seed_button)

    def render_settings(self) -> None:
        groupbox = QGroupBox('Randomizer Settings')
        self.layout().addWidget(groupbox)

        hbox = QHBoxLayout()
        groupbox.setLayout(hbox)

        for i, setting in enumerate(RANDOMIZER_SETTINGS.values()):
            if i % 6 == 0:
                current_widget = QWidget()
                vbox = QVBoxLayout()
                current_widget.setLayout(vbox)
                hbox.addWidget(current_widget)

            internal_widget = QWidget()
            internal_hbox = QHBoxLayout()
            internal_widget.setLayout(internal_hbox)
            if setting.type == 'flag':
                chbox = QCheckBox(inflection.titleize(setting.name))
                chbox.setEnabled(setting.supported)
                internal_hbox.addWidget(chbox)
            else:
                assert (
                    setting.choices is not None
                ), f'setting.choices is None for setting {setting.name!r}'
                assert len(setting.choices) > 0, f'No options provided for setting {setting.name!r}'
                comboxbox_label = QLabel(inflection.titleize(setting.name))
                comboxbox = QComboBox()
                comboxbox.addItems([inflection.titleize(s) for s in setting.choices])
                comboxbox.setEnabled(setting.supported)
                internal_hbox.addWidget(comboxbox)
                internal_hbox.addWidget(comboxbox_label)
            vbox.addWidget(internal_widget)
            if setting.description:
                internal_widget.setToolTip(setting.description)

    def render_bottom_panel(self) -> None:
        layout = self.layout()
        container = QWidget()
        layout.addWidget(container)

        hbox = QHBoxLayout()
        container.setLayout(hbox)
        randomize_btn = QPushButton(text='Randomize')
        hbox.addWidget(randomize_btn)


def render_ui() -> NoReturn:
    app = QApplication(sys.argv)
    screen = RandomizerUi()
    screen.show()
    sys.exit(app.exec())
