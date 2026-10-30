from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class MatchResult:
    """A single match reported by KarpRabinMatcher.search.

    Fields are kept strict and untyped-metadata-free so the result can be
    hashed and compared directly, which is useful in tests.
    """

    start: int
    end: int


class KarpRabinMatcher:
    """Karp-Rabin string matcher using a rolling polynomial hash.

    Choice of base and modulus
    --------------------------
    We use base=256 and modulus=1_000_000_007. The base equals the alphabet
    size for raw byte input so every distinct byte contributes a distinct
    term to the polynomial before reduction. The modulus is a large prime
    whose square fits comfortably inside a CPython (arbitrary-precision)
    integer; there is therefore no overflow concern and every intermediate
    value is a plain int. On CPython, small ints stay machine-word-sized,
    so the common path is cheap; only when a hash exceeds that threshold
    does Python transparently widen it. This keeps the implementation both
    portable and dependency-free.

    Why rolling
    -----------
    The defining feature of Karp-Rabin is O(1) hash update when the window
    advances: drop the leading byte's contribution and append the trailing
    byte's. We then verify any hash collision with a full slice equality
    check, so the matcher is always correct regardless of hash collisions;
    the hash only drives the filter.

    Determinism
    -----------
    Hashing is deterministic given the pattern and text: no randomisation,
    no salt, no secret base. The same inputs always yield the same matches.
    """

    __slots__ = ("_pattern", "_base", "_mod", "_pat_hash", "_high_pow")

    def __init__(
        self,
        pattern: str,
        *,
        base: int = 256,
        mod: int = 1_000_000_007,
    ) -> None:
        if not isinstance(pattern, str):
            raise TypeError(f"pattern must be str, got {type(pattern).__name__}")
        if not isinstance(base, int) or isinstance(base, bool):
            raise TypeError("base must be int")
        if not isinstance(mod, int) or isinstance(mod, bool):
            raise TypeError("mod must be int")
        if base <= 0:
            raise ValueError("base must be positive")
        if mod <= 1:
            raise ValueError("mod must be greater than 1")

        self._pattern: str = pattern
        self._base: int = base
        self._mod: int = mod
        # Precompute the pattern hash and base^(m-1) mod mod once so the
        # rolling update is a constant number of arithmetic operations.
        self._pat_hash: int = self._hash(pattern)
        self._high_pow: int = self._pow_mod(base, len(pattern) - 1, mod)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _hash(self, s: str) -> int:
        h = 0
        mod = self._mod
        base = self._base
        for ch in s:
            h = (h * base + ord(ch)) % mod
        return h

    @staticmethod
    def _pow_mod(base: int, exp: int, mod: int) -> int:
        """Compute base**exp mod mod via fast exponentiation.

        We avoid pow()'s three-argument form here only for transparency of
        the algorithm; both are O(log exp) in CPython. Using the static
        method keeps the helper callable without an instance.
        """
        result = 1 % mod
        b = base % mod
        e = exp
        while e > 0:
            if e & 1:
                result = (result * b) % mod
            b = (b * b) % mod
            e >>= 1
        return result

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    @property
    def pattern(self) -> str:
        return self._pattern

    def search(self, text: str) -> list[MatchResult]:
        """Return every start position of the pattern in text.

        Returns an empty list when the pattern is the empty string or longer
        than the text. Positions are 0-indexed and sorted ascending.
        """
        if not isinstance(text, str):
            raise TypeError(f"text must be str, got {type(text).__name__}")

        n = len(text)
        m = len(self._pattern)
        if m == 0 or m > n:
            return []

        mod = self._mod
        base = self._base
        pat = self._pattern
        target = self._pat_hash
        high_pow = self._high_pow

        # Seed the rolling hash with the first window.
        window_hash = self._hash(text[:m])
        results: list[MatchResult] = []

        # Because collisions are possible with any finite modulus, every
        # hash hit is confirmed by an actual string comparison. This makes
        # the matcher correct in all cases; the hash is only a filter.
        if window_hash == target and text[:m] == pat:
            results.append(MatchResult(0, m))

        for i in range(1, n - m + 1):
            # Rolling update: subtract the outgoing byte scaled by base^(m-1),
            # shift left by one base, add the incoming byte, reduce mod mod.
            # Adding mod before the first subtraction guarantees the
            # intermediate stays non-negative even after Python's % on a
            # negative dividend would already do the right thing — this is
            # belt-and-braces for readers who expect C-style modulo.
            window_hash = (
                (window_hash - ord(text[i - 1]) * high_pow) * base
                + ord(text[i + m - 1])
            ) % mod

            if window_hash == target and text[i : i + m] == pat:
                results.append(MatchResult(i, i + m))

        return results
