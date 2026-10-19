import sys
import time
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from phonalign import lexicon
from phonalign.config import SETTINGS
from phonalign.methods import q_pool, r_route
from phonalign.pool import candidate_pool
import phonalign.units as units


def entry(word, pron):
    return {"word": word, "pron": pron, "gold": [], "accepted": []}


def first_choice(state, questions):
    answers = {}
    for key, question in questions.items():
        keys = list(question["criteria"])
        answers[key] = {"probabilities": {k: (1.0 if i == 0 else 0.0) for i, k in enumerate(keys)}}
    return answers


class LexiconTests(unittest.TestCase):
    def test_abbreviation_finds_expansion(self):
        self.assertEqual(lexicon.expansions("mr", ["M", "IH1", "S", "T", "ER0"])[0], "mister")

    def test_homophone_spelling_is_not_an_expansion(self):
        self.assertEqual(lexicon.expansions("burger", ["B", "ER1", "G", "ER0"]), [])


class PoolTests(unittest.TestCase):
    def test_long_word_is_fast_and_capped(self):
        started = time.time()
        pool = candidate_pool(entry("unbelievable", "AH2 N B AH0 L IY1 V AH0 B AH0 L"))
        self.assertLess(time.time() - started, 2)
        self.assertLessEqual(len(pool), SETTINGS["alignment"]["pool_cap"])

    def test_syllabic_l_needs_a_schwa(self):
        pool = candidate_pool(entry("fields", "F IY1 L D Z"))
        self.assertTrue(all(all(u.spelling != "el" for u in units_) for units_ in pool))


class GraphemeSchemeTests(unittest.TestCase):
    def setUp(self):
        SETTINGS["alignment"]["scheme"] = "grapheme"
        units._CACHE.clear()

    def tearDown(self):
        SETTINGS["alignment"]["scheme"] = "teaching"
        units._CACHE.clear()

    def test_vowel_part_of_split_unit_is_known(self):
        self.assertTrue(units.compatible("ea", ["IH1"]))

    def test_r_can_spell_er(self):
        self.assertTrue(units.compatible("r", ["ER0"]))


class BatchTests(unittest.TestCase):
    def test_batch_matches_single(self):
        words = [entry("knight", "N AY1 T"), entry("cat", "K AE1 T"), entry("queen", "K W IY1 N")]
        batch = q_pool.run_batch(words, first_choice)
        single = [q_pool.run(w, first_choice) for w in words]
        self.assertEqual([r.units for r in batch], [r.units for r in single])

    def test_category_mapping(self):
        self.assertEqual(r_route.category_of("acronym"), "word")
        self.assertEqual(r_route.category_of("initialism"), "initialism")
        self.assertEqual(r_route.category_of("mixed"), "mixed")


if __name__ == "__main__":
    unittest.main()
