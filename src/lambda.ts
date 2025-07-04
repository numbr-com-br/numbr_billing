import serverless from 'serverless-http'
import { app, appSetupPromise } from './app'

// Create the serverless handler
const serverlessHandler = serverless(app)

// Wrap to ensure app is setup before handling requests
export const handler: typeof serverlessHandler = async (event, context) => {
  await appSetupPromise
  return serverlessHandler(event, context)
}