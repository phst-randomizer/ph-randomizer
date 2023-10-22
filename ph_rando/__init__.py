from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version('ph_rando')
except PackageNotFoundError:
    __version__ = 'unknown_version'
