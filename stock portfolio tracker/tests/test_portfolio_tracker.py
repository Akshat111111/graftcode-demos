"""
Comprehensive unit tests for PortfolioTracker.

Design constraints (per AGENTS.md):
- pytest only
- Fully offline — no network calls, no Docker dependency
- Fast — pure in-memory operations
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

# Make the parent directory importable regardless of where pytest is invoked
_parent = str(Path(__file__).resolve().parent.parent)
if _parent not in sys.path:
    sys.path.insert(0, _parent)

from portfolio_tracker.tracker import PortfolioTracker  # noqa: E402

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def empty_tracker() -> PortfolioTracker:
    """A freshly-created, empty PortfolioTracker."""
    return PortfolioTracker()


@pytest.fixture()
def single_position_tracker() -> PortfolioTracker:
    """Tracker with one AAPL position (100 shares @ $150, current $180)."""
    t = PortfolioTracker()
    t.add_position("AAPL", shares=100.0, avg_cost=150.0)
    t.update_price("AAPL", current_price=180.0)
    return t


@pytest.fixture()
def multi_position_tracker() -> PortfolioTracker:
    """
    Tracker with three positions:
      AAPL: 100 shares @ $150 cost, current $180  → value=$18 000, P&L=+$3 000
      MSFT: 50  shares @ $300 cost, current $280  → value=$14 000, P&L=−$1 000
      TSLA: 20  shares @ $200 cost, current $200  → value= $4 000, P&L= $0
    Total value: $36 000 | Total cost: $36 000 | Net P&L: +$2 000
    """
    t = PortfolioTracker()
    t.add_position("AAPL", shares=100.0, avg_cost=150.0)
    t.update_price("AAPL", current_price=180.0)

    t.add_position("MSFT", shares=50.0, avg_cost=300.0)
    t.update_price("MSFT", current_price=280.0)

    t.add_position("TSLA", shares=20.0, avg_cost=200.0)
    # TSLA price stays at avg_cost (no update_price call) — zero P&L
    return t


# ---------------------------------------------------------------------------
# add_position
# ---------------------------------------------------------------------------


class TestAddPosition:
    def test_add_new_position(self, empty_tracker: PortfolioTracker) -> None:
        empty_tracker.add_position("AAPL", shares=10.0, avg_cost=100.0)
        summary = empty_tracker.get_position_summary("AAPL")
        assert summary["shares"] == 10.0
        assert summary["avg_cost"] == 100.0

    def test_add_position_case_insensitive(
        self, empty_tracker: PortfolioTracker
    ) -> None:
        empty_tracker.add_position("aapl", shares=5.0, avg_cost=50.0)
        # Should be reachable via upper-case ticker
        summary = empty_tracker.get_position_summary("AAPL")
        assert summary["shares"] == 5.0

    def test_add_position_sets_current_price_to_avg_cost(
        self, empty_tracker: PortfolioTracker
    ) -> None:
        empty_tracker.add_position("GOOG", shares=2.0, avg_cost=175.0)
        summary = empty_tracker.get_position_summary("GOOG")
        assert summary["current_price"] == 175.0

    def test_overwrite_position_preserves_current_price(
        self, single_position_tracker: PortfolioTracker
    ) -> None:
        """Overwriting AAPL should keep current_price=$180, not reset to avg_cost."""
        single_position_tracker.add_position("AAPL", shares=200.0, avg_cost=160.0)
        summary = single_position_tracker.get_position_summary("AAPL")
        assert summary["shares"] == 200.0
        assert summary["avg_cost"] == 160.0
        assert summary["current_price"] == 180.0  # preserved

    def test_add_position_zero_avg_cost_allowed(
        self, empty_tracker: PortfolioTracker
    ) -> None:
        """Zero avg_cost is valid (e.g. inherited/gifted shares).

        percentage_return is None rather than raising, because cost basis is 0.
        """
        empty_tracker.add_position("XYZ", shares=10.0, avg_cost=0.0)
        summary = empty_tracker.get_position_summary("XYZ")
        assert summary["avg_cost"] == 0.0
        assert summary["percentage_return"] is None  # undefined when cost basis == 0

    def test_add_position_negative_shares_raises(
        self, empty_tracker: PortfolioTracker
    ) -> None:
        with pytest.raises(ValueError, match="shares must be greater than zero"):
            empty_tracker.add_position("AAPL", shares=-5.0, avg_cost=100.0)

    def test_add_position_zero_shares_raises(
        self, empty_tracker: PortfolioTracker
    ) -> None:
        with pytest.raises(ValueError, match="shares must be greater than zero"):
            empty_tracker.add_position("AAPL", shares=0.0, avg_cost=100.0)

    def test_add_position_negative_avg_cost_raises(
        self, empty_tracker: PortfolioTracker
    ) -> None:
        with pytest.raises(ValueError, match="avg_cost must be non-negative"):
            empty_tracker.add_position("AAPL", shares=10.0, avg_cost=-1.0)


# ---------------------------------------------------------------------------
# remove_position
# ---------------------------------------------------------------------------


class TestRemovePosition:
    def test_remove_existing_position(
        self, single_position_tracker: PortfolioTracker
    ) -> None:
        result = single_position_tracker.remove_position("AAPL")
        assert result is True

    def test_remove_existing_position_actually_removes_it(
        self, single_position_tracker: PortfolioTracker
    ) -> None:
        single_position_tracker.remove_position("AAPL")
        with pytest.raises(ValueError, match="not found in portfolio"):
            single_position_tracker.get_position_summary("AAPL")

    def test_remove_nonexistent_ticker_returns_false(
        self, empty_tracker: PortfolioTracker
    ) -> None:
        result = empty_tracker.remove_position("FAKE")
        assert result is False

    def test_remove_position_case_insensitive(
        self, single_position_tracker: PortfolioTracker
    ) -> None:
        result = single_position_tracker.remove_position("aapl")
        assert result is True
        assert single_position_tracker.get_portfolio_value() == 0.0


# ---------------------------------------------------------------------------
# update_price
# ---------------------------------------------------------------------------


class TestUpdatePrice:
    def test_update_price_changes_current_price(
        self, single_position_tracker: PortfolioTracker
    ) -> None:
        single_position_tracker.update_price("AAPL", current_price=200.0)
        summary = single_position_tracker.get_position_summary("AAPL")
        assert summary["current_price"] == 200.0

    def test_update_price_zero_allowed(
        self, single_position_tracker: PortfolioTracker
    ) -> None:
        single_position_tracker.update_price("AAPL", current_price=0.0)
        summary = single_position_tracker.get_position_summary("AAPL")
        assert summary["current_price"] == 0.0

    def test_update_price_unknown_ticker_raises(
        self, empty_tracker: PortfolioTracker
    ) -> None:
        with pytest.raises(ValueError, match="not found in portfolio"):
            empty_tracker.update_price("NOPE", current_price=100.0)

    def test_update_price_negative_raises(
        self, single_position_tracker: PortfolioTracker
    ) -> None:
        with pytest.raises(ValueError, match="current_price must be non-negative"):
            single_position_tracker.update_price("AAPL", current_price=-10.0)

    def test_update_price_case_insensitive(
        self, single_position_tracker: PortfolioTracker
    ) -> None:
        single_position_tracker.update_price("aapl", current_price=250.0)
        summary = single_position_tracker.get_position_summary("AAPL")
        assert summary["current_price"] == 250.0


# ---------------------------------------------------------------------------
# get_portfolio_value
# ---------------------------------------------------------------------------


class TestGetPortfolioValue:
    def test_empty_portfolio_returns_zero(
        self, empty_tracker: PortfolioTracker
    ) -> None:
        assert empty_tracker.get_portfolio_value() == 0.0

    def test_single_position_value(
        self, single_position_tracker: PortfolioTracker
    ) -> None:
        # 100 shares × $180 = $18,000
        assert single_position_tracker.get_portfolio_value() == pytest.approx(18_000.0)

    def test_multi_position_value(
        self, multi_position_tracker: PortfolioTracker
    ) -> None:
        # AAPL: 100×180=18000, MSFT: 50×280=14000, TSLA: 20×200=4000 → 36000
        assert multi_position_tracker.get_portfolio_value() == pytest.approx(36_000.0)

    def test_value_reflects_price_update(
        self, single_position_tracker: PortfolioTracker
    ) -> None:
        single_position_tracker.update_price("AAPL", current_price=200.0)
        assert single_position_tracker.get_portfolio_value() == pytest.approx(20_000.0)

    def test_value_after_remove(self, multi_position_tracker: PortfolioTracker) -> None:
        multi_position_tracker.remove_position("AAPL")
        # MSFT: 14000 + TSLA: 4000 = 18000
        assert multi_position_tracker.get_portfolio_value() == pytest.approx(18_000.0)


# ---------------------------------------------------------------------------
# get_profit_loss
# ---------------------------------------------------------------------------


class TestGetProfitLoss:
    def test_empty_portfolio_returns_zero(
        self, empty_tracker: PortfolioTracker
    ) -> None:
        assert empty_tracker.get_profit_loss() == 0.0

    def test_gain_position(self, single_position_tracker: PortfolioTracker) -> None:
        # cost=100×150=15000, value=100×180=18000 → P&L=+3000
        assert single_position_tracker.get_profit_loss() == pytest.approx(3_000.0)

    def test_loss_position(self, empty_tracker: PortfolioTracker) -> None:
        empty_tracker.add_position("MSFT", shares=50.0, avg_cost=300.0)
        empty_tracker.update_price("MSFT", current_price=280.0)
        # cost=50×300=15000, value=50×280=14000 → P&L=−1000
        assert empty_tracker.get_profit_loss() == pytest.approx(-1_000.0)

    def test_breakeven_position(self, empty_tracker: PortfolioTracker) -> None:
        empty_tracker.add_position("TSLA", shares=20.0, avg_cost=200.0)
        # No price update → current_price == avg_cost → P&L=0
        assert empty_tracker.get_profit_loss() == pytest.approx(0.0)

    def test_multi_position_net_pl(
        self, multi_position_tracker: PortfolioTracker
    ) -> None:
        # AAPL +3000, MSFT −1000, TSLA 0 → net +2000
        assert multi_position_tracker.get_profit_loss() == pytest.approx(2_000.0)


# ---------------------------------------------------------------------------
# get_percentage_return
# ---------------------------------------------------------------------------


class TestGetPercentageReturn:
    def test_empty_portfolio_raises(self, empty_tracker: PortfolioTracker) -> None:
        with pytest.raises(ValueError, match="total cost basis is zero"):
            empty_tracker.get_percentage_return()

    def test_positive_return(self, single_position_tracker: PortfolioTracker) -> None:
        # P&L=3000, cost=15000 → 20%
        assert single_position_tracker.get_percentage_return() == pytest.approx(20.0)

    def test_negative_return(self, empty_tracker: PortfolioTracker) -> None:
        empty_tracker.add_position("MSFT", shares=50.0, avg_cost=300.0)
        empty_tracker.update_price("MSFT", current_price=280.0)
        # P&L=−1000, cost=15000 → −6.666...%
        expected = (-1_000.0 / 15_000.0) * 100.0
        assert empty_tracker.get_percentage_return() == pytest.approx(expected)

    def test_breakeven_return_is_zero(self, empty_tracker: PortfolioTracker) -> None:
        empty_tracker.add_position("TSLA", shares=20.0, avg_cost=200.0)
        assert empty_tracker.get_percentage_return() == pytest.approx(0.0)

    def test_multi_position_percentage_return(
        self, multi_position_tracker: PortfolioTracker
    ) -> None:
        # cost: AAPL=15000, MSFT=15000, TSLA=4000 → total=34000
        # P&L: +3000−1000+0 = +2000
        # → (2000/34000)*100 ≈ 5.882%
        total_cost = 100 * 150 + 50 * 300 + 20 * 200  # 34000
        expected = (2_000.0 / total_cost) * 100.0
        assert multi_position_tracker.get_percentage_return() == pytest.approx(expected)

    def test_zero_cost_basis_single_position_raises(
        self, empty_tracker: PortfolioTracker
    ) -> None:
        empty_tracker.add_position("FREE", shares=10.0, avg_cost=0.0)
        with pytest.raises(ValueError, match="total cost basis is zero"):
            empty_tracker.get_percentage_return()


# ---------------------------------------------------------------------------
# get_position_summary
# ---------------------------------------------------------------------------


class TestGetPositionSummary:
    def test_summary_contains_all_keys(
        self, single_position_tracker: PortfolioTracker
    ) -> None:
        summary = single_position_tracker.get_position_summary("AAPL")
        expected_keys = {
            "shares",
            "avg_cost",
            "current_price",
            "market_value",
            "cost_basis",
            "profit_loss",
            "percentage_return",
        }
        assert set(summary.keys()) == expected_keys

    def test_summary_values_correct(
        self, single_position_tracker: PortfolioTracker
    ) -> None:
        summary = single_position_tracker.get_position_summary("AAPL")
        assert summary["shares"] == pytest.approx(100.0)
        assert summary["avg_cost"] == pytest.approx(150.0)
        assert summary["current_price"] == pytest.approx(180.0)
        assert summary["market_value"] == pytest.approx(18_000.0)
        assert summary["cost_basis"] == pytest.approx(15_000.0)
        assert summary["profit_loss"] == pytest.approx(3_000.0)
        assert summary["percentage_return"] == pytest.approx(20.0)

    def test_summary_unknown_ticker_raises(
        self, empty_tracker: PortfolioTracker
    ) -> None:
        with pytest.raises(ValueError, match="not found in portfolio"):
            empty_tracker.get_position_summary("FAKE")

    def test_summary_case_insensitive(
        self, single_position_tracker: PortfolioTracker
    ) -> None:
        summary = single_position_tracker.get_position_summary("aapl")
        assert summary["shares"] == pytest.approx(100.0)


# ---------------------------------------------------------------------------
# get_all_positions
# ---------------------------------------------------------------------------


class TestGetAllPositions:
    def test_empty_portfolio_returns_empty_list(
        self, empty_tracker: PortfolioTracker
    ) -> None:
        assert empty_tracker.get_all_positions() == []

    def test_single_position_list_length(
        self, single_position_tracker: PortfolioTracker
    ) -> None:
        positions = single_position_tracker.get_all_positions()
        assert len(positions) == 1

    def test_multi_position_list_length(
        self, multi_position_tracker: PortfolioTracker
    ) -> None:
        positions = multi_position_tracker.get_all_positions()
        assert len(positions) == 3

    def test_all_positions_contain_ticker_key(
        self, multi_position_tracker: PortfolioTracker
    ) -> None:
        tickers = {p["ticker"] for p in multi_position_tracker.get_all_positions()}
        assert tickers == {"AAPL", "MSFT", "TSLA"}

    def test_all_positions_values_match_individual_summaries(
        self, multi_position_tracker: PortfolioTracker
    ) -> None:
        all_pos = {p["ticker"]: p for p in multi_position_tracker.get_all_positions()}
        for ticker in ("AAPL", "MSFT", "TSLA"):
            summary = multi_position_tracker.get_position_summary(ticker)
            for key, val in summary.items():
                assert all_pos[ticker][key] == pytest.approx(
                    val
                ), f"Mismatch for {ticker}.{key}"

    def test_all_positions_after_removal(
        self, multi_position_tracker: PortfolioTracker
    ) -> None:
        multi_position_tracker.remove_position("MSFT")
        tickers = {p["ticker"] for p in multi_position_tracker.get_all_positions()}
        assert tickers == {"AAPL", "TSLA"}
        assert "MSFT" not in tickers
