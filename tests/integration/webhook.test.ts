import request from 'supertest'
import express from 'express'
import { webhookRouter } from '../../src/webhooks/asaas.webhook'
import { prisma } from '../../src/services/prisma.service'
import { config } from '../../src/config/env'
import { SubscriptionFactory, PaymentFactory } from '../helpers/factories'

const app = express()
app.use(express.json())
app.use('/webhooks', webhookRouter)

describe('Webhook Integration Tests', () => {
  const validWebhookToken = config.asaas.webhookToken

  describe('POST /webhooks/asaas', () => {
    it('should reject request with invalid token', async () => {
      const response = await request(app)
        .post('/webhooks/asaas')
        .set('asaas-access-token', 'invalid-token')
        .send({
          event: 'PAYMENT_CREATED',
          payment: { id: 'pay_123' },
        })

      expect(response.status).toBe(401)
      expect(response.body.error).toBe('Unauthorized')
    })

    it('should handle PAYMENT_CREATED event', async () => {
      const subscription = await SubscriptionFactory.create()
      
      const webhookPayload = {
        event: 'PAYMENT_CREATED',
        payment: {
          id: 'pay_asaas_123',
          customer: 'cus_123',
          subscription: subscription.asaasSubscriptionId,
          value: 99.99,
          status: 'PENDING',
          billingType: 'PIX',
          dueDate: '2024-01-01',
          invoiceUrl: 'https://invoice.url',
          invoiceNumber: 'INV-001',
          description: 'Monthly payment',
        },
      }

      const response = await request(app)
        .post('/webhooks/asaas')
        .set('asaas-access-token', validWebhookToken)
        .send(webhookPayload)

      expect(response.status).toBe(200)
      expect(response.body.success).toBe(true)

      const payment = await prisma.payment.findFirst({
        where: { asaasPaymentId: 'pay_asaas_123' },
      })

      expect(payment).toBeDefined()
      expect(payment?.subscriptionId).toBe(subscription.id)
      expect(payment?.amount.toString()).toBe('99.99')
      expect(payment?.status).toBe('PENDING')

      const webhookLog = await prisma.webhookLog.findFirst({
        where: { event: 'PAYMENT_CREATED' },
      })

      expect(webhookLog).toBeDefined()
      expect(webhookLog?.success).toBe(true)
    })

    it('should handle PAYMENT_RECEIVED event and update subscription status', async () => {
      const subscription = await SubscriptionFactory.create({ status: 'PENDING' })
      const payment = await PaymentFactory.create({
        subscriptionId: subscription.id,
        asaasPaymentId: 'pay_asaas_456',
        status: 'PENDING',
      })

      const webhookPayload = {
        event: 'PAYMENT_RECEIVED',
        payment: {
          id: 'pay_asaas_456',
          customer: 'cus_123',
          subscription: subscription.asaasSubscriptionId,
          value: 99.99,
          status: 'RECEIVED',
          paymentDate: '2024-01-01T10:00:00Z',
        },
      }

      const response = await request(app)
        .post('/webhooks/asaas')
        .set('asaas-access-token', validWebhookToken)
        .send(webhookPayload)

      expect(response.status).toBe(200)

      const updatedPayment = await prisma.payment.findUnique({
        where: { id: payment.id },
      })

      expect(updatedPayment?.status).toBe('RECEIVED')
      expect(updatedPayment?.paidAt).toBeDefined()

      const updatedSubscription = await prisma.subscription.findUnique({
        where: { id: subscription.id },
      })

      expect(updatedSubscription?.status).toBe('ACTIVE')
    })

    it('should handle PAYMENT_OVERDUE event', async () => {
      const payment = await PaymentFactory.create({
        asaasPaymentId: 'pay_asaas_789',
        status: 'PENDING',
      })

      const webhookPayload = {
        event: 'PAYMENT_OVERDUE',
        payment: {
          id: 'pay_asaas_789',
          status: 'OVERDUE',
        },
      }

      const response = await request(app)
        .post('/webhooks/asaas')
        .set('asaas-access-token', validWebhookToken)
        .send(webhookPayload)

      expect(response.status).toBe(200)

      const updatedPayment = await prisma.payment.findUnique({
        where: { id: payment.id },
      })

      expect(updatedPayment?.status).toBe('OVERDUE')
    })

    it('should handle PAYMENT_REFUNDED event', async () => {
      const payment = await PaymentFactory.create({
        asaasPaymentId: 'pay_asaas_999',
        status: 'RECEIVED',
      })

      const webhookPayload = {
        event: 'PAYMENT_REFUNDED',
        payment: {
          id: 'pay_asaas_999',
          status: 'REFUNDED',
        },
      }

      const response = await request(app)
        .post('/webhooks/asaas')
        .set('asaas-access-token', validWebhookToken)
        .send(webhookPayload)

      expect(response.status).toBe(200)

      const updatedPayment = await prisma.payment.findUnique({
        where: { id: payment.id },
      })

      expect(updatedPayment?.status).toBe('REFUNDED')
    })

    it('should log unhandled events', async () => {
      const webhookPayload = {
        event: 'UNKNOWN_EVENT',
        data: { test: 'data' },
      }

      const response = await request(app)
        .post('/webhooks/asaas')
        .set('asaas-access-token', validWebhookToken)
        .send(webhookPayload)

      expect(response.status).toBe(200)

      const webhookLog = await prisma.webhookLog.findFirst({
        where: { event: 'UNKNOWN_EVENT' },
      })

      expect(webhookLog).toBeDefined()
      expect(webhookLog?.success).toBe(true)
    })

    it('should handle and log errors', async () => {
      jest.spyOn(prisma.webhookLog, 'create')
        .mockRejectedValueOnce(new Error('Database error'))
        .mockResolvedValueOnce({} as any)

      const webhookPayload = {
        event: 'PAYMENT_CREATED',
        payment: { id: 'pay_123' },
      }

      const response = await request(app)
        .post('/webhooks/asaas')
        .set('asaas-access-token', validWebhookToken)
        .send(webhookPayload)

      expect(response.status).toBe(500)
      expect(response.body.error).toBe('Internal server error')
    })
  })
})