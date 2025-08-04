# main.py

import time as tm
import tracemalloc
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse

from core.goal_engine import run_analysis
from core.sip_plotter import generate_returns_html
from core.exceptions import DataFileNotFoundError, InvalidAllocationWeightsError
from models.goal_request import GoalRequest
from models.portfolio_summary import PortfolioSummary
from utils.logger import get_logger

# Initialize FastAPI app
app = FastAPI()

@app.post(
    "/calculate-goal",
    response_model=PortfolioSummary,
    summary="Calculate Goal-Based SIP Plan",
    description="""
        This endpoint computes a goal-based SIP strategy based on user inputs such as goal amount,
        time horizon, lumpsum, and risk profile. It returns the monthly SIP needed, asset allocation,
        expected growth, and other insights including XIRR and goal probability.
    """
)
async def calculate_goal(req: GoalRequest) -> JSONResponse:
    """
    Endpoint to calculate SIP goal based on user input.
    Logs performance metrics and handles expected/unexpected exceptions.
    """
    logger = get_logger()
    logger.info('------- New Goal Calculation Request Received -------')
    try:
        start = tm.time()
        tracemalloc.start()

        result = run_analysis(
            goal_amount=req.goal_amount,
            time_horizon=req.time_horizon,
            lumpsum=req.lumpsum_amount,
            risk_profile=req.risk_profile,
            allocation=req.asset_allocation
        )

        _, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        end = tm.time()

        logger.info(f"Total Request Runtime: {end - start : 0.3f} s.")
        logger.info(f"Peak memory usage: {peak / 10**6:.3f} MB")
        logger.info('Goal Calculation Completed Successfully.')
        logger.info('------------------------------------------')
        return result
    
    except DataFileNotFoundError as e:
        logger.exception(e)
        raise HTTPException(status_code=400, detail="One or more specified assets do not exist in database.")
    
    except InvalidAllocationWeightsError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    except Exception as e:
        logger.exception("Unexpected error during goal calculation.")
        raise HTTPException(status_code=500, detail=f"Unexpected error during goal calculation: {str(e)}.")

@app.post(
    "/get-returns-visualization",
    response_class=HTMLResponse,
    summary="Get Interactive Returns Visualization",
    description="""
        Returns an interactive HTML visualization of the rolling returns distribution
        and trend for the goal-based SIP analysis.
    """
)
async def get_returns_visualization(
    pf_summary: PortfolioSummary
) -> HTMLResponse:
    """
    Generate and return an interactive HTML visualization of rolling returns.
    """
    logger = get_logger()
    logger.info('------- New Visualization Request Received -------')
    try:        
        start = tm.time()
        tracemalloc.start()
        
        rolling_returns = pf_summary.rolling_returns
        dates = pf_summary.dates

        if rolling_returns is None:
            logger.warning('Rolling Returns List is empty.')
        if dates is None:
            logger.warning('Dates List is empty.')
        
        html_content = generate_returns_html(rolling_returns, dates)
        logger.info('Rolling Returns and Returns Distribution chart generated.')

        _, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        end = tm.time()
        logger.info(f"Total Request Runtime: {end - start : 0.3f} s.")
        logger.info(f"Peak memory usage: {peak / 10**6:.3f} MB")
        logger.info('Returns Visualization Completed Successfully.')
        logger.info('------------------------------------------')

        return HTMLResponse(content=html_content)
    
    except DataFileNotFoundError as e:
        logger.error(f"Data file not found: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
    
    except Exception as e:
        logger.error(f"Error generating visualization: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
