import axios, { AxiosInstance } from 'axios'
import { config } from '../config/env.js'

export interface AsaasCustomer {
  id: string
  name: string
  email: string
  cpfCnpj?: string
  phone?: string
}

export interface AsaasSubscription {
  id: string
  customer: string
  billingType: 'BOLETO' | 'CREDIT_CARD' | 'PIX'
  value: number
  nextDueDate: string
  cycle: 'WEEKLY' | 'BIWEEKLY' | 'MONTHLY' | 'QUARTERLY' | 'SEMIANNUALLY' | 'YEARLY'
  description?: string
  status: string
}

export interface AsaasPayment {
  id: string
  customer: string
  subscription?: string
  value: number
  dueDate: string
  status: string
  billingType: string
  invoiceUrl?: string
  boletoUrl?: string
  pixQrCode?: string
}

class AsaasService {
  private api: AxiosInstance

  constructor() {
    this.api = axios.create({
      baseURL: config.asaas.apiUrl,
      headers: {
        'Content-Type': 'application/json',
        access_token: config.asaas.apiKey,
      },
    })
  }

  async createCustomer(data: {
    name: string
    email: string
    cpfCnpj?: string
    phone?: string
  }): Promise<AsaasCustomer> {
    const response = await this.api.post('/customers', data)
    return response.data
  }

  async getCustomer(id: string): Promise<AsaasCustomer> {
    const response = await this.api.get(`/customers/${id}`)
    return response.data
  }

  async createSubscription(data: {
    customer: string
    billingType: 'BOLETO' | 'CREDIT_CARD' | 'PIX'
    value: number
    nextDueDate: string
    cycle: string
    description?: string
  }): Promise<AsaasSubscription> {
    const response = await this.api.post('/subscriptions', data)
    return response.data
  }

  async getSubscription(id: string): Promise<AsaasSubscription> {
    const response = await this.api.get(`/subscriptions/${id}`)
    return response.data
  }

  async cancelSubscription(id: string): Promise<void> {
    await this.api.delete(`/subscriptions/${id}`)
  }

  async getPayment(id: string): Promise<AsaasPayment> {
    const response = await this.api.get(`/payments/${id}`)
    return response.data
  }

  async getSubscriptionPayments(subscriptionId: string): Promise<AsaasPayment[]> {
    const response = await this.api.get(`/subscriptions/${subscriptionId}/payments`)
    return response.data.data || []
  }

  async createPaymentLink(data: {
    customer: string
    billingType: 'BOLETO' | 'CREDIT_CARD' | 'PIX'
    value: number
    dueDate: string
    description?: string
  }): Promise<AsaasPayment> {
    const response = await this.api.post('/payments', data)
    return response.data
  }

  async getPaymentLink(paymentId: string): Promise<string> {
    const payment = await this.getPayment(paymentId)
    return payment.invoiceUrl || payment.boletoUrl || ''
  }
}

export const asaasService = new AsaasService()