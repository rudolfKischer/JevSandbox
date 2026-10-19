import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from phonalign import units
from phonalign.config import SETTINGS
from phonalign.dialect import ipa, rules


class MapperTests(unittest.TestCase):
    def test_british_car(self):
        self.assertEqual(ipa.convert("k ɑː".split()), ["K", "AA"])

    def test_diphthong_pair(self):
        self.assertEqual(ipa.convert("b a ʊ t".split()), ["B", "AW", "T"])

    def test_affricate_pair(self):
        self.assertEqual(ipa.convert("d ʒ ɒ b".split()), ["JH", "AA", "B"])

    def test_unknown_token(self):
        self.assertIsNone(ipa.convert(["k", "☃"]))


class RuleTests(unittest.TestCase):
    def test_non_rhotic_drops_final_r(self):
        self.assertEqual(rules.non_rhotic(["K", "AA1", "R"]), ["K", "AA1"])

    def test_linking_r_stays_before_vowel(self):
        self.assertEqual(rules.non_rhotic(["V", "EH1", "R", "IY0"]), ["V", "EH1", "R", "IY0"])

    def test_final_er_becomes_schwa(self):
        self.assertEqual(rules.non_rhotic(["B", "AH1", "T", "ER0"]), ["B", "AH1", "T", "AH0"])

    def test_yod_needs_u_spelling(self):
        self.assertIn("Y", rules.yod(["T", "UW1", "N"], "tune"))
        self.assertNotIn("Y", rules.yod(["T", "UW1"], "too"))

    def test_bath_vowel(self):
        self.assertEqual(rules.bath(["B", "AE1", "TH"]), ["B", "AA1", "TH"])


class UnitTableTests(unittest.TestCase):
    def tearDown(self):
        SETTINGS["alignment"]["dialect"] = "us"
        units._CACHE.clear()

    def test_uk_table_allows_vowel_without_r(self):
        SETTINGS["alignment"]["dialect"] = "uk"
        units._CACHE.clear()
        self.assertTrue(units.compatible("ar", ["AA1"]))

    def test_us_table_does_not(self):
        SETTINGS["alignment"]["dialect"] = "us"
        units._CACHE.clear()
        self.assertFalse(units.compatible("ar", ["AA1"]))


if __name__ == "__main__":
    unittest.main()
