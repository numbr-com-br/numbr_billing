import { ComponentLoader } from 'adminjs'
import { prisma } from '../services/prisma.service.js'
import { SubscriptionStatus, PaymentStatus } from '@prisma/client'

export const dashboardHandler = async () => {
  const [
    totalCustomers,
    activeSubscriptions,
    totalRevenue,
    pendingPayments,
    recentPayments,
    subscriptionsByPlan,
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
      where: { status: PaymentStatus.RECEIVED },
      orderBy: { paidAt: 'desc' },
      take: 5,
      include: {
        subscription: {
          include: {
            customer: true,
            plan: true,
          },
        },
      },
    }),
    
    prisma.subscription.groupBy({
      by: ['planId', 'status'],
      _count: true,
    }),
  ])

  const planDetails = await prisma.plan.findMany({
    select: { id: true, name: true },
  })

  const planMap = Object.fromEntries(planDetails.map(p => [p.id, p.name]))

  const mrr = await calculateMRR()

  return {
    totalCustomers,
    activeSubscriptions,
    totalRevenue: totalRevenue._sum.amount || 0,
    pendingPayments,
    mrr,
    recentPayments: recentPayments.map(payment => ({
      id: payment.id,
      amount: payment.amount,
      paidAt: payment.paidAt,
      customerName: payment.subscription.customer.name,
      planName: payment.subscription.plan.name,
    })),
    subscriptionsByPlan: subscriptionsByPlan.map(item => ({
      planName: planMap[item.planId] || 'Unknown',
      status: item.status,
      count: item._count,
    })),
  }
}

async function calculateMRR(): Promise<number> {
  const activeSubscriptions = await prisma.subscription.findMany({
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

  let mrr = 0

  for (const subscription of activeSubscriptions) {
    let subscriptionValue = Number(subscription.plan.price)
    
    for (const subscriptionAddon of subscription.addons) {
      if (subscriptionAddon.addon.type === 'RECURRING') {
        subscriptionValue += Number(subscriptionAddon.addon.price) * subscriptionAddon.quantity
      }
    }

    switch (subscription.plan.cycle) {
      case 'WEEKLY':
        mrr += subscriptionValue * 4.33
        break
      case 'BIWEEKLY':
        mrr += subscriptionValue * 2.17
        break
      case 'MONTHLY':
        mrr += subscriptionValue
        break
      case 'QUARTERLY':
        mrr += subscriptionValue / 3
        break
      case 'SEMIANNUALLY':
        mrr += subscriptionValue / 6
        break
      case 'YEARLY':
        mrr += subscriptionValue / 12
        break
    }
  }

  return Math.round(mrr * 100) / 100
}

export const Dashboard = {
  component: ComponentLoader.add('Dashboard', `
    import React from 'react'
    import { Box, H2, H3, Text, Table, TableBody, TableCell, TableHead, TableRow } from '@adminjs/design-system'

    const Dashboard = ({ data }) => {
      return (
        <Box variant="grey" p="xl">
          <Box variant="white" boxShadow="card" p="xl" mb="xl">
            <H2 mb="lg">Dashboard</H2>
            
            <Box display="grid" gridTemplateColumns="repeat(auto-fit, minmax(200px, 1fr))" gap="lg" mb="xl">
              <Box variant="grey" p="lg" borderRadius="lg">
                <Text variant="sm" color="grey60">Total de Clientes</Text>
                <H3>{data.totalCustomers}</H3>
              </Box>
              
              <Box variant="grey" p="lg" borderRadius="lg">
                <Text variant="sm" color="grey60">Assinaturas Ativas</Text>
                <H3>{data.activeSubscriptions}</H3>
              </Box>
              
              <Box variant="grey" p="lg" borderRadius="lg">
                <Text variant="sm" color="grey60">MRR</Text>
                <H3>R$ {data.mrr.toLocaleString('pt-BR', { minimumFractionDigits: 2 })}</H3>
              </Box>
              
              <Box variant="grey" p="lg" borderRadius="lg">
                <Text variant="sm" color="grey60">Receita Total</Text>
                <H3>R$ {Number(data.totalRevenue).toLocaleString('pt-BR', { minimumFractionDigits: 2 })}</H3>
              </Box>
              
              <Box variant="grey" p="lg" borderRadius="lg">
                <Text variant="sm" color="grey60">Pagamentos Pendentes</Text>
                <H3>{data.pendingPayments}</H3>
              </Box>
            </Box>
          </Box>
          
          <Box variant="white" boxShadow="card" p="xl">
            <H3 mb="lg">Pagamentos Recentes</H3>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>Cliente</TableCell>
                  <TableCell>Plano</TableCell>
                  <TableCell>Valor</TableCell>
                  <TableCell>Data</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {data.recentPayments.map(payment => (
                  <TableRow key={payment.id}>
                    <TableCell>{payment.customerName}</TableCell>
                    <TableCell>{payment.planName}</TableCell>
                    <TableCell>R$ {Number(payment.amount).toLocaleString('pt-BR', { minimumFractionDigits: 2 })}</TableCell>
                    <TableCell>{new Date(payment.paidAt).toLocaleDateString('pt-BR')}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </Box>
        </Box>
      )
    }

    export default Dashboard
  `),
  handler: dashboardHandler,
}