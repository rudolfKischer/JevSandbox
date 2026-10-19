import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from phonalign import em, progress, units
from phonalign.config import SETTINGS
from phonalign.models import parse_units, render_units
from phonalign.pool import candidate_pool, stressed_syllabic, with_teams_intact
from phonalign.runner import verdict_for
from phonalign.tilings import cross_cost, units_cost


def pool_of(word, pron):
    return {render_units(candidate) for candidate in candidate_pool({"word": word, "pron": pron, "gold": [], "accepted": []})}


class CleanTableTests(unittest.TestCase):
    def test_consonant_letters_do_not_spell_vowels(self):
        self.assertTrue(units.cross_type("s", ["EY"]))
        self.assertFalse(units.cross_type("a", ["EY"]))
        self.assertFalse(units.cross_type("y", ["IY"]))

    def test_curated_units_exist(self):
        self.assertTrue(units.compatible("gh", ["K"]))
        self.assertTrue(units.compatible("mc", ["M", "AH", "K"]))
        self.assertTrue(units.compatible("oi", ["W", "AA"]))

    def test_off_catalog_guess_costs_more_across_types(self):
        self.assertGreater(cross_cost("s", ["EY"]), cross_cost("a", ["EY"]))
        self.assertGreater(units_cost(parse_units("s:EY1")), units_cost(parse_units("a:EY1")))

    def test_cost_lowers_the_score(self):
        good = parse_units("c:K a:AE1 t:T")
        bad = parse_units("c:K a:AE1 t:T s:-")
        self.assertGreater(em.catalog_cost(tuple(bad)), em.catalog_cost(tuple(good)))


class KeepWholeTests(unittest.TestCase):
    def test_vowel_team_beats_soft_c_stealing_a_letter(self):
        pool = pool_of("deceived", "D IH0 S IY1 V D")
        self.assertIn("d:D e:IH0 c:S ei:IY1 v:V ed:D", pool)
        self.assertNotIn("d:D e:IH0 ce:S i:IY1 v:V ed:D", pool)

    def test_double_consonant_is_not_split(self):
        pool = pool_of("wallets", "W AO1 L AH0 T S")
        self.assertIn("w:W a:AO1 ll:L e:AH0 t:T s:S", pool)
        self.assertNotIn("w:W al:AO1 l:L e:AH0 t:T s:S", pool)

    def test_gu_beats_g_plus_ui(self):
        pool = pool_of("plaguing", "P L EY1 G IH0 NG")
        self.assertTrue(any("gu:G i:IH0" in text for text in pool))
        self.assertFalse(any("g:G ui:IH0" in text for text in pool))

    def test_gu_and_qu_are_exempt_from_team_rule(self):
        pool = pool_of("guessing", "G EH1 S IH0 NG")
        self.assertTrue(any(text.startswith("gu:G e:EH1") for text in pool))

    def test_rule_never_empties_a_pool(self):
        self.assertEqual(with_teams_intact([]), [])

    def test_syllabic_never_takes_a_stressed_vowel(self):
        self.assertTrue(stressed_syllabic(parse_units("m:M ul:AH1+L t:T")))
        self.assertFalse(stressed_syllabic(parse_units("l:L i:IH1 t:T le:AH0+L")))
        pool = pool_of("multipart", "M AH1 L T IY0 P AA2 R T")
        self.assertTrue(all("ul:AH+L" not in text for text in pool))

    def test_syllabic_m_goes_to_the_m(self):
        pool = pool_of("tourism", "T UH1 R IH2 Z AH0 M")
        self.assertIn("t:T our:UH1+R i:IH2 s:Z m:AH0+M", pool)


class JudgedAnswerTests(unittest.TestCase):
    def entry(self):
        return {"judge": {"verdict": "ok", "units": "c:K a:AE1 t:T", "alts": {"k:K a:AE1 t:T": {"verdict": "wrong"}}}}

    def test_judged_answer_matches(self):
        self.assertEqual(verdict_for(self.entry(), parse_units("c:K a:AE1 t:T"))["verdict"], "ok")

    def test_alternate_answer_has_its_own_verdict(self):
        self.assertEqual(verdict_for(self.entry(), parse_units("k:K a:AE1 t:T"))["verdict"], "wrong")

    def test_unseen_answer_is_unread(self):
        self.assertIsNone(verdict_for(self.entry(), parse_units("c:K aa:AE1 t:T")))


class RouteTests(unittest.TestCase):
    def test_weak_kind_call_stays_ordinary(self):
        from phonalign.methods.r_route import confident_kind
        self.assertEqual(confident_kind("abbreviation", 0.505)[0], "ordinary")
        self.assertEqual(confident_kind("abbreviation", 0.71)[0], "abbreviation")
        self.assertEqual(confident_kind("ordinary", 0.4)[0], "ordinary")


class ProgressTests(unittest.TestCase):
    def test_bar_counts(self):
        bar = progress.Bar(10, "x")
        bar.update(4, "note")
        self.assertEqual(bar.done, 4)
        bar.close()


if __name__ == "__main__":
    unittest.main()
