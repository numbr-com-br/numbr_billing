import request from 'supertest'
import express from 'express'
import { checkoutRouter } from '../../src/routes/checkout.route'
import { prisma } from '../../src/services/prisma.service'
import { asaasService } from '../../src/services/asaas.service'
import { PlanFactory, AddonFactory, CustomerFactory } from '../helpers/factories'

jest.mock('../../src/services/asaas.service')

const app = express()
app.use(express.json())
app.use('/api/checkout', checkoutRouter)

describe('Checkout API Integration Tests', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  describe('GET /api/checkout/plans', () => {
    it('should return active plans and addons', async () => {
      const plan1 = await PlanFactory.create({ name: 'Basic Plan', price: 49.99 })
      const plan2 = await PlanFactory.create({ name: 'Pro Plan', price: 99.99 })
      await PlanFactory.create({ name: 'Inactive Plan', isActive: false })

      const addon1 = await AddonFactory.create({ name: 'Extra Storage', price: 9.99 })
      const addon2 = await AddonFactory.create({ name: 'Priority Support', price: 19.99 })
      await AddonFactory.create({ name: 'Inactive Addon', isActive: false })

      const response = await request(app).get('/api/checkout/plans')

      expect(response.status).toBe(200)
      expect(response.body.plans).toHaveLength(2)
      expect(response.body.addons).toHaveLength(2)
      expect(response.body.plans[0].id).toBe(plan1.id)
      expect(response.body.plans[1].id).toBe(plan2.id)
      expect(response.body.addons[0].id).toBe(addon1.id)
      expect(response.body.addons[1].id).toBe(addon2.id)
    })

    it('should handle database errors gracefully', async () => {
      jest.spyOn(prisma.plan, 'findMany').mockRejectedValue(new Error('Database error'))

      const response = await request(app).get('/api/checkout/plans')

      expect(response.status).toBe(500)
      expect(response.body.error).toBe('Failed to fetch plans')
    })
  })

  describe('POST /api/checkout/start', () => {
    it('should create a new subscription for new customer', async () => {
      const plan = await PlanFactory.create()
      const addon = await AddonFactory.create()

      const mockAsaasCustomer = { id: 'cus_asaas_123' }
      const mockAsaasSubscription = { id: 'sub_asaas_456' }
      const mockPaymentLink = {
        id: 'pay_asaas_789',
        invoiceUrl: 'https://checkout.asaas.com/invoice/123',
        boletoUrl: null,
      }

      ;(asaasService.createCustomer as jest.Mock).mockResolvedValue(mockAsaasCustomer)
      ;(asaasService.createSubscription as jest.Mock).mockResolvedValue(mockAsaasSubscription)
      ;(asaasService.createPaymentLink as jest.Mock).mockResolvedValue(mockPaymentLink)

      const response = await request(app)
        .post('/api/checkout/start')
        .send({
          planId: plan.id,
          addonIds: [addon.id],
          customer: {
            name: 'New Customer',
            email: 'new@example.com',
            cpfCnpj: '12345678900',
            phone: '11999999999',
          },
          billingType: 'PIX',
        })

      expect(response.status).toBe(200)
      expect(response.body.success).toBe(true)
      expect(response.body.subscriptionId).toBeDefined()
      expect(response.body.paymentUrl).toBe('https://checkout.asaas.com/invoice/123')
      expect(response.body.paymentId).toBe('pay_asaas_789')

      const createdCustomer = await prisma.customer.findUnique({
        where: { email: 'new@example.com' },
      })
      expect(createdCustomer).toBeDefined()
      expect(createdCustomer?.asaasCustomerId).toBe('cus_asaas_123')

      const subscription = await prisma.subscription.findUnique({
        where: { id: response.body.subscriptionId },
        include: { addons: true },
      })
      expect(subscription).toBeDefined()
      expect(subscription?.planId).toBe(plan.id)
      expect(subscription?.addons).toHaveLength(1)
    })

    it('should use existing customer if email already exists', async () => {
      const existingCustomer = await CustomerFactory.create({
        email: 'existing@example.com',
        asaasCustomerId: 'cus_existing_123',
      })
      const plan = await PlanFactory.create()

      const mockAsaasSubscription = { id: 'sub_asaas_456' }
      const mockPaymentLink = {
        id: 'pay_asaas_789',
        invoiceUrl: 'https://checkout.asaas.com/invoice/123',
        boletoUrl: null,
      }

      ;(asaasService.createSubscription as jest.Mock).mockResolvedValue(mockAsaasSubscription)
      ;(asaasService.createPaymentLink as jest.Mock).mockResolvedValue(mockPaymentLink)

      const response = await request(app)
        .post('/api/checkout/start')
        .send({
          planId: plan.id,
          customer: {
            name: 'Existing Customer',
            email: 'existing@example.com',
          },
          billingType: 'CREDIT_CARD',
        })

      expect(response.status).toBe(200)
      expect(asaasService.createCustomer).not.toHaveBeenCalled()

      const subscription = await prisma.subscription.findUnique({
        where: { id: response.body.subscriptionId },
      })
      expect(subscription?.customerId).toBe(existingCustomer.id)
    })

    it('should return 404 for inactive or non-existent plan', async () => {
      const response = await request(app)
        .post('/api/checkout/start')
        .send({
          planId: 'non-existent-plan',
          customer: {
            name: 'Test Customer',
            email: 'test@example.com',
          },
          billingType: 'PIX',
        })

      expect(response.status).toBe(404)
      expect(response.body.error).toBe('Plan not found or inactive')
    })

    it('should handle Asaas API errors', async () => {
      const plan = await PlanFactory.create()

      ;(asaasService.createCustomer as jest.Mock).mockRejectedValue(new Error('Asaas API error'))

      const response = await request(app)
        .post('/api/checkout/start')
        .send({
          planId: plan.id,
          customer: {
            name: 'Test Customer',
            email: 'test@example.com',
          },
          billingType: 'PIX',
        })

      expect(response.status).toBe(500)
      expect(response.body.error).toBe('Failed to process checkout')
    })
  })

  describe('GET /api/checkout/subscription/:id', () => {
    it('should return subscription details with relationships', async () => {
      const customer = await CustomerFactory.create()
      const plan = await PlanFactory.create()
      const subscription = await prisma.subscription.create({
        data: {
          customerId: customer.id,
          planId: plan.id,
          status: 'ACTIVE',
          startDate: new Date(),
        },
      })

      const addon = await AddonFactory.create()
      await prisma.subscriptionAddon.create({
        data: {
          subscriptionId: subscription.id,
          addonId: addon.id,
          quantity: 1,
        },
      })

      await prisma.payment.create({
        data: {
          subscriptionId: subscription.id,
          amount: 99.99,
          status: 'RECEIVED',
          dueDate: new Date(),
          paidAt: new Date(),
        },
      })

      const response = await request(app).get(`/api/checkout/subscription/${subscription.id}`)

      expect(response.status).toBe(200)
      expect(response.body.id).toBe(subscription.id)
      expect(response.body.customer.id).toBe(customer.id)
      expect(response.body.plan.id).toBe(plan.id)
      expect(response.body.addons).toHaveLength(1)
      expect(response.body.addons[0].addon.id).toBe(addon.id)
      expect(response.body.payments).toHaveLength(1)
    })

    it('should return 404 for non-existent subscription', async () => {
      const response = await request(app).get('/api/checkout/subscription/non-existent-id')

      expect(response.status).toBe(404)
      expect(response.body.error).toBe('Subscription not found')
    })
  })
})