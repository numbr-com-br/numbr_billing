import axios from 'axios'
import { asaasService } from '../../../src/services/asaas.service'

jest.mock('axios')
const mockedAxios = axios as jest.Mocked<typeof axios>

describe('AsaasService', () => {
  let mockAxiosInstance: any

  beforeEach(() => {
    mockAxiosInstance = {
      post: jest.fn(),
      get: jest.fn(),
      delete: jest.fn(),
    }
    mockedAxios.create.mockReturnValue(mockAxiosInstance)
  })

  afterEach(() => {
    jest.clearAllMocks()
  })

  describe('createCustomer', () => {
    it('should create a customer successfully', async () => {
      const customerData = {
        name: 'John Doe',
        email: 'john@example.com',
        cpfCnpj: '12345678900',
        phone: '11999999999',
      }

      const mockResponse = {
        data: {
          id: 'cus_123',
          ...customerData,
        },
      }

      mockAxiosInstance.post.mockResolvedValue(mockResponse)

      const result = await asaasService.createCustomer(customerData)

      expect(mockAxiosInstance.post).toHaveBeenCalledWith('/customers', customerData)
      expect(result).toEqual(mockResponse.data)
    })

    it('should handle errors when creating customer', async () => {
      const customerData = {
        name: 'John Doe',
        email: 'john@example.com',
      }

      mockAxiosInstance.post.mockRejectedValue(new Error('API Error'))

      await expect(asaasService.createCustomer(customerData)).rejects.toThrow('API Error')
    })
  })

  describe('createSubscription', () => {
    it('should create a subscription successfully', async () => {
      const subscriptionData = {
        customer: 'cus_123',
        billingType: 'PIX' as const,
        value: 99.99,
        nextDueDate: '2024-01-01',
        cycle: 'MONTHLY',
        description: 'Test subscription',
      }

      const mockResponse = {
        data: {
          id: 'sub_456',
          ...subscriptionData,
          status: 'ACTIVE',
        },
      }

      mockAxiosInstance.post.mockResolvedValue(mockResponse)

      const result = await asaasService.createSubscription(subscriptionData)

      expect(mockAxiosInstance.post).toHaveBeenCalledWith('/subscriptions', subscriptionData)
      expect(result).toEqual(mockResponse.data)
    })
  })

  describe('getPayment', () => {
    it('should get payment details successfully', async () => {
      const paymentId = 'pay_789'
      const mockResponse = {
        data: {
          id: paymentId,
          customer: 'cus_123',
          value: 99.99,
          status: 'PENDING',
          dueDate: '2024-01-01',
          billingType: 'PIX',
          invoiceUrl: 'https://payment.link',
        },
      }

      mockAxiosInstance.get.mockResolvedValue(mockResponse)

      const result = await asaasService.getPayment(paymentId)

      expect(mockAxiosInstance.get).toHaveBeenCalledWith(`/payments/${paymentId}`)
      expect(result).toEqual(mockResponse.data)
    })
  })

  describe('cancelSubscription', () => {
    it('should cancel subscription successfully', async () => {
      const subscriptionId = 'sub_456'

      mockAxiosInstance.delete.mockResolvedValue({ data: {} })

      await asaasService.cancelSubscription(subscriptionId)

      expect(mockAxiosInstance.delete).toHaveBeenCalledWith(`/subscriptions/${subscriptionId}`)
    })
  })

  describe('createPaymentLink', () => {
    it('should create payment link successfully', async () => {
      const paymentData = {
        customer: 'cus_123',
        billingType: 'CREDIT_CARD' as const,
        value: 150.00,
        dueDate: '2024-01-15',
        description: 'Payment for services',
      }

      const mockResponse = {
        data: {
          id: 'pay_999',
          ...paymentData,
          invoiceUrl: 'https://checkout.asaas.com/pay_999',
          status: 'PENDING',
        },
      }

      mockAxiosInstance.post.mockResolvedValue(mockResponse)

      const result = await asaasService.createPaymentLink(paymentData)

      expect(mockAxiosInstance.post).toHaveBeenCalledWith('/payments', paymentData)
      expect(result).toEqual(mockResponse.data)
    })
  })

  describe('getPaymentLink', () => {
    it('should return invoice URL when available', async () => {
      const paymentId = 'pay_123'
      const mockResponse = {
        data: {
          id: paymentId,
          invoiceUrl: 'https://invoice.url',
          boletoUrl: 'https://boleto.url',
        },
      }

      mockAxiosInstance.get.mockResolvedValue(mockResponse)

      const result = await asaasService.getPaymentLink(paymentId)

      expect(result).toBe('https://invoice.url')
    })

    it('should return boleto URL when invoice URL is not available', async () => {
      const paymentId = 'pay_123'
      const mockResponse = {
        data: {
          id: paymentId,
          invoiceUrl: null,
          boletoUrl: 'https://boleto.url',
        },
      }

      mockAxiosInstance.get.mockResolvedValue(mockResponse)

      const result = await asaasService.getPaymentLink(paymentId)

      expect(result).toBe('https://boleto.url')
    })

    it('should return empty string when no URLs are available', async () => {
      const paymentId = 'pay_123'
      const mockResponse = {
        data: {
          id: paymentId,
          invoiceUrl: null,
          boletoUrl: null,
        },
      }

      mockAxiosInstance.get.mockResolvedValue(mockResponse)

      const result = await asaasService.getPaymentLink(paymentId)

      expect(result).toBe('')
    })
  })
})