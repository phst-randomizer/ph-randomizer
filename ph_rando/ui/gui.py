import json
import logging
from pathlib import Path
import sys
from typing import NoReturn

from PySide6.QtCore import QObject, Qt, QThread, Signal, Slot
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
from ndspy.rom import NintendoDSRom

from ph_rando.common import RANDOMIZER_SETTINGS
from ph_rando.patcher._patcher import Patcher
from ph_rando.settings import SingleChoiceSetting
from ph_rando.shuffler._shuffler import Shuffler
from ph_rando.shuffler._spoiler_log import generate_spoiler_log
from ph_rando.shuffler._util import generate_random_seed


class RandomizerWorker(QObject):
    finished = Signal()

    def __init__(self) -> None:
        super().__init__()
        self.randomized_rom: NintendoDSRom
        self.rom_path: Path
        self.seed: str
        self.settings: dict[str, str | set[str] | bool]

    @Slot()
    def randomize(self) -> None:
        # Run the shuffler
        shuffled_aux_data = Shuffler(self.seed, self.settings).generate()

        # Generate spoiler log
        sl = generate_spoiler_log(shuffled_aux_data, self.settings).dict()
        (Path.cwd() / f'{self.seed}_spoiler.json').write_text(json.dumps(sl, indent=2))

        # Patch the rom
        patcher = Patcher(rom=self.rom_path, aux_data=shuffled_aux_data, settings=self.settings)
        self.randomized_rom = patcher.generate()
        self.finished.emit()


class RandomizerUi(QWidget):
    rom_path: Path | None
    seed: str | None
    settings: dict[str, bool | str | set[str]]
    randomizing_in_progress: bool

    def __init__(self) -> None:
        super().__init__()

        self.rom_path = None
        self.seed = None
        self.settings = {}

        self.worker: RandomizerWorker
        self._thread: QThread

        self.setWindowTitle('Phantom Hourglass Randomizer')
        layout = QFormLayout()
        self.setLayout(layout)

        self.render_file_open_ui()
        self.render_settings()
        self.render_bottom_panel()

    def _get_rom_file_select_widget(self) -> QWidget:
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

    def _get_seed_widget(self) -> QWidget:
        seed_widget = QWidget()
        hbox = QHBoxLayout()
        seed_widget.setLayout(hbox)
        seed = QLineEdit()
        hbox.addWidget(QLabel('Seed'))
        hbox.addWidget(seed)

        gen_seed_button = QPushButton(text='Random Seed')
        hbox.addWidget(gen_seed_button)

        def on_random_seed_click() -> None:
            self.seed = generate_random_seed()
            seed.setText(self.seed)

        def on_seed_change(value: str) -> None:
            self.seed = value
            seed.setText(value)

        gen_seed_button.clicked.connect(on_random_seed_click)
        seed.textChanged.connect(on_seed_change)

        return seed_widget

    def render_file_open_ui(self) -> None:
        layout = self.layout()

        groupbox = QGroupBox('ROM Selection')
        layout.addWidget(groupbox)
        vbox = QVBoxLayout()
        groupbox.setLayout(vbox)

        vbox.addWidget(self._get_rom_file_select_widget())
        vbox.addWidget(self._get_seed_widget())

    def render_settings(self) -> None:
        SETTINGS_INTERNAL_TO_HUMAN_READABLE = {
            setting_name: inflection.titleize(setting_name) for setting_name in RANDOMIZER_SETTINGS
        } | {
            choice: inflection.titleize(choice)
            for setting in [
                s for s in RANDOMIZER_SETTINGS.values() if isinstance(s, SingleChoiceSetting)
            ]
            for choice in setting.choices
        }
        SETTINGS_HUMAN_READABLE_TO_INTERNAL = {
            v: k for k, v in SETTINGS_INTERNAL_TO_HUMAN_READABLE.items()
        }

        groupbox = QGroupBox('Randomizer Settings')
        self.layout().addWidget(groupbox)

        hbox = QHBoxLayout()
        groupbox.setLayout(hbox)

        for i, setting in enumerate(RANDOMIZER_SETTINGS.values()):
            self.settings[setting.name] = setting.default

            if i % 6 == 0:
                current_widget = QWidget()
                vbox = QVBoxLayout()
                current_widget.setLayout(vbox)
                hbox.addWidget(current_widget)

            internal_widget = QWidget()
            internal_hbox = QHBoxLayout()
            internal_widget.setLayout(internal_hbox)
            if setting.type == 'flag':
                chbox = QCheckBox(SETTINGS_INTERNAL_TO_HUMAN_READABLE[setting.name])
                chbox.setEnabled(setting.supported)
                chbox.setChecked(setting.default)
                internal_hbox.addWidget(chbox)

                def _on_chbox_change(checkbox: QCheckBox, setting: str) -> None:
                    new_value = not self.settings[setting]
                    assert isinstance(new_value, bool)  # for type-checker
                    self.settings[setting] = new_value
                    checkbox.setChecked(new_value)

                chbox.clicked.connect(
                    lambda chbox=chbox, setting=setting.name: _on_chbox_change(chbox, setting)
                )
            elif setting.type == 'single_choice':
                assert (
                    setting.choices is not None
                ), f'setting.choices is None for setting {setting.name!r}'
                assert len(setting.choices) > 0, f'No options provided for setting {setting.name!r}'
                comboxbox_label = QLabel(inflection.titleize(setting.name))
                comboxbox = QComboBox()
                comboxbox.addItems([inflection.titleize(s) for s in setting.choices])
                comboxbox.setEnabled(setting.supported)
                comboxbox.setCurrentText(inflection.titleize(setting.default))
                internal_hbox.addWidget(comboxbox)
                internal_hbox.addWidget(comboxbox_label)

                def _on_cbox_change(cbox: QComboBox, setting: str) -> None:
                    self.settings[setting] = SETTINGS_HUMAN_READABLE_TO_INTERNAL[cbox.currentText()]

                comboxbox.currentTextChanged.connect(
                    lambda _, comboxbox=comboxbox, setting=setting.name: _on_cbox_change(
                        comboxbox, setting
                    )
                )

            vbox.addWidget(internal_widget)
            if setting.description:
                internal_widget.setToolTip(setting.description)

    def render_bottom_panel(self) -> None:
        layout = self.layout()

        def _on_randomize_button_click() -> None:
            # TODO: actually validate these properly instead of using asserts
            assert self.seed is not None
            assert self.settings is not None
            assert self.rom_path is not None

            status_label.setVisible(True)
            randomize_btn.setEnabled(False)

            def _on_randomize_finish() -> None:
                save_to = Path(
                    QFileDialog.getSaveFileName(
                        parent=self, caption='Save randomized ROM', dir='.', filter='*.nds'
                    )[0]
                )

                if save_to.suffix != '.nds':
                    save_to = save_to.parent / f'{save_to.name}.nds'

                self.worker.randomized_rom.saveToFile(save_to)
                status_label.setVisible(False)
                randomize_btn.setEnabled(True)

            self.worker = RandomizerWorker()
            self.worker.rom_path = self.rom_path
            self.worker.seed = self.seed
            self.worker.settings = self.settings

            self._thread = QThread()
            self.worker.moveToThread(self._thread)
            self._thread.started.connect(self.worker.randomize)
            self.worker.finished.connect(_on_randomize_finish)
            self.worker.finished.connect(self._thread.quit)
            self.worker.finished.connect(self.worker.deleteLater)
            self._thread.finished.connect(self._thread.deleteLater)
            self._thread.start()

        randomize_button_container = QWidget()
        status_label = QLabel(text='Please wait...')
        status_label.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        status_label.setVisible(False)
        hbox = QHBoxLayout()
        randomize_button_container.setLayout(hbox)
        randomize_btn = QPushButton(text='Randomize')
        hbox.addWidget(status_label)
        hbox.addWidget(randomize_btn)
        layout.addWidget(status_label)
        layout.addWidget(randomize_button_container)
        randomize_btn.clicked.connect(_on_randomize_button_click)


def render_ui() -> NoReturn:
    logging.basicConfig(level=logging.DEBUG)
    app = QApplication(sys.argv)
    screen = RandomizerUi()
    screen.show()
    sys.exit(app.exec())
