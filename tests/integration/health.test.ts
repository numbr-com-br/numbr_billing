import request from 'supertest'
import express from 'express'

const app = express()

app.get('/health', (req, res) => {
  res.json({ status: 'ok', timestamp: new Date().toISOString() })
})

describe('Health Check Integration Test', () => {
  it('should return health status', async () => {
    const response = await request(app).get('/health')

    expect(response.status).toBe(200)
    expect(response.body.status).toBe('ok')
    expect(response.body.timestamp).toBeDefined()
    expect(new Date(response.body.timestamp)).toBeInstanceOf(Date)
  })
})