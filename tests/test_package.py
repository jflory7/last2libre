from types import ModuleType


def test_import():
    from last2libre import __version__, last2libre_cli, exporter, importer
    assert type(__version__) is str
    assert type(last2libre_cli) is ModuleType
    assert type(exporter) is ModuleType
    assert type(importer) is ModuleType
