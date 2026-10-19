import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from phonalign import m2m
from phonalign.models import parse_units
from phonalign.sources.common import merge_schwa
from phonalign.sources.compare import DIFFERENT, IDENTICAL, STRUCTURE, relation


class RelationTests(unittest.TestCase):
    def test_identical(self):
        a = parse_units("c:K a:AE1 t:T")
        self.assertEqual(relation(a, parse_units("c:K a:AE1 t:T")), IDENTICAL)

    def test_silent_letter_placement_is_structure_only(self):
        ours = parse_units("kn:N igh:AY1 t:T")
        theirs = parse_units("kn:N i:AY1 gh:- t:T")
        self.assertEqual(relation(ours, theirs), STRUCTURE)

    def test_different_grouping(self):
        self.assertEqual(relation(parse_units("c:K ar:AA1+R"), parse_units("c:K a:AA1 r:R")), DIFFERENT)

    def test_sounds_ignored_when_asked(self):
        self.assertEqual(relation(parse_units("c:K a:AE1 t:T"), parse_units("c:? a:? t:?"), False), STRUCTURE)

    def test_syllabic_unit_equals_schwa_plus_l(self):
        ours = parse_units("f:F i:AY n:N al:AH+L")
        theirs = parse_units("f:F i:AY n:N a:AH l:L")
        self.assertEqual(relation(ours, theirs), IDENTICAL)

    def test_schwa_and_syllabic_are_one_chunk(self):
        merged = merge_schwa(parse_units("l:L e:AH l:L"))
        self.assertEqual([u.spelling for u in merged], ["l", "el"])


class AlignerTests(unittest.TestCase):
    def test_unsupervised_pass_aligns_a_simple_word(self):
        pairs = [("cat", ["K", "AE", "T"]), ("cap", ["K", "AE", "P"]), ("sat", ["S", "AE", "T"])] * 5
        probs = m2m.train(pairs, rounds=3)
        units = m2m.align("cat", ["K", "AE", "T"], probs)
        self.assertEqual("".join(u.spelling for u in units), "cat")
        self.assertEqual([s for u in units for s in u.sounds], ["K", "AE", "T"])


if __name__ == "__main__":
    unittest.main()
