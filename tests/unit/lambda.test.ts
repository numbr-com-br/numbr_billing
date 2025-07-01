import { handler } from '../../src/lambda'
import { APIGatewayProxyEvent, Context } from 'aws-lambda'

jest.mock('@vendia/serverless-express', () => ({
  default: jest.fn(() => jest.fn((event, context, callback) => {
    callback(null, {
      statusCode: 200,
      body: JSON.stringify({ message: 'mocked response' }),
    })
  })),
}))

jest.mock('../../src/app', () => ({
  app: {
    use: jest.fn(),
    get: jest.fn(),
    post: jest.fn(),
  },
}))

describe('Lambda Handler', () => {
  let mockEvent: APIGatewayProxyEvent
  let mockContext: Context

  beforeEach(() => {
    mockEvent = {
      httpMethod: 'GET',
      path: '/health',
      headers: {},
      body: null,
      isBase64Encoded: false,
    } as APIGatewayProxyEvent

    mockContext = {
      callbackWaitsForEmptyEventLoop: false,
      functionName: 'test-function',
      functionVersion: '1',
      invokedFunctionArn: 'arn:aws:lambda:us-east-1:123456789:function:test',
      memoryLimitInMB: '128',
      awsRequestId: 'test-request-id',
      logGroupName: 'test-log-group',
      logStreamName: 'test-log-stream',
      getRemainingTimeInMillis: () => 30000,
      done: jest.fn(),
      fail: jest.fn(),
      succeed: jest.fn(),
    } as unknown as Context
  })

  afterEach(() => {
    jest.clearAllMocks()
  })

  it('should handle requests successfully', async () => {
    const result = await handler(mockEvent, mockContext)

    expect(result).toEqual({
      statusCode: 200,
      body: JSON.stringify({ message: 'mocked response' }),
    })
  })

  it('should reuse serverless express instance on subsequent calls', async () => {
    await handler(mockEvent, mockContext)
    await handler(mockEvent, mockContext)

    const serverlessExpress = require('@vendia/serverless-express').default
    expect(serverlessExpress).toHaveBeenCalledTimes(1)
  })

  it('should handle different HTTP methods', async () => {
    const postEvent = { ...mockEvent, httpMethod: 'POST' }
    const result = await handler(postEvent, mockContext)

    expect(result).toEqual({
      statusCode: 200,
      body: JSON.stringify({ message: 'mocked response' }),
    })
  })

  it('should handle different paths', async () => {
    const apiEvent = { ...mockEvent, path: '/api/checkout/plans' }
    const result = await handler(apiEvent, mockContext)

    expect(result).toEqual({
      statusCode: 200,
      body: JSON.stringify({ message: 'mocked response' }),
    })
  })
})