import serverlessExpress from '@vendia/serverless-express'
import type { Handler, Context, APIGatewayProxyEvent } from 'aws-lambda'
import { app } from './app.js'

let serverlessExpressInstance: Handler

async function setup(event: APIGatewayProxyEvent, context: Context) {
  serverlessExpressInstance = serverlessExpress({ app })
  return serverlessExpressInstance(event, context, () => {})
}

export const handler: Handler = async (event: APIGatewayProxyEvent, context: Context) => {
  if (serverlessExpressInstance) {
    return serverlessExpressInstance(event, context, () => {})
  }

  return setup(event, context)
}