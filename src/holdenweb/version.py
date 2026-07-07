from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("holdenweb")
except PackageNotFoundError:
    __version__ = "0.0.0+unknown"
