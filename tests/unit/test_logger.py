"""
Testy pro logger modul.
"""

import sys
import os
# Přidat TalosForge do sys.path pro import
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'TalosForge'))

import pytest
from utils.logger import log_warning, log_error, _supports_color, _colorize


def test_log_warning(capsys):
    """Test WARNING logu"""
    log_warning("Test warning zpráva")
    captured = capsys.readouterr()
    assert "[WARNING]" in captured.out
    assert "Test warning zpráva" in captured.out


def test_log_error(capsys):
    """Test ERROR logu"""
    log_error("Test error zpráva")
    captured = capsys.readouterr()
    assert "[ERROR]" in captured.out
    assert "Test error zpráva" in captured.out


def test_colorize_without_tty(monkeypatch):
    """Test že bez TTY se nepřidávají barvy"""
    monkeypatch.setattr("sys.stdout.isatty", lambda: False)
    result = _colorize("test", "WARNING")
    assert result == "test"


def test_colorize_with_tty(monkeypatch):
    """Test že s TTY se přidávají barvy"""
    monkeypatch.setattr("sys.stdout.isatty", lambda: True)
    result = _colorize("test", "WARNING")
    assert "\033[" in result  # ANSI escape code


def test_supports_color(monkeypatch):
    """Test detekce TTY"""
    monkeypatch.setattr("sys.stdout.isatty", lambda: True)
    assert _supports_color() is True

    monkeypatch.setattr("sys.stdout.isatty", lambda: False)
    assert _supports_color() is False
