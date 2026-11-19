# Perfkit

Perfkit is a small Python project for reviewing trade data. It reads a CSV
file, checks each trade, calculates performance metrics, and prints a report
in the terminal or as JSON.

The project also includes a short example of a bug in `backtesting==0.6.2`
and a temporary fix for it. Together, the two parts demonstrate both
debugging a library issue and building a practical command-line tool.

## What it does

- Reads trades from CSV and explains why invalid rows are rejected.
- Calculates profit and loss for long and short trades.
- Reports portfolio metrics, an equity curve, and a per-symbol summary.
- Calculates a position size from capital, risk, entry price, and stop price.
- Provides a text report and a JSON version of the same report.
- Reproduces and temporarily fixes the `Position.pl_pct` issue in
  `backtesting==0.6.2`.

## Requirements and installation

Python 3.9 or later is required. From the project folder, install the
dependencies and the project:

```powershell
py -3.11 -m pip install -r requirements.txt
py -3.11 -m pip install -e .
```

If your Python launcher uses a different installed version, replace
`py -3.11` with `py`.

## Create a report

Run the report on the included sample data:

```powershell
py -3.11 -m perfkit report trades.csv
```

Choose JSON output or a different starting balance with:

```powershell
py -3.11 -m perfkit report trades.csv --format json
py -3.11 -m perfkit report trades.csv --capital 500000
```

The project also supports a shorter command:

```powershell
py -3.11 main.py trades.csv
```

## Part A: fixing `Position.pl_pct`

In `backtesting==0.6.2`, `Position.pl_pct` combines the percentage returns of
open trades using share count as the weight. When trades have different entry
prices, share count does not represent how much money was invested in each
trade, so the resulting position return can be misleading.

For example, suppose a position contains:

| Trade | Shares | Entry price | Current price | Cash P&L |
|---|---:|---:|---:|---:|
| A | 10 | 10 | 15 | +50 |
| B | 1 | 100 | 15 | -85 |

Together, the trades have a cash P&L of `-35` and an entry cost of `200`.
The combined return should therefore be `-35 / 200`, or **-17.5%**. The
library's share-weighted calculation instead gives approximately **+37.73%**.

`part_a/bug_reproduction.py` runs this example against the actual library.
`part_a/fix.py` calculates the return using total cash P&L divided by total
entry cost. Its context manager applies the correction temporarily, checks
that the installed library version is supported, and restores the original
property afterward.

Run the example with:

```powershell
py -3.11 -m part_a.bug_reproduction
```

## Part B: trade reports

The report is built in a few steps:

1. `perfkit/cli.py` reads the command and its options.
2. `perfkit/loader.py` validates the CSV and creates a `Trade` for each valid
   row.
3. `perfkit/calculations.py` calculates each trade's gross and net P&L.
4. `perfkit/metrics.py` calculates portfolio statistics and the equity curve.
5. `perfkit/report.py` formats the results as text or JSON.

`perfkit/sizing.py` contains the separate position-sizing calculation.

### Input and calculation details

- CSV headers are trimmed and treated without regard to letter case.
- Dates may use `YYYY-MM-DD` or `DD/MM/YYYY` format; slash-separated dates are
  interpreted as day first.
- Rows with invalid values are rejected with a line number and reason.
- A later row with the same required values as an earlier row is rejected as
  a duplicate.
- Negative fees are allowed as rebates, but non-finite numbers are rejected.
- Weekend exits are credited on the next weekday. Holidays are not accounted
  for.
- A break-even trade is neither a win nor a loss and resets a losing streak.
- Metrics that cannot be calculated are shown as `n/a` in text and `null` in
  JSON. An infinite profit factor is shown as `"inf"` in JSON.

On the included `trades.csv`, the report contains 61 valid trades and 5
rejected rows. The total net P&L is INR 6,182.02, and the win rate is 63.93%.

## Tests

Run the complete test suite from the project folder:

```powershell
py -3.11 -m pytest
```

The tests cover trade calculations, CSV validation, metrics, position sizing,
the command-line interface, and the sample CSV. Two tests are marked as
expected failures because they demonstrate the original library bug before
the temporary fix is applied.
