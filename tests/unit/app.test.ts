import { app } from '../../src/app'

describe('App Configuration', () => {
  beforeEach(() => {
    process.env.IS_LAMBDA = 'true'
  })

  afterEach(() => {
    delete process.env.IS_LAMBDA
  })

  it('should export Express app instance', () => {
    expect(app).toBeDefined()
    expect(app.use).toBeDefined()
    expect(app.get).toBeDefined()
    expect(app.post).toBeDefined()
  })

  it('should not start server when IS_LAMBDA is set', () => {
    const listenSpy = jest.spyOn(app, 'listen')
    
    // Re-require the module to trigger the IS_LAMBDA check
    jest.isolateModules(() => {
      require('../../src/app')
    })

    expect(listenSpy).not.toHaveBeenCalled()
  })

  it('should handle setup errors gracefully in Lambda environment', async () => {
    const consoleErrorSpy = jest.spyOn(console, 'error').mockImplementation()
    const processExitSpy = jest.spyOn(process, 'exit').mockImplementation()

    // Mock connectDatabase to throw error
    jest.mock('../../src/services/prisma.service', () => ({
      connectDatabase: jest.fn().mockRejectedValue(new Error('Connection failed')),
      prisma: {},
    }))

    jest.isolateModules(() => {
      require('../../src/app')
    })

    // Wait for async setup to complete
    await new Promise(resolve => setTimeout(resolve, 100))

    expect(consoleErrorSpy).toHaveBeenCalledWith('Failed to setup app:', expect.any(Error))
    expect(processExitSpy).not.toHaveBeenCalled()

    consoleErrorSpy.mockRestore()
    processExitSpy.mockRestore()
  })
})