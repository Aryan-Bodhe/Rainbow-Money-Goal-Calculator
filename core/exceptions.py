# ---- Asset.py ---- #

class InvalidReturnRateError(Exception):
    def __init__(self, erring_rate):
        message = f"Expected a positive return rate, but got: {erring_rate}. Rate must be > 0."
        super().__init__(message)


class InvalidCashflowsError(Exception):
    def __init__(self, cashflows):
        message = (
            f"Invalid cash flow series provided: {cashflows}. "
            "Ensure at least one negative (investment) and one positive (redeem) value, "
            "and that dates align correctly."
        )
        super().__init__(message)


class InvalidStartDateError(Exception):
    def __init__(self, start_date):
        message = f"Invalid start date: {start_date}. Start date must be a valid datetime.date or datetime.datetime."
        super().__init__(message)


class InvalidSipAmountError(Exception):
    def __init__(self, error_amount):
        message = f"SIP amount must be non-negative, but got: {error_amount}."
        super().__init__(message)


class LumpsumEnoughToReachGoalError(Exception):
    def __init__(self, lumpsum, goal_amount):
        message = (
            f"Lumpsum of {lumpsum} is already greater than or equal to the goal amount {goal_amount}. "
            "No SIP is required."
        )
        super().__init__(message)


class XirrComputationFailedError(Exception):
    def __init__(self, original_exception):
        message = (
            f"XIRR computation failed: {original_exception}. "
            "Check that cash flows contain at least one negative and one positive value "
            "and that dates are in chronological order."
        )
        super().__init__(message)

# ---- SIP_Goal_Based.py ---- #

class InvalidGoalAmountError(Exception):
    def __init__(self, goal_amount):
        message = f"Goal amount must be positive, but got: {goal_amount}."
        super().__init__(message)


class InvalidTimeHorizonError(Exception):
    def __init__(self, time_horizon):
        message = f"Time horizon must be greater than zero, but got: {time_horizon}."
        super().__init__(message)


class InvalidLumpsumAmountError(Exception):
    def __init__(self, lumpsum, goal_amount):
        if lumpsum < 0:
            message = f"Lumpsum cannot be negative (got {lumpsum})."
        else:
            message = f"Lumpsum of {lumpsum} exceeds or equals the goal amount {goal_amount}."
        super().__init__(message)


class TimeHorizonNotIntegerError(Exception):
    def __init__(self, value):
        message = f"Time horizon must be an integer number of years (got {value})."
        super().__init__(message)


class InvalidRiskProfileError(Exception):
    def __init__(self, profile, valid_profiles):
        message = (
            f"Invalid risk profile: '{profile}'. "
            f"Expected one of {valid_profiles}."
        )
        super().__init__(message)


class DataFileNotFoundError(Exception):
    def __init__(self, asset_name, feather_path):
        message = (
            f"No Feather file found for asset '{asset_name}': {feather_path}"
        )
        super().__init__(message)



# ---- Prob_Calc.py ---- #

class HistoricalDataNotFoundError(Exception):
    def __init__(self, asset_name):
        message = f"Historical NAV data not found for asset: '{asset_name}'."
        super().__init__(message)


class HistoricalDataTooLowError(Exception):
    def __init__(self, asset_name, available_months, required_months):
        message = (
            f"Insufficient historical data for asset '{asset_name}': "
            f"found {available_months} months, but need at least {required_months} months."
        )
        super().__init__(message)


# ---- Return_Forecaster.py ---- #

class NeitherDataNorPathProvidedError(Exception):
    def __init__(self):
        message = (
            "Must provide either a DataFrame of returns or a valid file path. "
            "Both were missing."
        )
        super().__init__(message)


class InvalidReturnCalculationModeError(Exception):
    def __init__(self, mode, valid_modes):
        message = (
            f"Invalid return calculation mode: '{mode}'. "
            f"Valid modes are: {valid_modes}."
        )
        super().__init__(message)


# ---- CurrencyConverter.py ---- #

class NavAlreadyInINRError(Exception):
    def __init__(self):
        message = (
            "NAV Values Already in INR."
        )
        super().__init__(message)

class DatesNotAlignedError(Exception):
    def __init__(self):
        message = (
            f"Date columns of NAV_data and Forex do not match."
        )
        super().__init__(message)