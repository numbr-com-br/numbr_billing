import { Router } from 'express'
import { prisma } from '../services/prisma.service.js'
import { config } from '../config/env.js'
import { PaymentStatus, SubscriptionStatus } from '@prisma/client'

export const webhookRouter = Router()

interface AsaasWebhookPayload {
  event: string
  payment?: {
    id: string
    customer: string
    subscription?: string
    value: number
    netValue: number
    status: string
    billingType: string
    confirmedDate?: string
    paymentDate?: string
    dueDate: string
    invoiceUrl?: string
    invoiceNumber?: string
    externalReference?: string
    description?: string
  }
  subscription?: {
    id: string
    customer: string
    value: number
    nextDueDate: string
    cycle: string
    status: string
  }
}

const paymentStatusMap: Record<string, PaymentStatus> = {
  PENDING: PaymentStatus.PENDING,
  RECEIVED: PaymentStatus.RECEIVED,
  CONFIRMED: PaymentStatus.CONFIRMED,
  OVERDUE: PaymentStatus.OVERDUE,
  REFUNDED: PaymentStatus.REFUNDED,
  RECEIVED_IN_CASH: PaymentStatus.RECEIVED,
  REFUND_REQUESTED: PaymentStatus.REFUNDED,
  CHARGEBACK_REQUESTED: PaymentStatus.FAILED,
  CHARGEBACK_DISPUTE: PaymentStatus.FAILED,
  AWAITING_CHARGEBACK_REVERSAL: PaymentStatus.FAILED,
  DUNNING_REQUESTED: PaymentStatus.OVERDUE,
  DUNNING_RECEIVED: PaymentStatus.RECEIVED,
  AWAITING_RISK_ANALYSIS: PaymentStatus.PENDING,
}

webhookRouter.post('/asaas', async (req, res): Promise<void> => {
  const webhookToken = req.headers['asaas-access-token']

  if (webhookToken !== config.asaas.webhookToken) {
    res.status(401).json({ error: 'Unauthorized' })
    return
  }

  const payload: AsaasWebhookPayload = req.body

  try {
    await prisma.webhookLog.create({
      data: {
        event: payload.event,
        payload: payload as any,
        success: true,
      },
    })

    switch (payload.event) {
      case 'PAYMENT_CREATED':
        await handlePaymentCreated(payload)
        break

      case 'PAYMENT_UPDATED':
        await handlePaymentUpdated(payload)
        break

      case 'PAYMENT_CONFIRMED':
      case 'PAYMENT_RECEIVED':
        await handlePaymentReceived(payload)
        break

      case 'PAYMENT_OVERDUE':
        await handlePaymentOverdue(payload)
        break

      case 'PAYMENT_DELETED':
        await handlePaymentDeleted(payload)
        break

      case 'PAYMENT_REFUNDED':
        await handlePaymentRefunded(payload)
        break

      default:
        console.log(`Unhandled webhook event: ${payload.event}`)
    }

    res.status(200).json({ success: true })
  } catch (error) {
    console.error('Webhook processing error:', error)

    await prisma.webhookLog.create({
      data: {
        event: payload.event,
        payload: payload as any,
        success: false,
        error: error instanceof Error ? error.message : 'Unknown error',
      },
    })

    res.status(500).json({ error: 'Internal server error' })
  }
})

async function handlePaymentCreated(payload: AsaasWebhookPayload) {
  if (!payload.payment) return

  const { payment } = payload

  if (payment.subscription) {
    const subscription = await prisma.subscription.findUnique({
      where: { asaasSubscriptionId: payment.subscription },
    })

    if (subscription) {
      await prisma.payment.create({
        data: {
          subscriptionId: subscription.id,
          asaasPaymentId: payment.id,
          amount: payment.value,
          status: paymentStatusMap[payment.status] || PaymentStatus.PENDING,
          dueDate: new Date(payment.dueDate),
          billingType: payment.billingType,
          invoiceNumber: payment.invoiceNumber,
          externalReference: payment.externalReference,
          description: payment.description,
          paymentLink: payment.invoiceUrl,
        },
      })
    }
  }
}

async function handlePaymentUpdated(payload: AsaasWebhookPayload) {
  if (!payload.payment) return

  const { payment } = payload

  await prisma.payment.updateMany({
    where: { asaasPaymentId: payment.id },
    data: {
      status: paymentStatusMap[payment.status] || PaymentStatus.PENDING,
      paymentLink: payment.invoiceUrl,
    },
  })
}

async function handlePaymentReceived(payload: AsaasWebhookPayload) {
  if (!payload.payment) return

  const { payment } = payload

  await prisma.payment.updateMany({
    where: { asaasPaymentId: payment.id },
    data: {
      status: PaymentStatus.RECEIVED,
      paidAt: payment.paymentDate ? new Date(payment.paymentDate) : new Date(),
    },
  })

  if (payment.subscription) {
    await prisma.subscription.updateMany({
      where: { asaasSubscriptionId: payment.subscription },
      data: { status: SubscriptionStatus.ACTIVE },
    })
  }
}

async function handlePaymentOverdue(payload: AsaasWebhookPayload) {
  if (!payload.payment) return

  const { payment } = payload

  await prisma.payment.updateMany({
    where: { asaasPaymentId: payment.id },
    data: {
      status: PaymentStatus.OVERDUE,
    },
  })
}

async function handlePaymentDeleted(payload: AsaasWebhookPayload) {
  if (!payload.payment) return

  const { payment } = payload

  await prisma.payment.updateMany({
    where: { asaasPaymentId: payment.id },
    data: {
      status: PaymentStatus.FAILED,
    },
  })
}

async function handlePaymentRefunded(payload: AsaasWebhookPayload) {
  if (!payload.payment) return

  const { payment } = payload

  await prisma.payment.updateMany({
    where: { asaasPaymentId: payment.id },
    data: {
      status: PaymentStatus.REFUNDED,
    },
  })
}