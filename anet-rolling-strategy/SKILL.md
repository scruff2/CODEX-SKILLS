---
name: anet-rolling-strategy
description: Rebuild, evaluate, and explain a rolling one-year long-only ANET trading strategy from OHLCV Excel data. Use when the user asks to analyze ANET historical data, update the daily rolling one-year strategy, calculate tomorrow buy targets, compare buy/sell rules, regenerate the ANET strategy workbook, or recover the ANET trading-analysis workflow in a new session.
---

# ANET Rolling Strategy

## Purpose

Use this skill to continue or restart the ANET trading-strategy workflow from scratch. The user wants a **long-only** strategy for ANET that is re-evaluated after each market close using only the most recent rolling one-year OHLCV window.

Always treat this as a decision-support analysis, not financial advice. Be explicit about assumptions, stale data, sample-size risk, and any limitations from daily OHLCV bars.

Before implementing or changing strategy logic, read:

- `references/strategy-runbook.md`

## Core Constraints

- Use only the rolling one-year data window. Do not import older ANET price history unless the user explicitly changes this constraint.
- Use long-only actions: buy ANET, hold ANET, sell/exit ANET, or stay in cash.
- Do not use shorting, inverse exposure, or options unless the user explicitly changes the scope.
- Prefer simple, auditable rules over complex optimized models.
- Re-evaluate daily after market close, but do not recommend changing the active strategy unless the new rule is meaningfully better and robust.
- For current or latest market data, browse or otherwise verify current prices because quote, close, and news data are time-sensitive.

## Expected Project Files

The ANET project usually lives at:

`C:\Users\mark\Documents\Stock Market\ANET`

Common files:

- `HistoricalData_Full_ANET.xlsx`: source one-year OHLCV workbook.
- `tools/analyze_anet_strategy.py`: main analysis and strategy-grid script.
- `tools/build_anet_strategy_workbook.py`: creates the Excel review workbook.
- `tools/sweep_anet_buy_rules.py`: broader buy-rule sweep.
- `outputs/anet_strategy_lab/ANET_One_Year_Strategy_Lab.xlsx`: baseline output workbook.
- `outputs/anet_strategy_lab/ANET_One_Year_Strategy_Lab_With_Buy_Sweep.xlsx`: output workbook with broader buy-rule sweep.
- `outputs/anet_strategy_lab/anet_strategy_analysis.json`: strategy-lab JSON output.
- `outputs/anet_strategy_lab/anet_buy_rule_sweep.json`: broad buy-rule sweep output.

If files are missing, recreate them using the runbook. If the workbook is open in Excel and cannot be overwritten, save a timestamped or suffixed output workbook instead of asking the user to close Excel.

## Current Known Leading Strategy

As of the prior analysis, the best broad-sweep long-only strategy was:

- **Buy rule**: Buy ANET at the open when the opening gap is between **+0.5% and +3.0%** versus the prior close.
- **Sell rule**: Sell at the **next trading day close**.
- **No stop-loss, no profit target, no trailing stop** in this specific top-tested rule.

Prior backtest on the one-year workbook:

- Return: approximately **+98.6%**
- Max drawdown: approximately **-11.8%**
- Trades: **65**
- Win rate: approximately **63.1%**
- Profit factor: approximately **2.11**
- Average hold: **2 trading days**

Also tested:

- Buy +1.5% to +3.5% gap-up, sell at same-day close: lower return, lower hold time.
- Buy +1.5% to +3.5% gap-up, sell at +10% target / -5% stop / 10-day time stop: about +70.2% in the prior test.
- Buy +0.5% to +3.0% gap-up, sell at +10% target / -5% stop / 10-day time stop: about +94.7% in the prior broad sweep.

Do not assume these remain current. Re-run the rolling-window analysis after new data is added.

## Daily Workflow

1. Confirm the latest available official ANET close and whether the local workbook includes it.
2. Update `HistoricalData_Full_ANET.xlsx` with the newest OHLCV row if needed.
3. Keep only the most recent rolling one-year trading window, normally about 252 trading days.
4. Run:

```powershell
python tools/analyze_anet_strategy.py
python tools/sweep_anet_buy_rules.py
python tools/build_anet_strategy_workbook.py
```

5. Verify the output workbook opens and includes these tabs:
   - `Decision`
   - `Strategy Matrix`
   - `Buy Rule Sweep`
   - `Top Trade Log`
   - `Strategy Tests`
   - `Gap Behavior`
   - `One-Year Signals`
   - `Equity Curves`
6. Compare the previous active strategy with the new rolling-window winner.
7. Recommend one of:
   - keep current strategy,
   - switch strategy,
   - pause/no-trade regime,
   - collect more data or add constraints.

## Tomorrow Buy Target Calculation

For the leading strategy, calculate tomorrow's buy zone from the prior official close:

```text
lower buy trigger = prior close * 1.005
upper buy limit   = prior close * 1.030
```

Only the **opening price** matters for this rule.

- If ANET opens below the lower trigger: no trade.
- If ANET opens inside the zone: buy signal is active.
- If ANET opens above the upper limit: no trade.
- If ANET opens outside the zone and later moves into the zone intraday: no trade under this tested rule.

If the user asks for actual target prices, verify or clearly state the prior close being used.

## Robustness Guardrails

When comparing daily strategy candidates, avoid switching just because a new rule is slightly better. Prefer switching only when the new strategy has:

- Minimum trade count: generally **30+ trades** in the one-year window.
- Max drawdown acceptable to the user, commonly under **15%** unless explicitly changed.
- Profit factor above **1.5**.
- Meaningful return improvement over the active rule, not a tiny marginal difference.
- Simple, explainable buy and sell rules.
- Stable nearby parameter variants. For example, +0.5% to +3.0% and +0.5% to +3.5% producing similar results is more credible than a narrow isolated optimum.

If the best rule has very few trades, label it as fragile even if return is high.

## OHLCV Backtest Assumptions

Daily OHLCV bars cannot show intraday event order. For stop/target rules:

- If both stop and target are touched in the same daily bar, assume the stop happened first.
- State this conservative assumption in summaries.
- Prefer next-close or time-close exits when the user wants fewer intraday ordering assumptions.

Account for transaction costs. The prior scripts used **10 bps per trade**.

## Response Style

For user-facing trading-strategy answers:

- Give the concrete rule first.
- Include the exact prices when asked for targets.
- State the data date and prior close used.
- State whether the action is buy, sell/exit, hold, or no trade.
- Keep caveats short but explicit.
- Do not imply certainty or guarantee.

Example:

```text
Using the $166.46 prior close, the buy zone is $167.29 to $171.45.
This is an opening-gap rule: if ANET opens outside that range, the strategy says no trade.
```

## When Updating Code

Use the repo's existing scripts if present. Prefer patching those scripts over rewriting from scratch:

- `tools/analyze_anet_strategy.py`
- `tools/sweep_anet_buy_rules.py`
- `tools/build_anet_strategy_workbook.py`

After edits, run:

```powershell
python -m py_compile tools/analyze_anet_strategy.py tools/sweep_anet_buy_rules.py tools/build_anet_strategy_workbook.py
python tools/analyze_anet_strategy.py
python tools/sweep_anet_buy_rules.py
python tools/build_anet_strategy_workbook.py
```

If Python modules are missing, install only what is needed. The scripts have used `openpyxl` and standard-library modules.
