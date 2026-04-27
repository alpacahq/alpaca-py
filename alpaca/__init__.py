from importlib.metadata import PackageNotFoundError, version

# placeholder for poetry-dynamic-versioning
try:
    __version__ = version("alpaca-py")
except PackageNotFoundError:
    __version__ = "0.0.0"
