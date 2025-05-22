# Goal-Based SIP Calculator & Visualizer

A comprehensive Python application to plan, calculate, and visualize goal-based Systematic Investment Plans (SIPs).  
It allows users to input their investment goals, expected returns, and lumpsum amounts, then calculates the required monthly SIP, effective annualized return (XIRR), and plots the portfolio growth over time.

---

## Features

- **User Input Validation:** Ensures goal amount, time horizon, return rates, and lumpsum inputs are valid and meaningful.
- **Monthly SIP Calculation:** Computes the exact monthly SIP required to reach the investment goal given a lumpsum and expected CAGR.
- **XIRR Calculation:** Uses extended internal rate of return (XIRR) to evaluate the actual annualized return considering cash flows (lumpsum, SIPs, and final redemption).
- **Portfolio Growth Visualization:** Generates detailed, publication-quality stacked bar charts showing invested amounts, returns, and goal achievement timelines.
- **Interactive Console UI:** Color-coded error messages and prompts for a smooth user experience.

---

## Installation

1. Clone the repository:
   ```
   git clone https://github.com/Aryan-Bodhe/Rainbow-Money-Goal-Calculator.git
   cd goal-based-sip
   ```

2. Install dependencies (preferably in a virtual environment):

   ```
   python -m venv env
   pip install -r requirements.txt
   ```

4. Required Python packages:

   * `matplotlib`
   * `pandas`
   * `pyxirr`
   * `colorama`

---

## Usage

Run the SIP analysis tool from the command line:
```
python app.py
```


### Workflow:

1. Enter your **target goal amount** (e.g., `1000000`).
2. Provide the **expected CAGR rate** in percentage (e.g., `12`).
3. Specify the **investment duration** in years (must be an integer, e.g., `10`).
4. Input any **initial lumpsum investment** (can be zero).
5. The tool will calculate and display:

   * Required monthly SIP amount.
   * Total investment and final XIRR.
6. A detailed plot of the portfolio growth will be saved in the `./temp` folder as `returns_histogram.png`.

---

## Code Structure

### `source/SIP_Goal_Based.py`

* Defines the `SipGoalBased` class which stores SIP parameters and manages user input validation and display of SIP data.

### `source/SIP_Calculator.py`

* Contains the `SipCalculator` class for:

  * Calculating monthly SIP required.
  * Computing the effective XIRR for the investment plan.
  * Helper functions for generating date sequences for XIRR calculations.

### `source/SIP_Plotter.py`

* Implements the `SipPlotter` class responsible for simulating portfolio returns and plotting investments vs. returns over time.
* Highlights the goal achievement month in the plot for clear visualization.

### `app.py`

* Orchestrates the SIP analysis workflow:

  * Collects user input.
  * Computes SIP and XIRR.
  * Displays results.
  * Generates and saves the investment growth chart.
* Includes error handling with colored terminal output for invalid inputs.

---

## Example Output
```
----------------------------------------------------
SIP Details:
Target Goal Amount : 1000000.0
Expected CAGR Rate : 12.0%
Investment Duration : 10 years
Lumpsum Amount Invested : 50000.0
XIRR : 12.45%

Monthly SIP amount : 5623.45
Total SIP Amount : 674814.00
Total Investment Amount : 724814.00
----------------------------------------------------
```

A plot named `returns_histogram.png` will be saved in the `temp/` folder showing the invested amount and returns over the 10-year horizon.

---

## Notes

* The lumpsum amount must be less than or equal to the goal amount.
* If the lumpsum alone can meet the goal with expected returns, the program will notify that no SIP is required.
* The investment duration must be a positive integer (years).
* The CAGR must be positive.
* This tool uses the annuity-due formula for SIP calculations, assuming investments at the start of each period.


---

## Contact

For questions, feature requests, or contributions, please open an issue or contact \[[aryanbodhe7705@gmail.com](mailto:aryanbodhe7705@gmail.com)].

---

Thank you for using the Goal-Based SIP Calculator & Visualizer! 🚀
