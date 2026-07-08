from unittest.mock import MagicMock, patch

from vindex.core.plugins import (
    get_extractor_plugins,
    get_output_plugins,
    get_runtime_plugins,
    load_plugins,
)


def test_load_plugins_mock():
    mock_ep = MagicMock()
    mock_ep.name = "mock_plugin"
    mock_ep.load.return_value = "LoadedModule"
    
    with patch("vindex.core.plugins.entry_points", return_value=[mock_ep]):
        plugins = load_plugins("vindex.test")
        assert "mock_plugin" in plugins
        assert plugins["mock_plugin"] == "LoadedModule"


def test_get_extractor_plugins_mock():
    mock_ep = MagicMock()
    mock_ep.name = "mock_extractor"
    mock_ep.load.return_value = "ExtractorClass"
    
    with patch("vindex.core.plugins.entry_points", return_value=[mock_ep]) as mock_entry_points:
        plugins = get_extractor_plugins()
        mock_entry_points.assert_called_once_with(group="vindex.extractors")
        assert "mock_extractor" in plugins
        assert plugins["mock_extractor"] == "ExtractorClass"


def test_get_runtime_plugins_mock():
    mock_ep = MagicMock()
    mock_ep.name = "mock_runtime"
    mock_ep.load.return_value = "RuntimeClass"
    
    with patch("vindex.core.plugins.entry_points", return_value=[mock_ep]) as mock_entry_points:
        plugins = get_runtime_plugins()
        mock_entry_points.assert_called_once_with(group="vindex.runtimes")
        assert "mock_runtime" in plugins
        assert plugins["mock_runtime"] == "RuntimeClass"


def test_get_output_plugins_mock():
    mock_ep = MagicMock()
    mock_ep.name = "mock_output"
    mock_ep.load.return_value = "OutputClass"
    
    with patch("vindex.core.plugins.entry_points", return_value=[mock_ep]) as mock_entry_points:
        plugins = get_output_plugins()
        mock_entry_points.assert_called_once_with(group="vindex.outputs")
        assert "mock_output" in plugins
        assert plugins["mock_output"] == "OutputClass"
