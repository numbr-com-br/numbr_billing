import { prisma } from '../services/prisma.service';
export function setupAdminResources(dmmf) {
    const models = dmmf.datamodel.models.reduce((acc, model) => {
        acc[model.name] = model;
        return acc;
    }, {});
    return [
        {
            resource: { model: models.Plan, client: prisma },
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
            resource: { model: models.Addon, client: prisma },
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
            resource: { model: models.Customer, client: prisma },
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
            resource: { model: models.Subscription, client: prisma },
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
            resource: { model: models.Payment, client: prisma },
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
            resource: { model: models.WebhookLog, client: prisma },
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
    ];
}
//# sourceMappingURL=resources.js.map