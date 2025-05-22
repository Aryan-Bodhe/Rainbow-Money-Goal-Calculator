import pyxirr
import pandas as pd
from source.SIP_Goal_Based import SipGoalBased as SGP

class SipCalculator:
    """
    A utility class for performing SIP-related financial calculations such as 
    monthly SIP requirement and effective XIRR based on user input.
    """
    def __init__(self):
        pass

    def compute_monthly_sip(self, sip_plan: SGP) -> float:
        """
        Computes the required monthly SIP amount to achieve a target goal amount.

        Args:
            sip_plan (SGP): An instance of SipGoalBased containing user parameters
                            such as time horizon, return rate, goal amount, and lumpsum.

        Returns:
            float: Required monthly SIP amount.

        Raises:
            ValueError: If the lumpsum amount alone is sufficient to achieve the goal,
                        resulting in a negative SIP requirement.
        """
        months = sip_plan.time_horizon * 12
        r = sip_plan.return_rate / 100 / 12  # monthly rate
        FV = sip_plan.goal_amount
        L = sip_plan.lumpsum_amount

        # SIP annuity formula adjusted for lumpsum at t=0
        monthly_sip = (FV - L * (1 + r) ** months) / (((1 + r) ** months - 1) / r)

        if monthly_sip < 0: 
            raise ValueError('[ERROR] Negative Monthly SIP. Reason: Lumpsum Amount is enough to achieve Goal Amount.')
        
        return monthly_sip

    def compute_xirr(self, sip_plan: SGP) -> float:
        """
        Computes the Extended Internal Rate of Return (XIRR) for the SIP investment plan.

        Args:
            sip_plan (SGP): An instance of SipGoalBased with user investment data.

        Returns:
            float: XIRR in percentage form.

        Raises:
            ValueError: If XIRR computation fails due to malformed or invalid cashflows.
        """
        time_horizon = sip_plan.time_horizon
        dates = []
        amounts = []

        # Add lumpsum outflow at the beginning if provided
        if sip_plan.lumpsum_amount > 0:
            amounts = [-sip_plan.lumpsum_amount]  # lump sum investment (negative cashflow)
            dates = self._generate_monthly_dates(time_horizon * 12 + 2)
        else:
            dates = self._generate_monthly_dates(time_horizon * 12 + 1) 

        # Add monthly SIP outflows
        amounts += [-sip_plan.monthly_sip for _ in range(time_horizon * 12)]

        # Final inflow on maturity (goal amount)
        amounts.append(sip_plan.goal_amount)

        try:
            xirr_value = pyxirr.xirr(dict(zip(dates, amounts)))
            return xirr_value * 100  # Convert to percentage
        except Exception as e:
            raise ValueError("[ERROR] XIRR computation failed. Reason: Invalid cashflows.")

    def _generate_monthly_dates(self, time_period):
        """
        Generates a list of monthly dates starting from the first day of the current month.

        Args:
            time_period (int): Number of monthly periods to generate.

        Returns:
            List[pd.Timestamp]: List of date objects spaced one month apart.
        """
        start_date = pd.Timestamp.today().replace(day=1)  # Start from current month
        return pd.date_range(start=start_date, periods=time_period, freq='MS').tolist()
