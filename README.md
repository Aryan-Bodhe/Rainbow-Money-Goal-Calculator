# Rainbow Money Goal Calculator

**Rainbow Money Goal Calculator** is a goal-based SIP (Systematic Investment Plan) simulation toolbox. It helps investors determine the monthly SIP required (in addition to any lump-sum) to reach a financial goal within a specified time horizon and risk profile.

---

## 🧩 Key Features

* **Multi-Asset Allocation**: Distributes investments across asset classes (Large Cap, S\&P 500, Gold) based on user-selected risk profile (`conservative`, `balanced`, `aggressive`).
* **Goal-Based SIP Computation**: Calculates per-asset SIP using the annuity-due future-value formula.
* **XIRR Analysis**: Computes annualized return (XIRR) for each asset and the overall portfolio.
* **Monte Carlo Simulation**: Simulates correlated monthly returns via Cholesky decomposition on historical NAV data.
* **Probability Estimation**: Estimates the probability of achieving the goal given return volatility.
* **SIP Suggestion**: Uses binary search over simulations to find the SIP amount required to hit a user-defined success probability (default 90%).
* **FastAPI Backend**: Exposes a `/calculate-goal` POST endpoint returning a structured JSON response with SIP details, XIRR, growth estimates, and goal probability.
* **Modular Design**: Clear separation of concerns across `core`, `models`, and `utils` packages.

---

## 🚀 Installation

1. **Clone the repository**

   ```bash
   git clone https://github.com/Aryan-Bodhe/Rainbow-Money-Goal-Calculator.git
   cd Rainbow-Money-Goal-Calculator
   ```

2. **Create & activate a virtual environment** (optional but recommended)

   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Install dependencies**

   ```bash
   pip install -r requirements.txt
   ```

4. **Prepare NAV & Forex Data**

   * Place monthly NAV data (`.feather` files) under `data/newfinal/monthly_nav/`.
   * Forex rates (if needed) under `data/newfinal/monthly_forex/`.
   * **Data Usage & Guidelines**: Refer to [`data/data_guidelines.md`](data/data_guidelines.md) for instructions on downloading, formatting, and updating data files.

5. **Configure**

   * Edit `config.py` to adjust simulations (`NUM_SIMULATIONS`), target probability (`TARGET_PROB_OF_SUCCESS`), logging settings, and portfolio weights.

---

## 📂 Project Structure

```plaintext
Rainbow-Money-Goal-Calculator/
├── assets/                  # Static assets (e.g., logos, diagrams)
├── core/                    # Business logic pipeline
│   ├── goal_engine.py       # Orchestrates analysis workflow
│   ├── asset.py             # Asset class & XIRR logic
│   ├── portfolio.py         # Portfolio class: build, simulate & metrics
│   ├── sip_goal_based.py    # Computes asset weights & SIP plan
│   ├── sip_plotter.py       # (Optional) Generates return histograms
│   └── exceptions.py        # Custom domain exceptions
├── data/                    # Input data (NAV & Forex rates)
│   └── data_guidelines.md   # Guidelines for data sourcing & formatting
├── logs/                    # Generated logs (daily rotating)
├── models/                  # Pydantic schemas for API
│   ├── goal_request.py      # Input request schema
│   ├── asset.py             # Asset summary schema
│   └── portfolio.py         # Portfolio summary schema
├── utils/                   # Shared utilities
│   └── logger.py            # Colored console + timed file logging
├── config.py                # Simulation parameters & file paths
├── main.py                  # FastAPI entrypoint (`/calculate-goal` endpoint)
├── requirements.txt         # Python dependencies
└── README.md                # Project overview & setup instructions
```

---

## ⚙️ Usage

1. **Run the API server**

   ```bash
   uvicorn main:app --reload
   ```

2. **Open the interactive docs**
   Navigate to `http://127.0.0.1:8000/docs` in your browser.

3. **Call the `/calculate-goal` endpoint**

   ```bash
   curl -X POST "http://127.0.0.1:8000/calculate-goal" \
     -H "Content-Type: application/json" \
     -d '{
       "goal_amount": 1000000,
       "time_horizon": 5,
       "lumpsum_amount": 200000,
       "risk_profile": "balanced"
     }'
   ```

4. **Response**

   ```json
   {
     "goal_amount": 1000000,
     "time_horizon": 5,
     "lumpsum_amount": 200000,
     "total_monthly_sip": 10000.50,
     "risk_profile": "balanced",
     "portfolio_growth": 1.345,
     "asset_summaries": [
       {"name": "largecap", "weight": 0.3, "expected_return": 0.07, "sip_amount": 3000.15, "xirr": 0.075},
       ...
     ],
     "rolling_xirr": 0.068,
     "goal_achievement_probability": 0.92,
     "suggested_sip": 9500.00
   }
   ```

---

## 🛠️ Configuration & Logging

* **`config.py`**: Adjust defaults for simulations, risk profiles & file paths.
* **Logging**: Uses `utils/logger.py` for console output (colored) and daily rotating logs under `logs/` (retains 10 days by default).

---

## 🤝 Contributing

1. Fork the repo
2. Create a feature branch (`git checkout -b feature/XYZ`)
3. Commit your changes (`git commit -m 'Add XYZ'`)
4. Push to branch (`git push origin feature/XYZ`)
5. Open a Pull Request

Please follow the existing code style and include tests for new functionality.

---

*Happy Investing!*
