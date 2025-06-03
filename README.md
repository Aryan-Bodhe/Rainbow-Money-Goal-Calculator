# SIP Goal-Based Portfolio Simulator

An advanced data-analytics based toolkit for planning systematic investment plans (SIPs) toward financial goals.
It supports:

* **Lump-sum + SIP planning** across multiple assets
* **Annuity-due** cashflow modeling & XIRR calculations
* **Monte Carlo simulation** of multi-asset portfolios using historical NAV returns
* **Custom exception handling** for clear error reporting

Use this to estimate the monthly SIP required (or validate that a lump-sum alone suffices), analyze probabilities of reaching your target given return volatility, and compare different risk-profile allocations.

---

## Table of Contents

1. [Features](#features)
2. [Installation](#installation)
3. [Project Structure](#project-structure)
4. [Configuration & Assumptions](#configuration--assumptions)
5. [Error Handling](#error-handling)
6. [Testing](#testing)
7. [Dependencies](#dependencies)

---

## Features

* **Multi-asset Weighted Allocations**
  Allocate both lump-sum and monthly SIP across assets (Smallcap, Midcap, Largecap, Debt, Gold) according to user-defined weights.

* **Annuity-Due SIP Calculations**
  Compute exact per-asset monthly SIP amounts using the annuity-due future-value formula:

  $$
    P_{\text{asset}} 
    = \frac{\bigl(\text{Goal} - \text{Lumpsum} \times (1+r)^{N}\bigr)}{\frac{(1+r)^{N} - 1}{r}} \times \text{weight}
  $$

  where $r$ is monthly rate, $N$ is the number of months.

* **XIRR Computation**
  Build forward-looking cashflow dictionaries (lump-sum at $t_0$, SIPs each month, redemption at $t_{N+1}$) and compute the annualized internal rate of return (XIRR) using [pyxirr](https://github.com/sanketplus/py-xirr).

* **Monte Carlo Simulation**

  * Compute historical monthly log-returns and covariance from aligned NAV data for all assets.
  * Simulate correlated monthly returns via Cholesky decomposition.
  * Inject both lumpsum + first SIP at Month 1 (annuity-due), then monthly SIPs for $N$ months.
  * Estimate the probability of the final portfolio exceeding the goal.

* **Binary Search for SIP**
  Find the monthly SIP required to achieve a user-specified probability (e.g., 95%) for reaching the goal, given lump-sum and return assumptions.

* **Custom Exceptions**
  Clear, domain-specific error types for invalid inputs (e.g. negative SIP, missing NAV data, invalid cashflows) to speed up debugging.

---

## Installation

1. **Clone the repository**

   ```
   git clone https://github.com/yourusername/sip-goal-simulator.git
   cd sip-goal-simulator
   ```

2. **Create a virtual environment (optional but recommended)**

   ```
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Install dependencies**

   ```
   pip install -r requirements.txt
   ```

   * Key packages: `numpy`, `pandas`, `pyxirr`

4. **Ensure your NAV CSVs or DataFrames are available**
   Each `Asset` expects a DataFrame (or CSV) with two columns: `Date` (YYYY-MM-DD) and `NAV` (float).

---

## Project Structure

```
sip-goal-simulator/
├── main.py                    # Example entry-point to run portfolio simulations
├── requirements.txt           # pip dependencies
├── README.md                  # This file
├── temp/                      # Temporary files directory
|   └── returns_histogram.py   # Simulated portfolio performance
├── source/  
    ├── exceptions.py          # Custom exception classes
    ├── asset.py               # Asset class & XIRR logic
    ├── portfolio.py           # Portfolio class, SIP + simulation methods
    ├── simulation.py          # Monte Carlo simulation routines (if separated)
    ├── return_forecaster.py   # (Optional) Historical return analysis
    ├── sip_plotter.py         # Plots the portfolio performance
    └── sip_goal_based.py      # Contains asset allocation configs

```

* **`asset.py`**
  Defines `Asset` with attributes: `name`, `weight`, `nav_df`, and method `compute_asset_xirr(lumpsum, start_date, total_months)` which constructs cashflows and calls `pyxirr.xirr()`.

* **`portfolio.py`**
  Contains `Portfolio` class:

  * `prepare_composite_nav()`: Align monthly NAVs from all assets into one DataFrame (forward/backward fill
    missing trading days).
  * `probability_of_reaching_goal(monthly_sip, lumpsum, num_simulations)`: Monte Carlo log-return simulation.
  * `suggest_sip_for_probability(target_prob, lumpsum, num_simulations)`: Binary search on SIP.

* **`sip_calculator.py` (or `utils/sip_calculator.py`)**

  * `compute_monthly_sip(goal_amount, lumpsum_amount, asset_weights, time_horizon, avg_return_rate)`
  * `compute_xirr_from_cashflows(cashflow_dict)`

* **`exceptions.py`**
  Custom exception classes to catch domain errors early (e.g., `SipAmountZeroOrNegativeError`, `InvalidCashflowsError`, `TimeHorizonNotIntegerError`, etc.)

---

## Configuration & Assumptions

* **Annuity-Due Timing**: Both the lump-sum and first SIP are invested at the start of Month 1 before any returns. Subsequent SIPs are invested at the start of each month. Redemption occurs after Month N returns, i.e. at the end of Month N.

* **Log-Normal Return Model**:
  We compute historical monthly log-returns from aligned NAV data (forward-fill non-trading days). Assuming returns are stationary, each simulation draws correlated Gaussian shocks transformed by $\exp(\cdot)$.

* **Correlation & Covariance**:
  We use the full covariance matrix of asset log-returns and Cholesky factorization to generate correlated monthly returns across assets.

* **Binary Search Tolerance**:
  We perform 20 iterations to find the SIP that achieves the target probability. This yields a precision of roughly `high - low ≈ goal_amount / 2^20`.

* **Simulation Size**:
  Default is 10 000 Monte Carlo runs. Increase for tighter confidence (e.g. 50 000+ for ±0.3% margin on probability).

---

## Error Handling

This project uses custom exceptions in `source/exceptions.py` to catch invalid inputs early:

* **`SipAmountZeroOrNegativeError`**: Raised if a calculated SIP is $≤ 0$.
* **`LumpsumEnoughToReachGoalError`**: Raised if the lumpsum alone reaches the goal under deterministic avg-return.
* **`InvalidCashflowsError`**: Raised if XIRR cashflows lack a positive or negative sign-change.
* **`InvalidStartDateError`**: Raised if `start_date` is malformed or missing.
* **`XirrComputationFailedError`**: Wraps any errors from `pyxirr.xirr()`.
* **`HistoricalDataNotFoundError`** / **`HistoricalDataTooLowError`**: If NAV history is missing or too short for the chosen time horizon.
* **`TimeHorizonNotIntegerError`** / **`TimeHorizonZeroOrNegativeError`**: For invalid horizon inputs.
* **`InvalidRiskProfileError`**: If the user selects a risk profile that doesn’t match predefined allocations.

---

## Testing
For testing purposes, execute the run_tests(...) module from main.

---

## Dependencies

* [NumPy](https://numpy.org/)
* [pandas](https://pandas.pydata.org/)
* [pyxirr](https://pypi.org/project/pyxirr/)

Install all at once:

```
pip install -r requirements.txt
```
---