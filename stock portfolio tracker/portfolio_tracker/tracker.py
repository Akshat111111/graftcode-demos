"""
Core portfolio tracking logic exposed as a plain Python class.

Graftcode Gateway introspects the public methods of PortfolioTracker at
startup and makes them remotely callable without any HTTP framework.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class _Position:
    """Internal representation of a single stock holding."""

    ticker: str
    shares: float
    avg_cost: float  # per-share average cost basis
    current_price: float  # per-share latest market price

    @property
    def market_value(self) -> float:
        """Current market value of the position."""
        return self.shares * self.current_price

    @property
    def cost_basis(self) -> float:
        """Total amount originally invested in this position."""
        return self.shares * self.avg_cost

    @property
    def profit_loss(self) -> float:
        """Absolute profit or loss for this position."""
        return self.market_value - self.cost_basis

    @property
    def percentage_return(self) -> float | None:
        """Percentage return for this position, or None if cost basis is zero."""
        if self.cost_basis == 0.0:
            return None
        return (self.profit_loss / self.cost_basis) * 100.0


class PortfolioTracker:
    """
    A plain Python class that tracks a stock portfolio.

    Exposes portfolio valuation, profit/loss calculations, and percentage
    returns without depending on any HTTP framework.  Graftcode Gateway
    (`gg`) wraps this class at runtime and makes every public method
    remotely callable via strongly-typed Grafts.

    State is held at the class level so it persists across the multiple
    instances that Graftcode Gateway creates (one per call).  A single
    shared portfolio is maintained for the lifetime of the process.
    """

    # Class-level shared state — persists across all instances created by gg.
    _positions: dict[str, _Position] = {}

    def __init__(self) -> None:
        # State lives at the class level; nothing to initialise per instance.
        pass

    def reset_portfolio(self) -> None:
        """
        Clear all positions from the portfolio.

        Useful for starting fresh in a live demo without restarting the
        gateway container.
        """
        PortfolioTracker._positions.clear()

    # ------------------------------------------------------------------
    # Write operations
    # ------------------------------------------------------------------

    def add_position(
        self,
        ticker: str,
        shares: float,
        avg_cost: float,
    ) -> None:
        """
        Add a new position or fully replace an existing one.

        If a position for *ticker* already exists it is overwritten.
        The current price is preserved when overwriting; new positions
        start with ``current_price == avg_cost``.

        Args:
            ticker:   Stock symbol (e.g. ``"AAPL"``).  Case-insensitive;
                      stored in upper-case.
            shares:   Number of shares held.  Must be > 0.
            avg_cost: Per-share average purchase price.  Must be >= 0.

        Raises:
            ValueError: If *shares* <= 0 or *avg_cost* < 0.
        """
        if shares <= 0:
            raise ValueError(f"shares must be greater than zero, got {shares!r}.")
        if avg_cost < 0:
            raise ValueError(f"avg_cost must be non-negative, got {avg_cost!r}.")

        ticker = ticker.upper().strip()
        existing = self._positions.get(ticker)
        current_price = existing.current_price if existing else avg_cost

        self._positions[ticker] = _Position(
            ticker=ticker,
            shares=shares,
            avg_cost=avg_cost,
            current_price=current_price,
        )

    def remove_position(self, ticker: str) -> bool:
        """
        Remove a position from the portfolio.

        Args:
            ticker: Stock symbol to remove.  Case-insensitive.

        Returns:
            ``True`` if the position was found and removed, ``False`` if
            the ticker was not in the portfolio.
        """
        ticker = ticker.upper().strip()
        if ticker in self._positions:
            del self._positions[ticker]
            return True
        return False

    def update_price(self, ticker: str, current_price: float) -> None:
        """
        Set the latest market price for a position.

        Args:
            ticker:        Stock symbol.  Case-insensitive.
            current_price: Latest per-share market price.  Must be >= 0.

        Raises:
            ValueError: If *ticker* is not in the portfolio, or if
                        *current_price* < 0.
        """
        if current_price < 0:
            raise ValueError(
                f"current_price must be non-negative, got {current_price!r}."
            )

        ticker = ticker.upper().strip()
        position = self._positions.get(ticker)
        if position is None:
            raise ValueError(
                f"Ticker '{ticker}' not found in portfolio. "
                "Add it with add_position() first."
            )
        position.current_price = current_price

    # ------------------------------------------------------------------
    # Portfolio-level read operations
    # ------------------------------------------------------------------

    def get_portfolio_value(self) -> float:
        """
        Return the total current market value of all positions.

        Returns:
            Sum of ``shares × current_price`` across all positions.
            Returns 0.0 for an empty portfolio.
        """
        return sum(p.market_value for p in self._positions.values())

    def get_profit_loss(self) -> float:
        """
        Return the total unrealised profit or loss across all positions.

        Returns:
            ``portfolio_value - total_cost_basis``.  Positive means gain,
            negative means loss.  Returns 0.0 for an empty portfolio.
        """
        return sum(p.profit_loss for p in self._positions.values())

    def get_percentage_return(self) -> float:
        """
        Return the portfolio-level percentage return.

        Calculated as ``(total_profit_loss / total_cost_basis) × 100``.

        Returns:
            Percentage return as a float (e.g. ``12.5`` means +12.5 %).

        Raises:
            ValueError: If the total cost basis is zero (empty portfolio
                        or all positions have zero avg_cost).
        """
        total_cost = sum(p.cost_basis for p in self._positions.values())
        if total_cost == 0.0:
            raise ValueError(
                "Cannot compute percentage return: total cost basis is zero."
            )
        return (self.get_profit_loss() / total_cost) * 100.0

    # ------------------------------------------------------------------
    # Position-level read operations
    # ------------------------------------------------------------------

    def get_position_summary(self, ticker: str) -> dict[str, float]:
        """
        Return a breakdown for a single position.

        Args:
            ticker: Stock symbol.  Case-insensitive.

        Returns:
            Dictionary with keys:
            ``shares``, ``avg_cost``, ``current_price``,
            ``market_value``, ``cost_basis``, ``profit_loss``,
            ``percentage_return``.

        Raises:
            ValueError: If *ticker* is not in the portfolio.
        """
        ticker = ticker.upper().strip()
        position = self._positions.get(ticker)
        if position is None:
            raise ValueError(f"Ticker '{ticker}' not found in portfolio.")
        return {
            "shares": position.shares,
            "avg_cost": position.avg_cost,
            "current_price": position.current_price,
            "market_value": position.market_value,
            "cost_basis": position.cost_basis,
            "profit_loss": position.profit_loss,
            # None when avg_cost is zero (e.g. inherited/gifted shares)
            "percentage_return": position.percentage_return,  # type: ignore[assignment]
        }

    def get_all_positions(self) -> list[dict[str, float]]:
        """
        Return a snapshot of every position in the portfolio.

        Returns:
            List of position summaries (same keys as
            :meth:`get_position_summary`), plus a ``"ticker"`` key.
            Returns an empty list for an empty portfolio.
        """
        result: list[dict[str, float]] = []
        for ticker, position in self._positions.items():
            summary: dict[str, object] = {
                "ticker": ticker,
                "shares": position.shares,
                "avg_cost": position.avg_cost,
                "current_price": position.current_price,
                "market_value": position.market_value,
                "cost_basis": position.cost_basis,
                "profit_loss": position.profit_loss,
                # None when avg_cost is zero (e.g. inherited/gifted shares)
                "percentage_return": position.percentage_return,
            }
            result.append(summary)
        return result
