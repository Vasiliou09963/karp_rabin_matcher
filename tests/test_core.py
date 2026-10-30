import unittest

from karp_rabin_matcher import KarpRabinMatcher, MatchResult


class TestKarpRabinMatcher(unittest.TestCase):
    def test_no_match(self) -> None:
        m = KarpRabinMatcher("xyz")
        self.assertEqual(m.search("abcdef"), [])

    def test_single_match(self) -> None:
        m = KarpRabinMatcher("abc")
        got = m.search("abcdef")
        self.assertEqual(got, [MatchResult(0, 3)])

    def test_overlapping_matches(self) -> None:
        m = KarpRabinMatcher("aa")
        got = m.search("aaaa")
        self.assertEqual(got, [MatchResult(0, 2), MatchResult(1, 3), MatchResult(2, 4)])

    def test_match_at_end(self) -> None:
        m = KarpRabinMatcher("def")
        got = m.search("abcdef")
        self.assertEqual(got, [MatchResult(3, 6)])

    def test_whole_text_is_pattern(self) -> None:
        m = KarpRabinMatcher("abc")
        got = m.search("abc")
        self.assertEqual(got, [MatchResult(0, 3)])

    def test_empty_pattern_returns_empty(self) -> None:
        m = KarpRabinMatcher("")
        self.assertEqual(m.search("abc"), [])

    def test_pattern_longer_than_text_returns_empty(self) -> None:
        m = KarpRabinMatcher("abcd")
        self.assertEqual(m.search("abc"), [])

    def test_empty_text_returns_empty(self) -> None:
        m = KarpRabinMatcher("abc")
        self.assertEqual(m.search(""), [])

    def test_duplicate_pattern_occurrences(self) -> None:
        m = KarpRabinMatcher("ab")
        got = m.search("ababab")
        self.assertEqual(
            got,
            [MatchResult(0, 2), MatchResult(2, 4), MatchResult(4, 6)],
        )

    def test_pattern_property(self) -> None:
        m = KarpRabinMatcher("hello")
        self.assertEqual(m.pattern, "hello")

    def test_type_error_on_non_str_pattern(self) -> None:
        with self.assertRaises(TypeError):
            KarpRabinMatcher(123)  # type: ignore[arg-type]

    def test_type_error_on_non_str_text(self) -> None:
        m = KarpRabinMatcher("abc")
        with self.assertRaises(TypeError):
            m.search(123)  # type: ignore[arg-type]

    def test_invalid_base_raises(self) -> None:
        with self.assertRaises(ValueError):
            KarpRabinMatcher("abc", base=0)

    def test_invalid_mod_raises(self) -> None:
        with self.assertRaises(ValueError):
            KarpRabinMatcher("abc", mod=1)

    def test_unicode_pattern_and_text(self) -> None:
        m = KarpRabinMatcher("élég")
        got = m.search(" café élégant ")
        self.assertEqual(got, [MatchResult(6, 10)])

    def test_match_result_is_frozen(self) -> None:
        r = MatchResult(1, 2)
        with self.assertRaises(Exception):
            r.start = 5  # type: ignore[misc]

    def test_results_sorted_ascending(self) -> None:
        m = KarpRabinMatcher("a")
        got = m.search("banana")
        starts = [r.start for r in got]
        self.assertEqual(starts, sorted(starts))
        self.assertEqual(starts, [1, 3, 5])


if __name__ == "__main__":
    unittest.main()
