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

from ph_rando.common import RANDOMIZER_SETTINGS


class RandomizerUi(QWidget):
    def __init__(self) -> None:
        QWidget.__init__(self)

        self.setWindowTitle('Phantom Hourglass Randomizer')
        layout = QFormLayout()
        self.setLayout(layout)

        self.render_file_open_ui()
        self.render_settings()
        self.render_bottom_panel()

    def render_file_open_ui(self) -> None:
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

    def render_settings(self) -> None:
        groupbox = QGroupBox('Randomizer Settings')
        self.layout().addWidget(groupbox)

        hbox = QHBoxLayout()
        groupbox.setLayout(hbox)

        for i, setting in enumerate(RANDOMIZER_SETTINGS):
            if i % 6 == 0:
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
                assert (
                    setting.options is not None
                ), f'setting.options is None for setting {setting.name!r}'
                assert len(setting.options) > 0, f'No options provided for setting {setting.name!r}'
                comboxbox_label = QLabel(inflection.titleize(setting.name))
                comboxbox = QComboBox()
                comboxbox.addItems([inflection.titleize(s) for s in setting.options])
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


def render_ui() -> None:
    app = QApplication(sys.argv)
    screen = RandomizerUi()
    screen.show()
    sys.exit(app.exec())