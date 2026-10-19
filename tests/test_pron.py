import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from phonalign.pron import hints, runner, unitg2p
from phonalign.pron.pick import merge, question_set


class HintTests(unittest.TestCase):
    def test_respelling(self):
        self.assertEqual(hints.respell(["K", "AE1", "T"]), "k-a-t")

    def test_rhyme_word_ends_the_same(self):
        word = hints.rhyme_word(["R", "EH1", "D"], "read")
        self.assertIsNotNone(word)

    def test_style_without_rhyme(self):
        self.assertNotIn("ends like", hints.describe(["K", "AE1", "T"], "cat", "respell"))


class ScoreTests(unittest.TestCase):
    def test_distance(self):
        self.assertEqual(runner.distance(["K", "AE", "T"], ["K", "AA", "T"]), 1)
        self.assertEqual(runner.distance([], ["K"]), 1)

    def test_score_accepts_any_variant(self):
        item = {"truth": ["R IY1 D", "R EH1 D"]}
        row = runner.score({"pred": ["R", "EH", "D"]}, item)
        self.assertTrue(row["exact"])


class PickTests(unittest.TestCase):
    def test_questions_cover_both_orders(self):
        item = {"word": "read"}
        questions = question_set(item, [["R", "IY"], ["R", "EH"]], "w0_", "respell")
        self.assertEqual(sorted(questions), ["w0_o0", "w0_o1"])

    def test_merge_returns_one_share_per_candidate(self):
        answers = {"w0_o0": {"probabilities": {"a": 1.0, "b": 0.0}}, "w0_o1": {"probabilities": {"a": 1.0, "b": 0.0}}}
        totals = merge(answers, 2, "read", "w0_")
        self.assertAlmostEqual(sum(totals), 1.0)


class UnitG2PTests(unittest.TestCase):
    def test_generates_something_for_a_simple_word(self):
        self.assertTrue(unitg2p.generate("cat"))


if __name__ == "__main__":
    unittest.main()
