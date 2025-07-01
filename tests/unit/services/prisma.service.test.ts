import { prisma, connectDatabase, disconnectDatabase } from '../../../src/services/prisma.service'

describe('PrismaService', () => {
  describe('connectDatabase', () => {
    it('should connect to database successfully', async () => {
      const consoleSpy = jest.spyOn(console, 'log').mockImplementation()
      const connectSpy = jest.spyOn(prisma, '$connect').mockResolvedValue()

      await connectDatabase()

      expect(connectSpy).toHaveBeenCalled()
      expect(consoleSpy).toHaveBeenCalledWith('Database connected successfully')

      consoleSpy.mockRestore()
      connectSpy.mockRestore()
    })

    it('should exit process on connection failure', async () => {
      const consoleErrorSpy = jest.spyOn(console, 'error').mockImplementation()
      const processExitSpy = jest.spyOn(process, 'exit').mockImplementation(() => {
        throw new Error('process.exit')
      })
      const connectSpy = jest.spyOn(prisma, '$connect').mockRejectedValue(new Error('Connection failed'))

      await expect(connectDatabase()).rejects.toThrow('process.exit')

      expect(connectSpy).toHaveBeenCalled()
      expect(consoleErrorSpy).toHaveBeenCalledWith('Failed to connect to database:', expect.any(Error))
      expect(processExitSpy).toHaveBeenCalledWith(1)

      consoleErrorSpy.mockRestore()
      processExitSpy.mockRestore()
      connectSpy.mockRestore()
    })
  })

  describe('disconnectDatabase', () => {
    it('should disconnect from database successfully', async () => {
      const disconnectSpy = jest.spyOn(prisma, '$disconnect').mockResolvedValue()

      await disconnectDatabase()

      expect(disconnectSpy).toHaveBeenCalled()

      disconnectSpy.mockRestore()
    })
  })
})