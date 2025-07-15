## DATA INGESTION & PREPROCESSING GUIDELINES

### 1. Directory & File Naming Conventions

* **NAV files (per asset)**

  * Location: `data/final/navs/`
  * Filename format: `<asset_name>.feather`

    * `asset_name` should be in “snake\_case”.
    * Example: `smallcap.feather`, `s&p_500.feather`, `gold.feather`.

* **Forex rate files (per foreign currency)**

  * Location: `data/final/forex/` (or whatever `FOREX_RATES_DIR` points to)
  * Filename format: `<CURRENCY>_to_INR.feather`

    * `<CURRENCY>` must be exactly the 3-letter ISO code (uppercase) that your assets use.
    * Example: `USD_to_INR.feather`, `EUR_to_INR.feather`, `JPY_to_INR.feather`.

---

### 2. Required Columns & Data Types

1. **NAV files**

   * Must contain exactly two columns **before processing**:

     * `Date` (dtype: `datetime64[ns]`)
     * `NAV_<CURRENCY>` (dtype: `float64`)

       * If the asset is already INR-denominated, it should be named `NAV_INR`.
       * If the asset is in USD, name it `NAV_USD`, etc.
   * **No extra columns** (e.g. volume, returns, etc.). If present, drop them before saving as Feather.

2. **Forex files**

   * Must contain exactly two columns:

     * `Date` (dtype: `datetime64[ns]`)
     * `<CURRENCY>_to_INR` (dtype: `float64`)

       * Example: `USD_to_INR` holds the day’s exchange rate to convert 1 USD → X INR.
   * **Rows** must cover every `Date` that appears in any NAV file of that currency’s assets (no gaps).

---

### 3. Preprocessing Steps (Before Committing to `data/final/`)

1. **Standardize Dates**

   * Ensure every CSV/Excel import has a `Date` column.
   * Convert to pandas DateTime applying the correct format (`df['Date'] = pd.to_datetime(df['Date'])`).
   * Sort by `Date` ascending (oldest dates at the top).
   * Convert all prices to float after removing any commas.
   * The historical data of all the assets are collected for the time period 01-01-2011 to 31-12-2023.

2. **Filter to Month-End**

   * Our simulations assume one NAV per calendar month.
   * Post filtering the date range should be 31-01-2011 to 31-12-2023.
   * If raw NAV data has daily frequency, reduce it to **month-end** values only. For example:

     ```python
     df = df.set_index('Date').resample('M').last().reset_index()
     ```
   * This guarantees exactly one row per month.

3. **Rename NAV Column**

   * If the CSV column is called e.g. “Closing Price” or "Price”, rename it to the required `NAV_<CURRENCY>` before saving.

     ```python
     df.rename(columns={'Close Price': 'NAV_USD'}, inplace=True)
     ```
   * If the asset is in INR already, rename to `NAV_INR`.

4. **Check for Missing Months**

   * After resampling, run:

     ```python
     dates = pd.date_range(start=df['Date'].min(), end=df['Date'].max(), freq='M')
     missing = dates.difference(df['Date'])
     if not missing.empty:
         raise ValueError(f"Missing NAV data for months: {missing}")
     ```
   * If there are missing months (e.g. no trading data that month), either fill with the previous valid NAV (`ffill`) or explicitly interpolate—but **be consistent** across all assets.

5. **Save as Feather**

   * Once cleaned and reduced to two columns (`Date`, `NAV_<CURRENCY>`), save:

     ```python
     df.to_feather("data/final/navs/<asset_name>.feather")
     ```
   * Commit that Feather file to the repo (don’t commit any temporary CSVs).

6. **Prepare Forex Data**

   * Obtain historical FX rates for each foreign currency → INR.
   * Convert to monthly, “month-end” series (just like NAV).
   * Ensure you have exactly the same `Date` range (and frequency) as your NAV files.

     ```python
     fx_df = fx_df.set_index('Date').resample('M').last().reset_index()
     fx_df.rename(columns={'Rate': 'USD_to_INR'}, inplace=True)
     ```
   * Save as Feather to `data/final/forex/USD_to_INR.feather`.

---

### 4. How the Code Expects Data to Look

1. **Asset.convert_to_inr(...) Flow**

   * When you call `asset.convert_to_inr(feather_path)`, the code will load the Feather, then run `_get_nav_currency()`.

     * If it finds `NAV_INR`, it assumes no conversion is needed.
     * If it finds `NAV_USD` (or any other `NAV_<CURR>`), it will load `<CURR>_to_INR.feather` from `FOREX_RATES_DIR`.
   * Then it checks alignment (`_is_data_aligned()`), which requires that the **two DataFrames share the same `Date` column** in the exact same order and have the same column count.
   * Finally, it multiplies `NAV_<CURR>` × `<CURR>_to_INR` and returns `['Date', 'NAV_INR']`.

2. **Portfolio Alignment**

   * After every asset has been converted to INR, the `Portfolio.prepare_composite_nav()` concatenates all NAV-­INR DataFrames (one per asset) on the `Date` column.
   * It expects each asset’s NAV DataFrame to look like `['Date', 'NAV_INR']`. Any deviation will break `.concat(...).sort_index().ffill().bfill()`.

3. **SIP-Forecaster Expectations**

   * `_compute_rolling_sip_xirrs(df, time_horizon)` expects a DataFrame `df` with:

     * `Date` (ranging from the earliest data point to the latest)
     * exactly one column starting with `NAV_` (e.g. `NAV_INR`).
   * If the column is named anything else, you must either rename it first or adjust the function to detect the correct column.

---

### 5. Example Workflow

Below is an end-to-end example showing how you’d add a “Tokyo Stock Index” (in JPY) to the project:

1. **Obtain Raw JPY NAV CSV** (e.g. from a data vendor) with columns:

   ```bash
    "Date","Price","Open","High","Low","Vol.","Change %"
    "03-06-2025","5,970.37","5,938.56","5,981.35","5,929.00","","0.58%"
    "02-06-2025","5,935.94","5,896.68","5,937.40","5,861.43","","0.41%"
   ...
   ```

2. **Preprocess the raw file**:
   ```python
   import pandas as pd

   data = pd.read_csv("data/raw/tokyo_jpy_nav.csv")

   data.drop(columns=["Open","High","Low","Vol.","Change %"], inplace=True)
   monthly = data.set_index('Date').resample('M').last().reset_index()
   monthly = monthly.rename(columns={'Price': 'NAV_JPY'}, axis=1, inplace=True)

   # Set data types
   monthly['Date'] = pd.to_datetime(monthly['Date'], format='%d-%m-%Y', errors='raise')
   monthly['Price'] = monthly['Price'].str.replace(',', '').astype(float)

   # Filter to date range (Jan 2011 - Dec 2023)
   final = monthly[monthly['Date'].dt.year >= 2011]
   final = final[final['Date'].dt.year <= 2023]

   # Sort in increasing dates
   final = final[::-1]

   final.to_feather("data/final/navs/tokyo_jpy.feather")
   ```

3. **Prepare Forex** (if not already present):
   Example Forex Data file for USD to INR conversion:
   ```bash
   "Date","Price","Open","High","Low","Vol.","Change %"
    "04-06-2025","0.59","0.61","0.62","0.57","","0.19%"
    "03-06-2025","0.60","0.59","0.62","0.58","","0.21%"
   ```

   ```python
   data = pd.read_csv("data/raw/usd_to_inr.csv")

   data.drop(columns=["Open","High","Low","Vol.","Change %"], inplace=True)
   monthly = data.set_index('Date').resample('M').last().reset_index()
   monthly = monthly.rename(columns={'Price': 'NAV_JPY'}, axis=1, inplace=True)

   # Set data types
   monthly['Date'] = pd.to_datetime(monthly['Date'], format='%d-%m-%Y', errors='raise')
   monthly['Price'] = monthly['Price'].str.replace(',', '').astype(float)

   # Filter to date range (Jan 2011 - Dec 2023)
   final = monthly[monthly['Date'].dt.year >= 2011]
   final = final[final['Date'].dt.year <= 2023]

   # Sort in increasing dates
   final = final[::-1]

   final.to_feather("data/final/navs/tokyo_jpy.feather")
   ```

4. **Add Asset in Code**:

    To add the asset, open the config.py file and modify the asset weightages to include the new asset. Ensure all sum to 1.
   ```python
    AGGRESSIVE_PORTFOLIO = {
        "smallcap": 0.15,
        "midcap": 0.25,
        "s&p_500": 0.35,
        "debt": 0.15,
        "gold": 0.10
    }
   ```
5. **Convert & Simulate**:
   When the code runs, `tokyo_jpy.convert_to_inr(...)` will:

   * Load `tokyo_jpy.feather`.
   * Detect `NAV_JPY`.
   * Load `JPY_to_INR.feather`.
   * Check that `tokyo_jpy`’s `Date` column exactly matches `JPY_to_INR`’s `Date`.
   * Multiply to produce a DataFrame `['Date', 'NAV_INR']`.

---

### 6. Recap & Best Practices

* **Always reduce to 1 row per month** (`resample('M').last()`).
* **Two columns only** in each final NAV or FX Feather: `['Date', 'NAV_<CURR>']` or `['Date', '<CURR>_to_INR']`.
* **Exact month-end dates** (`YYYY-MM-30/31`) with no gaps (or explicitly handle gaps via forward-fill before saving).
* **Filename = `<asset_name>.feather`** under `data/final/navs/` for NAV, `<CURRENCY>_to_INR.feather` under `data/final/forex/` for FX.
* **Column names must start with `NAV_` or end with `_to_INR`** so the code’s detection logic can pick them up.
* **Check alignment**: always verify the NAV and FX dataframes share the same `Date` index and same row count before converting.

