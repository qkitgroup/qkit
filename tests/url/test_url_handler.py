from parsita import Success

from qkit.gui.plot.url_launcher import QviewkitURLParser


def test_basic_url():
    result = QviewkitURLParser.url_pattern.parse("qviewkit://ABCDEF")
    assert result == Success(['ABCDEF', {}])
    result = QviewkitURLParser.url_pattern.parse("qviewkit://ABCDEF/")
    assert result == Success(['ABCDEF', {}])


def test_url_with_repo():
    result = QviewkitURLParser.url_pattern.parse("qviewkit://ABCDEF?repo=https://measurements.phi.kit.edu")
    assert result == Success(['ABCDEF', {'repo': 'https://measurements.phi.kit.edu'}])


def test_primitive_extraction():
    uuid, kvs = QviewkitURLParser.parse("qviewkit://ABCDEF?repo=https://measurements.phi.kit.edu")
    assert uuid == 'ABCDEF'
    assert kvs['repo'] == 'https://measurements.phi.kit.edu'


def test_extensibility():
    uuid, kvs = QviewkitURLParser.parse("qviewkit://ABCDEF?repo=https://measurements.phi.kit.edu&orig=10.0.0.1")
    assert uuid == 'ABCDEF'
    assert kvs['repo'] == 'https://measurements.phi.kit.edu'
    assert kvs['orig'] == '10.0.0.1'
