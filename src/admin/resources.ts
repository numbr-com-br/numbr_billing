import { DMMF } from '@prisma/client/runtime/library'
import { ResourceWithOptions } from 'adminjs'
import { prisma } from '../services/prisma.service.js'

export function setupAdminResources(dmmf: DMMF.Document): ResourceWithOptions[] {
  return [
    {
      resource: { model: dmmf.modelMap.Plan, client: prisma },
      options: {
        navigation: {
          name: 'Billing',
          icon: 'CreditCard',
        },
        listProperties: ['name', 'price', 'cycle', 'isActive', 'createdAt'],
        filterProperties: ['name', 'cycle', 'isActive'],
        editProperties: ['name', 'description', 'price', 'cycle', 'features', 'isActive'],
        showProperties: ['id', 'name', 'description', 'price', 'cycle', 'features', 'isActive', 'createdAt', 'updatedAt'],
        properties: {
          price: {
            type: 'number',
            props: {
              step: 0.01,
            },
          },
          features: {
            type: 'mixed',
            components: {
              edit: '@adminjs/design-system/src/molecules/property-json/property-json-editor.tsx',
            },
          },
          description: {
            type: 'textarea',
            props: {
              rows: 4,
            },
          },
        },
      },
    },
    {
      resource: { model: dmmf.modelMap.Addon, client: prisma },
      options: {
        navigation: {
          name: 'Billing',
          icon: 'Plus',
        },
        listProperties: ['name', 'price', 'type', 'isActive', 'createdAt'],
        filterProperties: ['name', 'type', 'isActive'],
        editProperties: ['name', 'description', 'price', 'type', 'isActive'],
        showProperties: ['id', 'name', 'description', 'price', 'type', 'isActive', 'createdAt', 'updatedAt'],
        properties: {
          price: {
            type: 'number',
            props: {
              step: 0.01,
            },
          },
          description: {
            type: 'textarea',
            props: {
              rows: 4,
            },
          },
        },
      },
    },
    {
      resource: { model: dmmf.modelMap.Customer, client: prisma },
      options: {
        navigation: {
          name: 'Customers',
          icon: 'User',
        },
        listProperties: ['name', 'email', 'phone', 'asaasCustomerId', 'createdAt'],
        filterProperties: ['name', 'email', 'phone'],
        editProperties: ['name', 'email', 'phone', 'cpfCnpj'],
        showProperties: ['id', 'name', 'email', 'phone', 'cpfCnpj', 'asaasCustomerId', 'createdAt', 'updatedAt'],
      },
    },
    {
      resource: { model: dmmf.modelMap.Subscription, client: prisma },
      options: {
        navigation: {
          name: 'Subscriptions',
          icon: 'Calendar',
        },
        listProperties: ['customer', 'plan', 'status', 'startDate', 'nextDueDate'],
        filterProperties: ['status', 'startDate'],
        editProperties: ['status', 'nextDueDate', 'canceledAt'],
        showProperties: ['id', 'customer', 'plan', 'asaasSubscriptionId', 'status', 'startDate', 'nextDueDate', 'canceledAt', 'createdAt', 'updatedAt'],
      },
    },
    {
      resource: { model: dmmf.modelMap.Payment, client: prisma },
      options: {
        navigation: {
          name: 'Payments',
          icon: 'Cash',
        },
        listProperties: ['subscription', 'amount', 'status', 'dueDate', 'paidAt'],
        filterProperties: ['status', 'dueDate', 'paidAt'],
        showProperties: ['id', 'subscription', 'amount', 'status', 'asaasPaymentId', 'dueDate', 'paidAt', 'paymentLink', 'billingType', 'invoiceNumber', 'description', 'createdAt'],
        actions: {
          new: { isVisible: false },
          edit: { isVisible: false },
          delete: { isVisible: false },
        },
        properties: {
          amount: {
            type: 'number',
            props: {
              step: 0.01,
            },
          },
        },
      },
    },
    {
      resource: { model: dmmf.modelMap.WebhookLog, client: prisma },
      options: {
        navigation: {
          name: 'System',
          icon: 'Terminal',
        },
        listProperties: ['event', 'success', 'processedAt'],
        filterProperties: ['event', 'success', 'processedAt'],
        showProperties: ['id', 'event', 'payload', 'success', 'error', 'processedAt'],
        actions: {
          new: { isVisible: false },
          edit: { isVisible: false },
          delete: { isVisible: false },
        },
        properties: {
          payload: {
            type: 'mixed',
          },
        },
      },
    },
  ]
}