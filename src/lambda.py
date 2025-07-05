from mangum import Mangum
from src.main import app

# Create the Lambda handler
handler = Mangum(app, lifespan="off")