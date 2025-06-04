import pandas as pd
import numpy as np
import os

from source.Exceptions import DatesNotAlignedError
from config import FOREX_RATES_DIR

class CurrencyConverter:
    def __init__(self):
        self.original_nav_data: pd.DataFrame = None
        self.forex_rate_data: pd.DataFrame = None


    def _load_forex_data(self, currency: str) -> None:
        """
        Loads a Feather file named <currency>_to_inr.feather from the given directory.

        :param currency: The foreign currency code, e.g. "USD".
        :param directory: The path to the directory where the .feather files are stored.
        :return: A pandas DataFrame containing the forex data.
        :raises FileNotFoundError: If the file does not exist in the directory.
        """
        filename = f"{currency.upper()}_to_INR.feather"
        filepath = os.path.join(FOREX_RATES_DIR, filename)

        if not os.path.exists(filepath):
            raise FileNotFoundError(f"Forex data file '{filename}' not found in directory '{FOREX_RATES_DIR}.' Expected file name format : '<CURR>_to_INR.feather'.")

        self.forex_rate_data = pd.read_feather(filepath)

    
    def _is_data_aligned(self) -> bool:
        """
        Checks if the original NAV data and forex rate data are aligned.

        Alignment is defined as:
        - Both dataframes have the same number of columns.
        - The 'Date' columns in both dataframes are identical and in the same order.

        Returns:
            bool: True if dataframes are aligned, False otherwise.
        """
        if len(self.original_nav_data.columns) != len(self.forex_rate_data.columns):
            return False
        if not self.original_nav_data['Date'].equals(self.forex_rate_data['Date']):
            return False
        return True


    def _load_nav_data(self, feather_path) -> None: 
        """
        Loads NAV data from a Feather file.

        Args:
            feather_path (str): Path to the feather file.

        Raises:
            FileNotFoundError: If the file cannot be read.
        """
        try:
            df = pd.read_feather(feather_path)
        except Exception:
            raise FileNotFoundError(f'NAV data file {feather_path} not found.')
        
        self.original_nav_data = df


    def _get_nav_currency(self) -> str:
        """
        Infers currency from NAV column.

        Returns:
            str: Currency code (e.g., 'USD', 'INR').

        Raises:
            ValueError: If no valid NAV column is found.
        """
        if 'NAV_INR' in self.original_nav_data.columns:
            return 'INR'
        
        nav_cols = [col for col in self.original_nav_data.columns if col.startswith('NAV_')][0]
        if not nav_cols:
            raise ValueError("No column found with prefix 'NAV_'. Cannot determine currency.")
        
        return str(nav_cols.split('_')[-1])


    def convert_to_inr(self, feather_path: str | None = None, nav_data: pd.DataFrame | None = None) -> pd.DataFrame:
        """
        Converts NAV from foreign currency to INR using historical exchange rates.

        Args:
            feather_path (str | None): Path to the feather file containing NAV data.
            nav_data (pd.DataFrame | None): Optional preloaded NAV DataFrame.

        Returns:
            pd.DataFrame: Converted DataFrame with columns ['Date', 'NAV_INR'].

        Raises:
            ValueError: If neither nav_data nor feather_path is provided.
        """

        if nav_data is not None:
            if not isinstance(nav_data, pd.DataFrame):
                raise TypeError(f"Expected nav_data to be of type 'pd.DataFrame', but got {type(nav_data)} instead.")
            self.original_nav_data = nav_data
        else:
            if feather_path is None:
                raise FileNotFoundError('Either a df or filepath must be provided')
            if not isinstance(feather_path, str):
                raise TypeError(f"Expected feather_path to be of type 'str', but got {type(feather_path)} instead.")
            self._load_nav_data(feather_path)

        currency = self._get_nav_currency()
        # print(currency)
        
        if currency == 'INR':
            return self.original_nav_data
        
        self._load_forex_data(currency)

        if not self._is_data_aligned():
            raise DatesNotAlignedError()

        converted_df = self.original_nav_data.copy()
        original_price_col = 'NAV_' + currency
        forex_col = currency + '_to_INR'
        converted_df[original_price_col] = converted_df[original_price_col] * self.forex_rate_data[forex_col]
        converted_df.columns = ['Date', 'NAV_INR']
        return converted_df
            