import { prisma } from '../services/prisma.service.js'
import { SubscriptionStatus, PaymentStatus } from '../generated/prisma/client.js'

export const dashboardHandler = async () => {
  const [
    totalCustomers,
    activeSubscriptions,
    totalRevenue,
    pendingPayments,
    recentPayments,
  ] = await Promise.all([
    prisma.customer.count(),
    prisma.subscription.count({
      where: { status: SubscriptionStatus.ACTIVE },
    }),
    prisma.payment.aggregate({
      where: { status: PaymentStatus.RECEIVED },
      _sum: { amount: true },
    }),
    prisma.payment.count({
      where: { status: PaymentStatus.PENDING },
    }),
    prisma.payment.findMany({
      where: { 
        status: PaymentStatus.RECEIVED,
        paidAt: { not: null } 
      },
      include: {
        subscription: {
          include: {
            customer: true,
            plan: true,
          },
        },
      },
      orderBy: { paidAt: 'desc' },
      take: 10,
    }),
  ])

  const subscriptions = await prisma.subscription.findMany({
    where: { status: SubscriptionStatus.ACTIVE },
    include: {
      plan: true,
      addons: {
        include: {
          addon: true,
        },
      },
    },
  })

  const metrics = {
    mrr: calculateMRR(subscriptions),
    paymentCycles: await getPaymentCycles(),
  }

  return {
    totalCustomers,
    activeSubscriptions,
    totalRevenue: Number(totalRevenue._sum.amount || 0),
    pendingPayments,
    recentPayments: recentPayments.map((payment) => ({
      id: payment.id,
      customerName: payment.subscription.customer.name,
      planName: payment.subscription.plan.name,
      amount: Number(payment.amount),
      paidAt: payment.paidAt!.toISOString(),
    })),
    mrr: metrics.mrr,
    metrics,
  }
}

async function getPaymentCycles() {
  const plans = await prisma.plan.groupBy({
    by: ['cycle'],
    _count: { cycle: true },
  })

  return plans.reduce((acc, item) => {
    acc[item.cycle] = item._count.cycle
    return acc
  }, {} as Record<string, number>)
}

function calculateMRR(subscriptions: any[]) {
  let mrr = 0

  for (const subscription of subscriptions) {
    const planPrice = Number(subscription.plan.price)
    const addonPrices = subscription.addons.reduce(
      (sum: number, sa: any) => sum + Number(sa.addon.price) * sa.quantity,
      0
    )
    const totalPrice = planPrice + addonPrices

    switch (subscription.plan.cycle) {
      case 'WEEKLY':
        mrr += totalPrice * 4.33
        break
      case 'BIWEEKLY':
        mrr += totalPrice * 2.17
        break
      case 'MONTHLY':
        mrr += totalPrice
        break
      case 'QUARTERLY':
        mrr += totalPrice / 3
        break
      case 'SEMIANNUALLY':
        mrr += totalPrice / 6
        break
      case 'YEARLY':
        mrr += totalPrice / 12
        break
    }
  }

  return Math.round(mrr * 100) / 100
}

// AdminJS dashboard configuration
export const Dashboard = {
  handler: dashboardHandler,
}