import { Router } from 'express'
import { prisma } from '../services/prisma.service.js'
import { asaasService } from '../services/asaas.service.js'
import { BillingCycle } from '@prisma/client'

export const checkoutRouter = Router()

interface CheckoutRequest {
  planId: string
  addonIds?: string[]
  customer: {
    name: string
    email: string
    cpfCnpj?: string
    phone?: string
  }
  billingType: 'BOLETO' | 'CREDIT_CARD' | 'PIX'
}

checkoutRouter.post('/start', async (req, res) => {
  try {
    const { planId, addonIds = [], customer, billingType } = req.body as CheckoutRequest

    const plan = await prisma.plan.findUnique({
      where: { id: planId, isActive: true },
    })

    if (!plan) {
      return res.status(404).json({ error: 'Plan not found or inactive' })
    }

    const addons = addonIds.length > 0
      ? await prisma.addon.findMany({
          where: { id: { in: addonIds }, isActive: true },
        })
      : []

    let existingCustomer = await prisma.customer.findUnique({
      where: { email: customer.email },
    })

    if (!existingCustomer) {
      const asaasCustomer = await asaasService.createCustomer(customer)

      existingCustomer = await prisma.customer.create({
        data: {
          ...customer,
          asaasCustomerId: asaasCustomer.id,
        },
      })
    } else if (!existingCustomer.asaasCustomerId) {
      const asaasCustomer = await asaasService.createCustomer({
        name: existingCustomer.name,
        email: existingCustomer.email,
        cpfCnpj: existingCustomer.cpfCnpj || undefined,
        phone: existingCustomer.phone || undefined,
      })

      existingCustomer = await prisma.customer.update({
        where: { id: existingCustomer.id },
        data: { asaasCustomerId: asaasCustomer.id },
      })
    }

    const totalValue = Number(plan.price) + addons.reduce((sum, addon) => sum + Number(addon.price), 0)

    const nextDueDate = new Date()
    nextDueDate.setDate(nextDueDate.getDate() + 7)

    const asaasSubscription = await asaasService.createSubscription({
      customer: existingCustomer.asaasCustomerId!,
      billingType,
      value: totalValue,
      nextDueDate: nextDueDate.toISOString().split('T')[0],
      cycle: plan.cycle,
      description: `Assinatura ${plan.name}`,
    })

    const subscription = await prisma.subscription.create({
      data: {
        customerId: existingCustomer.id,
        planId: plan.id,
        asaasSubscriptionId: asaasSubscription.id,
        status: 'PENDING',
        startDate: new Date(),
        nextDueDate,
      },
    })

    if (addons.length > 0) {
      await prisma.subscriptionAddon.createMany({
        data: addons.map((addon) => ({
          subscriptionId: subscription.id,
          addonId: addon.id,
          quantity: 1,
        })),
      })
    }

    const paymentLink = await asaasService.createPaymentLink({
      customer: existingCustomer.asaasCustomerId!,
      billingType,
      value: totalValue,
      dueDate: nextDueDate.toISOString().split('T')[0],
      description: `Primeira cobrança - ${plan.name}`,
    })

    res.json({
      success: true,
      subscriptionId: subscription.id,
      paymentUrl: paymentLink.invoiceUrl || paymentLink.boletoUrl,
      paymentId: paymentLink.id,
    })
  } catch (error) {
    console.error('Checkout error:', error)
    res.status(500).json({ error: 'Failed to process checkout' })
  }
})

checkoutRouter.get('/plans', async (req, res) => {
  try {
    const plans = await prisma.plan.findMany({
      where: { isActive: true },
      orderBy: { price: 'asc' },
    })

    const addons = await prisma.addon.findMany({
      where: { isActive: true },
      orderBy: { price: 'asc' },
    })

    res.json({ plans, addons })
  } catch (error) {
    console.error('Error fetching plans:', error)
    res.status(500).json({ error: 'Failed to fetch plans' })
  }
})

checkoutRouter.get('/subscription/:id', async (req, res) => {
  try {
    const subscription = await prisma.subscription.findUnique({
      where: { id: req.params.id },
      include: {
        plan: true,
        customer: true,
        addons: {
          include: {
            addon: true,
          },
        },
        payments: {
          orderBy: { createdAt: 'desc' },
          take: 1,
        },
      },
    })

    if (!subscription) {
      return res.status(404).json({ error: 'Subscription not found' })
    }

    res.json(subscription)
  } catch (error) {
    console.error('Error fetching subscription:', error)
    res.status(500).json({ error: 'Failed to fetch subscription' })
  }
})