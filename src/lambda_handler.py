from mangum import Mangum
from src.main import app

# Handler for AWS Lambda
handler = Mangum(app)
