# Forex Imbalance & Return Zone Backtester

A lightweight Python backtesting algorithm designed to detect institutional price imbalances and analyze statistical return probabilities. The script processes historical Forex market data (H4 timeframe) to evaluate premium/discount zone mitigations based on algorithmic Smart Money Concepts (SMC).

## Algorithm Logic

1. **Impulse Detection:** Scans the historical data layer to discover expansion candles where the body size exceeds the defined threshold (`min_impulse_points = 600`).
2. **Equilibrium Mapping:** Dynamically calculates the 50% median of the impulse candle to mark the core imbalance/fair value gap zone.
3. **Consolidation Filter:** Implements a time-horizon lock requiring a minimum accumulation phase (`min_wait_days = 14`) before a return can be validated.
4. **Metric Logging:** Measures maximum adverse deviations (above/below the zone), tracks internal fake breakouts, and registers the exact timestamp of the structural mitigation.

## Features

* Automated local CSV file resolution loop.
* Quantitative risk metrics generation (90% and 95% deviation percentiles for statistical Stop Loss optimization).
* Automatic dataset serialization to a semicolon-separated tabular format (`Imbalance_Return_Statistics.csv`).

## Requirements

Ensure Python 3.10+ and the required dependency are installed:

```bash
pip install -r requirements.txt
```

## Usage

Place your historical H4 ASCII export file (e.g., `USDCHF.fx240.csv`) in the root directory and execute the scanner:

```bash
python backtester.py
```
