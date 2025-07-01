import { BillingCycle, AddonType, SubscriptionStatus, PaymentStatus } from '@prisma/client'
import { prisma } from '../../src/services/prisma.service'

export const PlanFactory = {
  build: (overrides = {}) => ({
    name: 'Test Plan',
    description: 'Test plan description',
    price: 99.99,
    cycle: BillingCycle.MONTHLY,
    features: ['Feature 1', 'Feature 2'],
    isActive: true,
    ...overrides,
  }),

  create: async (overrides = {}) => {
    const data = PlanFactory.build(overrides)
    return await prisma.plan.create({ data })
  },
}

export const AddonFactory = {
  build: (overrides = {}) => ({
    name: 'Test Addon',
    description: 'Test addon description',
    price: 19.99,
    type: AddonType.RECURRING,
    isActive: true,
    ...overrides,
  }),

  create: async (overrides = {}) => {
    const data = AddonFactory.build(overrides)
    return await prisma.addon.create({ data })
  },
}

export const CustomerFactory = {
  build: (overrides = {}) => ({
    email: `test${Date.now()}@example.com`,
    name: 'Test Customer',
    phone: '11999999999',
    cpfCnpj: '12345678900',
    asaasCustomerId: `cus_${Date.now()}`,
    ...overrides,
  }),

  create: async (overrides = {}) => {
    const data = CustomerFactory.build(overrides)
    return await prisma.customer.create({ data })
  },
}

export const SubscriptionFactory = {
  build: (overrides: any = {}) => ({
    status: SubscriptionStatus.ACTIVE,
    startDate: new Date(),
    nextDueDate: new Date(Date.now() + 30 * 24 * 60 * 60 * 1000),
    asaasSubscriptionId: `sub_${Date.now()}`,
    ...overrides,
  }),

  create: async (overrides: any = {}) => {
    const { customerId, planId, ...rest } = overrides

    const customer = customerId 
      ? await prisma.customer.findUnique({ where: { id: customerId } })
      : await CustomerFactory.create()

    const plan = planId
      ? await prisma.plan.findUnique({ where: { id: planId } })
      : await PlanFactory.create()

    if (!customer || !plan) {
      throw new Error('Failed to create subscription: customer or plan not found')
    }

    const data = SubscriptionFactory.build({
      ...rest,
      customerId: customer.id,
      planId: plan.id,
    })

    return await prisma.subscription.create({
      data,
      include: { customer: true, plan: true },
    })
  },
}

export const PaymentFactory = {
  build: (overrides: any = {}) => ({
    amount: 99.99,
    status: PaymentStatus.PENDING,
    dueDate: new Date(Date.now() + 7 * 24 * 60 * 60 * 1000),
    asaasPaymentId: `pay_${Date.now()}`,
    ...overrides,
  }),

  create: async (overrides: any = {}) => {
    const { subscriptionId, ...rest } = overrides

    const subscription = subscriptionId
      ? await prisma.subscription.findUnique({ where: { id: subscriptionId } })
      : await SubscriptionFactory.create()

    if (!subscription) {
      throw new Error('Failed to create payment: subscription not found')
    }

    const data = PaymentFactory.build({
      ...rest,
      subscriptionId: subscription.id,
    })

    return await prisma.payment.create({
      data,
      include: { subscription: true },
    })
  },
}