# karp_rabin_matcher

A rolling-hash string matcher that preprocesses a pattern, then reports every start position of that pattern in a text in expected linear time, using only the Python standard library.

```python
from karp_rabin_matcher import KarpRabinMatcher

matcher = KarpRabinMatcher("ab")
for match in matcher.search("ababab"):
    print(match.start, match.end)
# 0 2
# 2 4
# 4 6
```

The exported names are `KarpRbinMatcher` and `MatchResult`. `KarpRabinMatcher(pattern, *, base=256, mod=1_000_000_007)` preprocesses the pattern; `.search(text)` returns a `list[MatchResult]` sorted by ascending start position. `MatchResult` is a frozen dataclass with integer fields `start` (inclusive) and `end` (exclusive).

## Why this exists

The problem is straightforward: find every occurrence of a fixed pattern in a text, including overlapping ones, without pulling in a dependency. Karp-Rabin gives a clean answer — a rolling polynomial hash lets each new window be tested in constant time, and a full string comparison on every hash hit guarantees correctness even when the hash collides. The trade-off is that the hash is a filter, not a proof: worst-case input can force O(nm) comparisons, but for realistic text the expected cost is linear. This library commits to that trade-off plainly rather than trying to be clever about collision avoidance.

Base 256 and a large prime modulus (`1_000_000_007`) keep the arithmetic inside CPython's fast small-int path for typical inputs while making spontaneous collisions rare. No randomisation is used, so results are fully deterministic for a given pattern and text.

## Edge cases you will hit

- An **empty pattern** returns no matches, rather than the "match at every position" semantics some textbooks describe. This is a deliberate choice: returning `[]` is less surprising for callers who immediately index into `text[start:end]`.
- A pattern **longer than the text** returns `[]`.
- **Overlapping** matches are all reported (e.g. `"aa"` in `"aaaa"` yields starts 0, 1, and 2).
- Input must be `str`; passing `bytes` or any non-string type raises `TypeError`. Convert `bytes` with `.decode()` first if you need to search raw byte data.
