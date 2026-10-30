"""Tests for the non-GUI pieces: hotkey parsing, config persistence, profile names."""
import json
import os
import tempfile
import unittest

from config import ClickerConfig
from core.hotkey_manager import normalize_hotkey, is_valid_hotkey
from profile_manager import ProfileManager


class TestHotkeys(unittest.TestCase):
    def test_normalize(self):
        self.assertEqual(normalize_hotkey('F6'), '<f6>')
        self.assertEqual(normalize_hotkey('ctrl+shift+a'), '<ctrl>+<shift>+a')
        self.assertEqual(normalize_hotkey('Control+Escape'), '<ctrl>+<esc>')
        self.assertEqual(normalize_hotkey('<f7>'), '<f7>')
        self.assertEqual(normalize_hotkey(''), '')

    def test_valid(self):
        for hk in ('f6', 'f24', 'a', 'ctrl+shift+a', 'space'):
            self.assertTrue(is_valid_hotkey(hk), hk)
        for hk in ('', 'notakey', 'f25'):
            self.assertFalse(is_valid_hotkey(hk), hk)


class TestConfig(unittest.TestCase):
    def test_from_dict_ignores_unknown_and_defaults_missing(self):
        c = ClickerConfig.from_dict({'interval_ms': 5, 'removed_field': 1})
        self.assertEqual(c.interval_ms, 5)
        self.assertEqual(c.hotkey, 'f6')

    def test_save_load_roundtrip_leaves_no_tmp(self):
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, 'p.json')
            c = ClickerConfig(interval_ms=7, macro_steps=[{'action': 'move', 'x': 1, 'y': 2, 'delay_ms': 3}])
            self.assertTrue(c.save_to_file(path))
            self.assertEqual(ClickerConfig.load_from_file(path), c)
            self.assertEqual(os.listdir(d), ['p.json'])

    def test_failed_save_keeps_old_file(self):
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, 'p.json')
            ClickerConfig(interval_ms=7).save_to_file(path)
            bad = ClickerConfig(macro_steps=[object()])  # not JSON-serializable
            self.assertFalse(bad.save_to_file(path))
            with open(path, encoding='utf-8') as f:
                self.assertEqual(json.load(f)['interval_ms'], 7)
            self.assertEqual(os.listdir(d), ['p.json'])


class TestProfileNames(unittest.TestCase):
    def test_valid_names(self):
        for name in ('default', 'Game 1', 'tiếng việt', 'a.b'):
            self.assertTrue(ProfileManager.is_valid_name(name), name)

    def test_invalid_names(self):
        for name in ('', '   ', 'a/b', 'a\\b', 'a:b', 'what?', '_last_session', 'CON', 'com1', 'nul.txt', 'x.', 'a' * 65):
            self.assertFalse(ProfileManager.is_valid_name(name), name)

    def test_save_profile_rejects_invalid(self):
        with tempfile.TemporaryDirectory() as d:
            pm = ProfileManager(d)
            self.assertFalse(pm.save_profile('_last_session', ClickerConfig()))
            self.assertTrue(pm.save_profile('ok', ClickerConfig()))
            self.assertEqual(pm.list_profiles(), ['ok'])


if __name__ == '__main__':
    unittest.main()
