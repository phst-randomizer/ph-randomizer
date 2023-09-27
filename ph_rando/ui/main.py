import sys

from ph_rando.ui.cli import randomizer_cli


def main() -> None:
    if '--no-gui' in sys.argv:
        sys.argv.remove('--no-gui')
        randomizer_cli()
    else:
        from ph_rando.ui.gui import render_ui

        render_ui()


if __name__ == '__main__':
    main()
