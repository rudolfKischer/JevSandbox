import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from phonalign import letterism, units
from phonalign.gold import load_gold
from phonalign.models import canonical, render_units
from phonalign.pool import candidate_pool
from phonalign.tilings import top_tilings


def entry(word, pron):
    return {"word": word, "pron": pron, "gold": [], "accepted": []}


def rendered(pool):
    return {render_units(canonical(units_)) for units_ in pool}


class UnitTests(unittest.TestCase):
    def test_bossy_r_is_a_unit(self):
        self.assertTrue(units.compatible("ar", ["AA1", "R"]))

    def test_silent_pair(self):
        self.assertTrue(units.compatible("kn", ["N"]))

    def test_unknown_unit(self):
        self.assertFalse(units.compatible("zz", ["T", "S"]))

    def test_syllabic_le_carries_schwa(self):
        self.assertTrue(units.compatible("le", ["AH0", "L"]))
        self.assertFalse(units.compatible("le", ["L"]))


class TilingTests(unittest.TestCase):
    def test_pool_offers_unit_and_split(self):
        pool = rendered(candidate_pool(entry("car", "K AA1 R")))
        self.assertIn("c:K ar:AA+R", pool)

    def test_final_silent_e_is_free(self):
        costs = [cost for cost, _ in top_tilings("make", ["M", "EY1", "K"], 5, 1)]
        self.assertEqual(min(costs), 0)

    def test_gold_is_in_pool_for_most_words(self):
        words = [e for e in load_gold("starter+edge") if e["category"] == "word"]
        found = 0
        for item in words:
            options = {render_units(canonical(g)) for g in [item["gold"]] + item["accepted"]}
            found += bool(options & rendered(candidate_pool(item)))
        self.assertGreater(found / len(words), 0.95)


class LetterismTests(unittest.TestCase):
    def test_tv(self):
        parts = letterism.breakdown("tv", ["T", "IY1", "V", "IY1"])
        self.assertEqual([p["name"] for p in parts], ["tee", "vee"])

    def test_mismatch_returns_none(self):
        self.assertIsNone(letterism.breakdown("tv", ["T", "V"]))

    def test_alternate_name(self):
        parts = letterism.breakdown("zz", ["Z", "EH1", "D", "Z", "IY1"])
        self.assertEqual([p["name"] for p in parts], ["zed", "zee"])


if __name__ == "__main__":
    unittest.main()
