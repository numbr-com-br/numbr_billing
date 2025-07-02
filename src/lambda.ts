import { configure } from '@vendia/serverless-express'
import type { Context, APIGatewayProxyEvent, APIGatewayProxyResult } from 'aws-lambda'
import { app } from './app.js'

let serverlessExpressInstance: any

export const handler = async (
  event: APIGatewayProxyEvent, 
  context: Context
): Promise<APIGatewayProxyResult> => {
  if (!serverlessExpressInstance) {
    serverlessExpressInstance = configure({ app })
  }
  
  return serverlessExpressInstance(event, context)
}