# ANET Rolling Strategy Runbook

## Goal

Rebuild the ANET rolling one-year long-only strategy analysis from scratch, update it after each market close, and identify whether the active buy/sell rule should be kept or changed.

The user believes market pressures older than one year may no longer apply, so the model must operate on a rolling one-year window only.

## Data Requirements

Required source data columns:

- `Date`
- `Close/Last`
- `Volume`
- `Open`
- `High`
- `Low`

Preferred source workbook:

`HistoricalData_Full_ANET.xlsx`

Expected row count:

- About 252 trading rows plus a header.
- A row count slightly above or below 252 can be acceptable because of holidays and data source behavior, but the window should represent the latest one-year trading period.

Do not use `HistoricalData_ANET.xlsx` for final strategy work if `HistoricalData_Full_ANET.xlsx` is available, because the smaller file lacks `High`, `Low`, and `Volume`.

## Feature Engineering

For each row sorted oldest to newest:

- Prior close: previous row's `Close/Last`
- Close-to-close return: `Close / prior close - 1`
- Opening gap: `Open / prior close - 1`
- Intraday return: `Close / Open - 1`
- High-low range: `High / Low - 1`
- True range percent: `max(High-Low, abs(High-prior close), abs(Low-prior close)) / prior close`
- Close range position: `(Close - Low) / (High - Low)`
- 20-day annualized volatility from close-to-close returns
- 20-day ATR percent from true range percent
- Volume versus prior 20-day average volume
- 10-day and 20-day simple moving averages
- Distance from 20-day high and low

Avoid using same-day close or full-day volume as entry filters for a trade entered at the open. They can be diagnostics, not open-time signal inputs.

## Candidate Buy Rules

All buy rules are long-only. Common families:

1. Positive opening gap bands:
   - `+0.5% to +3.0%`
   - `+0.5% to +3.5%`
   - `+1.0% to +3.0%`
   - `+1.5% to +3.5%`

2. Positive gap with prior trend:
   - gap band plus prior close above prior SMA10.

3. Positive gap with prior volume:
   - gap band plus prior day's volume/20-day average volume threshold.

4. Pullback in prior trend:
   - negative opening gap while prior close is above SMA10.
   - Treat as experimental; prior testing showed weak results.

5. Open near breakout:
   - open near or above prior 10/20/50-day high, with max gap cap.
   - Treat low-trade breakout winners as fragile unless enough trades exist.

6. Prior momentum plus controlled gap:
   - prior 3/5/10/20-day momentum above a threshold and current gap in a positive band.

7. Low-volatility gap-up:
   - positive gap band plus prior ATR20 below a threshold.

## Candidate Sell Rules

Test each buy rule against multiple sell rules:

1. Same-day close:
   - Sell at entry day's close.

2. Next-day close:
   - Hold through entry day and sell at the next trading day's close.
   - Prior broad sweep winner used this sell rule.

3. Profit target / stop / time stop:
   - `+5% target / -3% stop / 5-trading-day max`
   - `+7% target / -4% stop / 8-trading-day max`
   - `+10% target / -5% stop / 10-trading-day max`

4. Trailing stop:
   - Example: 6% trailing stop with 10-trading-day max hold.

5. Trend break:
   - Exit when close drops below SMA10, with 10-trading-day max hold and protective stop.

## Prior Strategy Findings

Initial workbook:

- `HistoricalData_Full_ANET.xlsx`
- Window: `2025-07-07 to 2026-07-07`
- Latest workbook close at the time: `$166.46`

Prior best broad-sweep rule:

- Buy: open gap between `+0.5%` and `+3.0%`.
- Sell: next trading day's close.
- Return: about `+98.6%`.
- Max drawdown: about `-11.8%`.
- Trades: `65`.
- Win rate: about `63.1%`.
- Profit factor: about `2.11`.

Prior refined stop/target rule:

- Buy: open gap between `+1.5%` and `+3.5%`.
- Sell: first of `+10% target`, `-5% stop`, or close after 10 trading days.
- Return: about `+70.2%`.
- Max drawdown: about `-9.9%`.
- Trades: `22`.

Do not assume these remain valid after new data is added. Use them as baselines.

## Daily Evaluation Logic

After market close:

1. Update the data workbook with the latest OHLCV bar.
2. Remove the oldest row if needed to preserve the one-year window.
3. Re-run the strategy matrix and buy-rule sweep.
4. Compare:
   - active strategy,
   - best strategy by total return,
   - best strategy subject to drawdown and trade-count guardrails,
   - nearby variants of the best strategy.
5. Recommend:
   - keep current strategy,
   - switch strategy,
   - pause/no-trade,
   - collect more data or add constraints.

## Switching Rules

Do not switch strategy daily just because the top ranking changes.

Recommend switching only when:

- The new strategy has at least 30 trades, unless the user accepts a sparse strategy.
- Max drawdown is acceptable.
- Profit factor remains above 1.5.
- The improvement is meaningful, preferably at least several percentage points of return or materially lower drawdown.
- The rule is simple and understandable.
- Neighboring parameter variants also perform well.

Recommend keeping the active strategy when:

- The current rule remains competitive.
- The new winner is a narrow parameter artifact.
- The new winner has low trade count.
- The new winner requires assumptions that cannot be trusted with daily bars.

## Tomorrow Decision Checklist

Before the next session:

1. Verify prior official close.
2. For the active opening-gap buy rule, calculate:
   - lower open trigger,
   - upper open limit.
3. Define the sell rule before entry.
4. State whether stops apply.
5. State whether intraday movement into the buy zone counts. For the leading rule, it does not; only the opening price matters.
6. Check for earnings, major company news, or market-moving events. Override or pause the model if news risk is unusually high.

## Example Target Calculation

If prior close is `$166.46` and active buy rule is `+0.5% to +3.0%`:

```text
lower trigger = 166.46 * 1.005 = 167.29
upper limit   = 166.46 * 1.030 = 171.45
```

Interpretation:

- Open below `$167.29`: no trade.
- Open from `$167.29` to `$171.45`: buy signal active.
- Open above `$171.45`: no trade.

## Output Workbook Expectations

The generated workbook should include:

- `Decision`: user-facing summary and current recommendation.
- `Strategy Matrix`: focused strategy combinations.
- `Buy Rule Sweep`: broader sweep of buy rules and sell rules.
- `Top Trade Log`: every trade behind the top strategy.
- `Strategy Tests`: baseline long-only candidates.
- `Gap Behavior`: diagnostics by gap bucket.
- `One-Year Signals`: row-level data and indicators.
- `Equity Curves`: strategy growth curves.

If the output workbook cannot be overwritten because Excel has it open, save a new file with a suffix such as `_With_Buy_Sweep` or a timestamp.

## Known Pitfalls

- Do not accidentally use same-day volume for an open-time buy rule.
- Do not convert a gap-down continuation rule into a short strategy.
- Do not treat intraday movement into the buy zone as valid unless specifically tested.
- Do not treat the highest-return rule as robust if it has too few trades.
- Do not ignore transaction costs.
- Do not hide the daily-bar stop/target ordering assumption.
- Do not use stale web quotes without saying so.
