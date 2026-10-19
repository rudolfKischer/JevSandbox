import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from phonalign.gold import is_exact, load_gold
from phonalign.models import Unit, canonical, parse_units, render_units


class GoldTests(unittest.TestCase):
    def test_units_cover_word_and_pronunciation(self):
        for entry in [e for e in load_gold("starter+edge") if e["gold"]]:
            letters = "".join(unit.spelling for unit in entry["gold"])
            sounds = [sound for unit in entry["gold"] for sound in unit.sounds]
            self.assertEqual(letters, entry["word"], entry["id"])
            self.assertEqual(sounds, entry["pron"].split(), entry["id"])

    def test_ids_unique(self):
        ids = [entry["id"] for entry in load_gold()]
        self.assertEqual(len(ids), len(set(ids)))


class ModelTests(unittest.TestCase):
    def test_round_trip(self):
        text = "kn:N igh:AY1 t:T e:-"
        self.assertEqual(render_units(parse_units(text)), text)

    def test_canonical_merges_silent_runs(self):
        merged = canonical(parse_units("k:- n:N g:- h:- t:T"))
        self.assertEqual([u.spelling for u in merged], ["k", "n", "gh", "t"])

    def test_canonical_strips_stress(self):
        self.assertEqual(canonical([Unit("a", ("AE1",))])[0].sounds, ("AE",))


if __name__ == "__main__":
    unittest.main()
