from __future__ import annotations
import numpy as np
import pandas as pd
from typing import TYPE_CHECKING
from colorama import Fore

if TYPE_CHECKING:
    from source.SIP_Goal_Based import SipGoalBased as SGP

class SipProbabilityCalculator:
    """
    Simulates SIP outcomes via Monte Carlo to estimate probability of reaching a financial goal,
    and suggests adjusted SIP amounts to meet a target probability or reach goals earlier.
    """

    def __init__(self, feather_path: str):
        """
        :param nav_values: 1D array of historical NAVs on the first working day of each month.
        """

        try:
            dataset = pd.read_feather(feather_path)
        except Exception:
            raise ValueError('[ERROR] Historical data could not be found.')
            

        nav_values = dataset['Closing Price'].to_numpy()
        # print("NAV SAMPLE:")
        # print(dataset.head(10))

        # Compute monthly log returns from NAV series
        if len(nav_values) < 2:
            raise ValueError("[ERROR] At least two NAV values are required.")
        
        self.navs = nav_values
        self.log_returns = np.log(nav_values[1:] / nav_values[:-1])
        self.mu = np.mean(self.log_returns)
        self.sigma = np.std(self.log_returns)
        

    def _simulate_final_values(self, time_horizon_years: int, monthly_sip: float, num_simulations: int = 10000):
        """
        Run Monte Carlo simulations to project final portfolio values.
        
        :param time_horizon_years: Investment horizon in years.
        :param monthly_sip: Amount invested at the beginning of each month.
        :param num_simulations: Number of Monte Carlo trials.
        :return: Array of simulated final portfolio values.
        """
        months = int(time_horizon_years * 12)
        # generate random monthly returns
        rand_returns = np.random.normal(self.mu, self.sigma, size=(num_simulations, months))
        
        # simulate portfolio growth
        # Start with zero; invest SIP at beginning of each month, then apply return
        values = np.zeros(num_simulations)
        for m in range(months):
            values = (values + monthly_sip) * np.exp(rand_returns[:, m])
        return values


    def probability_of_goal(self, goal_amount: float, time_horizon: int, monthly_sip: float, num_simulations: int = 10000):
        """
        Estimate probability of achieving or exceeding the goal.
        
        :param goal_amount: Target corpus at the end of horizon.
        :param time_horizon_years: Investment horizon in years.
        :param monthly_sip: Monthly SIP amount.
        :param num_simulations: Number of Monte Carlo trials.
        :return: Probability (0-1) of reaching the goal.
        """

        finals = self._simulate_final_values(time_horizon, monthly_sip, num_simulations)
        return np.mean(finals >= goal_amount)
    

    def suggest_sip_for_probability(self, sip_plan:SGP, target_prob: float = 0.95, num_simulations: int = 10000):
        """
        Suggest a SIP amount to reach the goal with at least target probability.
        
        :param goal_amount: Target corpus.
        :param time_horizon_years: Horizon in years.
        :param target_prob: Desired probability (e.g., 0.8 for 80%).
        :param num_simulations: Number of trials per SIP guess.
        :return: Required monthly SIP amount.
        """
        # binary search over SIP amount
        low, high = 0, sip_plan.goal_amount
        for _ in range(20):  # ~20 iterations for convergence
            mid = (low + high) / 2
            prob = self.probability_of_goal(sip_plan.goal_amount, sip_plan.time_horizon, mid, num_simulations)
            if prob < target_prob:
                low = mid
            else:
                high = mid
        return round(high, 2)