import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from phonalign import concepts, scheme
from phonalign.methods.q_pool import arrangements, merge
from phonalign.models import parse_units


class SchemeTests(unittest.TestCase):
    def test_vowel_r_splits(self):
        parts = scheme.to_grapheme_scheme(parse_units("c:K ar:AA1+R"))
        self.assertEqual([u.spelling for u in parts], ["c", "a", "r"])

    def test_qu_splits(self):
        parts = scheme.to_grapheme_scheme(parse_units("qu:K+W ee:IY1 n:N"))
        self.assertEqual([u.spelling for u in parts], ["q", "u", "ee", "n"])

    def test_ore_leaves_silent_e(self):
        parts = scheme.to_grapheme_scheme(parse_units("m:M ore:AO1+R"))
        self.assertEqual([(u.spelling, bool(u.sounds)) for u in parts], [("m", True), ("o", True), ("r", True), ("e", False)])

    def test_x_stays(self):
        self.assertEqual(len(scheme.to_grapheme_scheme(parse_units("b:B o:AA1 x:K+S"))), 3)


class ConceptTests(unittest.TestCase):
    def test_r_controlled_and_blend(self):
        found = concepts.detect(parse_units("s:S t:T a:AA1 r:R"))
        self.assertEqual(found["r-controlled"], ["ar"])
        self.assertEqual(found["blend"], ["st"])

    def test_silent_e(self):
        self.assertEqual(concepts.detect(parse_units("m:M a:EY1 k:K e:-"))["silent e"], ["ake"])


class ArrangementTests(unittest.TestCase):
    def test_two_different_orders(self):
        first, second = arrangements(5, "knight")
        self.assertEqual(second, first[::-1])
        self.assertEqual(sorted(first), list(range(5)))

    def test_merge_maps_labels_back(self):
        first, _ = arrangements(3, "dog")
        answers = {"o0": {"probabilities": {"a": 1.0}}, "o1": {"probabilities": {"a": 1.0}}}
        totals = merge(answers, 3, "dog")
        self.assertAlmostEqual(totals[first[0]] + totals[first[::-1][0]], 1.0)


if __name__ == "__main__":
    unittest.main()
