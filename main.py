# main.py

import time as tm
from rich.console import Console
import tracemalloc
import asyncio
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse

from core.goal_engine import run_analysis
from core.exceptions import DataFileNotFoundError
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
    logger.info('---------- New Request Received ----------')
    try:
        start = tm.time()
        tracemalloc.start()

        result = run_analysis(
            goal_amount=req.goal_amount,
            time_horizon=req.time_horizon,
            lumpsum=req.lumpsum_amount,
            risk_profile=req.risk_profile
        )

        _, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        end = tm.time()

        logger.info(f"Total Test Runtime: {end - start : 0.3f} s.")
        logger.info(f"Peak memory usage: {peak / 10**6:.3f} MB")
        logger.info('Goal Calculation Completed Successfully.')
        logger.info('------------------------------------------')
        # console.print_json(data=result.model_dump())
        return result
    except DataFileNotFoundError as e:
        logger.exception("Unexpected error during goal calculation.")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.exception("Unexpected error during goal calculation.")
        raise HTTPException(status_code=500, detail="Internal error")


if __name__ == '__main__':
    console = Console()
    output = asyncio.run( 
        calculate_goal(
            GoalRequest(
                goal_amount=1_000_000,
                time_horizon=5,
                lumpsum_amount=0,
                risk_profile='conservative',
            )
        )
    )


