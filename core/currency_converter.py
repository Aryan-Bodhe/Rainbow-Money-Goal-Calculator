import os
import pandas as pd

from core.exceptions import DatesNotAlignedError
from config import FOREX_RATES_DIR

class CurrencyConverter:
    """
    Handles conversion of NAV prices from foreign currency to INR using historical forex rates.
    """

    def __init__(self):
        # DataFrame for NAV history and corresponding forex rates
        self.original_nav_data: pd.DataFrame = None
        self.forex_rate_data: pd.DataFrame = None

    def _load_forex_data(self, currency: str) -> None:
        """
        Loads a Feather file named <currency>_to_INR.feather from the forex directory.

        :param currency: Foreign currency code (e.g., 'USD').
        :raises FileNotFoundError: If the expected forex file is not found.
        """
        filename = f"{currency.upper()}_to_INR.feather"
        filepath = os.path.join(FOREX_RATES_DIR, filename)

        if not os.path.exists(filepath):
            raise FileNotFoundError(
                f"Forex data file '{filename}' not found in '{FOREX_RATES_DIR}'. "
                "Expected format: '<CURR>_to_INR.feather'."
            )

        # Read the forex rates into a DataFrame
        self.forex_rate_data = pd.read_feather(filepath)

    def _is_data_aligned(self) -> bool:
        """
        Verifies if NAV and forex rate data are aligned.

        Checks:
          - Same number of columns.
          - Identical 'Date' columns in the same order.

        :return: True if aligned; False otherwise.
        """
        if len(self.original_nav_data.columns) != len(self.forex_rate_data.columns):
            return False

        if not self.original_nav_data['Date'].equals(self.forex_rate_data['Date']):
            return False

        return True

    def _load_nav_data(self, feather_path: str) -> None:
        """
        Loads NAV data from the specified Feather file.

        :param feather_path: Path to the Feather file.
        :raises FileNotFoundError: If the file can't be read.
        """
        try:
            df = pd.read_feather(feather_path)
        except Exception:
            raise FileNotFoundError(f"NAV data file '{feather_path}' not found or unreadable.")

        # Store NAV history
        self.original_nav_data = df

    def _get_nav_currency(self) -> str:
        """
        Infers the currency code from the NAV column name.

        :return: Currency code (e.g., 'USD', 'INR').
        :raises ValueError: If no 'NAV_' column is present.
        """
        # Directly check for INR
        if 'NAV_INR' in self.original_nav_data.columns:
            return 'INR'

        # Find first column starting with 'NAV_'
        nav_cols = [col for col in self.original_nav_data.columns if col.startswith('NAV_')]
        if not nav_cols:
            raise ValueError("No column found with prefix 'NAV_'. Cannot determine currency.")

        # Extract currency suffix
        return nav_cols[0].split('_')[-1]

    def convert_to_inr(
        self,
        feather_path: str | None = None,
        nav_data: pd.DataFrame | None = None
    ) -> pd.DataFrame:
        """
        Converts foreign-currency NAV data to INR using historical forex rates.

        :param feather_path: Path to the NAV Feather file (if nav_data not provided).
        :param nav_data: Pre-loaded NAV DataFrame (optional).
        :return: DataFrame with columns ['Date', 'NAV_INR'].
        :raises FileNotFoundError: If neither input is provided or file missing.
        :raises TypeError: If inputs are of incorrect type.
        :raises DatesNotAlignedError: If NAV and forex dates do not match.
        """
        # Accept either a DataFrame or load from file
        if nav_data is not None:
            if not isinstance(nav_data, pd.DataFrame):
                raise TypeError(f"Expected nav_data as pd.DataFrame, got {type(nav_data)}.")
            self.original_nav_data = nav_data
        else:
            if feather_path is None:
                raise FileNotFoundError("Either nav_data or feather_path must be provided.")
            if not isinstance(feather_path, str):
                raise TypeError(f"Expected feather_path as str, got {type(feather_path)}.")
            self._load_nav_data(feather_path)

        # Determine currency and skip conversion if already INR
        currency = self._get_nav_currency()
        if currency == 'INR':
            return self.original_nav_data

        # Load forex rates and verify date alignment
        self._load_forex_data(currency)
        if not self._is_data_aligned():
            raise DatesNotAlignedError()

        # Multiply NAV by corresponding forex rate
        converted_df = self.original_nav_data.copy()
        price_col = f"NAV_{currency}"
        rate_col = f"{currency}_to_INR"
        converted_df[price_col] *= self.forex_rate_data[rate_col]

        # Rename columns to standard output
        converted_df.columns = ['Date', 'NAV_INR']
        return converted_df
