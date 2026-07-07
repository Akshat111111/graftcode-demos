"""
Live demo script — run with: python demo.py
Exercises every public method of PortfolioTracker.
No HTTP framework is imported anywhere.
"""

import sys

sys.path.insert(0, ".")

# Ensure UTF-8 output on Windows terminals
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from portfolio_tracker.tracker import PortfolioTracker  # noqa: E402

SEP = "=" * 62


def main() -> None:
    print(SEP)
    print("  Stock Portfolio Tracker — Live Demo")
    print(SEP)

    tracker = PortfolioTracker()

    # ------------------------------------------------------------------
    # 1. Add positions
    # ------------------------------------------------------------------
    print("\n[1] Adding positions...")
    tracker.add_position("AAPL", shares=100, avg_cost=150.00)
    tracker.add_position("MSFT", shares=50, avg_cost=300.00)
    tracker.add_position("TSLA", shares=20, avg_cost=200.00)
    print("    AAPL: 100 shares @ $150.00")
    print("    MSFT:  50 shares @ $300.00")
    print("    TSLA:  20 shares @ $200.00")

    # ------------------------------------------------------------------
    # 2. Supply market prices (caller-provided, no live API)
    # ------------------------------------------------------------------
    print("\n[2] Updating market prices...")
    tracker.update_price("AAPL", current_price=180.00)
    tracker.update_price("MSFT", current_price=280.00)
    tracker.update_price("TSLA", current_price=200.00)  # breakeven
    print("    AAPL: $180.00  (was $150) → +20.00%")
    print("    MSFT: $280.00  (was $300) →  -6.67%")
    print("    TSLA: $200.00  (unchanged)→   0.00%")

    # ------------------------------------------------------------------
    # 3. Portfolio-level metrics
    # ------------------------------------------------------------------
    print("\n[3] Portfolio summary:")
    print(f"    Total value    : ${tracker.get_portfolio_value():>10,.2f}")
    print(f"    Profit / Loss  : ${tracker.get_profit_loss():>+10,.2f}")
    print(f"    % Return       : {tracker.get_percentage_return():>+10.4f}%")

    # ------------------------------------------------------------------
    # 4. Per-position breakdown
    # ------------------------------------------------------------------
    print("\n[4] Position breakdown:")
    for pos in tracker.get_all_positions():
        pct = pos["percentage_return"]
        pct_str = f"{pct:+.2f}%" if pct is not None else "N/A"
        print(
            f"    {pos['ticker']:5s}  "
            f"value=${pos['market_value']:>9,.2f}  "
            f"P&L=${pos['profit_loss']:>+8,.2f}  "
            f"return={pct_str}"
        )

    # ------------------------------------------------------------------
    # 5. Single-position detail
    # ------------------------------------------------------------------
    print("\n[5] AAPL position detail:")
    summary = tracker.get_position_summary("AAPL")
    for key, val in summary.items():
        val_str = f"{val:,.2f}" if isinstance(val, float) else str(val)
        print(f"    {key:<20s}: {val_str}")

    # ------------------------------------------------------------------
    # 6. Remove a position
    # ------------------------------------------------------------------
    print("\n[6] Removing TSLA...")
    removed = tracker.remove_position("TSLA")
    print(f"    Removed: {removed}")
    print(f"    Portfolio value after removal: ${tracker.get_portfolio_value():,.2f}")

    # ------------------------------------------------------------------
    # 7. Error handling
    # ------------------------------------------------------------------
    print("\n[7] Error handling:")

    try:
        tracker.update_price("TSLA", 999.0)  # TSLA was removed
    except ValueError as exc:
        print(f"    update_price(unknown ticker)  → ValueError: {exc}")

    try:
        tracker.add_position("AAPL", shares=-10, avg_cost=100.0)
    except ValueError as exc:
        print(f"    add_position(negative shares) → ValueError: {exc}")

    try:
        tracker.add_position("AAPL", shares=10, avg_cost=-5.0)
    except ValueError as exc:
        print(f"    add_position(negative cost)   → ValueError: {exc}")

    try:
        empty = PortfolioTracker()
        empty.get_percentage_return()
    except ValueError as exc:
        print(f"    get_percentage_return(empty)  → ValueError: {exc}")

    # ------------------------------------------------------------------
    # Done
    # ------------------------------------------------------------------
    print()
    print(SEP)
    print("  All operations completed successfully.")
    print("  No Flask / FastAPI / Django imported — pure Python class.")
    print(SEP)


if __name__ == "__main__":
    main()
