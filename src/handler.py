"""
AWS Lambda handler for FastAPI application using Mangum
"""
from mangum import Mangum
from src.main import app

# Create the handler for AWS Lambda
# lifespan="off" is used to disable lifecycle events in Lambda
handler = Mangum(app, lifespan="off")