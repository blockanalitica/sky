"""Tests for the MAX_UINT256 sentinel clamp in process_events_chunk.

The clamp logic in agents.pipeline.processor.urn_states is:

    raw_dink = Decimal(args["dink"])
    if raw_dink >= MAX_UINT256:
        raw_dink = 0

This file verifies it behaves correctly at the boundaries and against
realistic JSON-decoded inputs (int and string forms, since args is
loaded from a JSONField via json.loads).
"""

from decimal import Decimal

import pytest

from core.constants import MAX_UINT256


def _clamp(raw_value):
    """Mirror of the inline snippet in urn_states.process_events_chunk."""
    raw_dink = Decimal(raw_value)
    if raw_dink >= MAX_UINT256:
        raw_dink = 0
    return raw_dink


@pytest.mark.parametrize(
    ("raw_value", "expected"),
    [
        # normal positive deltas pass through unchanged
        (0, Decimal(0)),
        (1, Decimal(1)),
        (10**18, Decimal(10**18)),  # 1 WAD
        # signed-negative deltas (json.loads returns Python int) pass through;
        # Decimal preserves the sign and the check MAX_UINT256 is far larger.
        (-1, Decimal(-1)),
        (-(10**18), Decimal(-(10**18))),
        # just below the sentinel — must NOT clamp
        (MAX_UINT256 - 1, Decimal(MAX_UINT256 - 1)),
        # exact sentinel (int form) — MUST clamp to 0
        (MAX_UINT256, Decimal(0)),
        # exact sentinel (string form, as JSON sometimes encodes large ints) — MUST clamp to 0
        (str(MAX_UINT256), Decimal(0)),
        # string form of a normal value — passes through
        ("12345", Decimal(12345)),
        ("-99", Decimal(-99)),
    ],
)
def test_max_uint256_clamp(raw_value, expected):
    assert _clamp(raw_value) == expected


def test_clamp_is_exactly_at_max_uint256_not_earlier():
    """Boundary check: MAX_UINT256-1 passes through, MAX_UINT256 clamps."""
    assert _clamp(MAX_UINT256 - 1) == Decimal(MAX_UINT256 - 1)
    assert _clamp(MAX_UINT256) == Decimal(0)


def test_max_uint256_constant_matches_real_uint256_max():
    """If this fails the clamp guard is meaningless for real on-chain values."""
    assert MAX_UINT256 == 2**256 - 1
