import axios from 'axios';
import { config } from '../config/env';
class AsaasService {
    api;
    constructor() {
        this.api = axios.create({
            baseURL: config.asaas.apiUrl,
            headers: {
                'Content-Type': 'application/json',
                access_token: config.asaas.apiKey,
            },
        });
    }
    async createCustomer(data) {
        const response = await this.api.post('/customers', data);
        return response.data;
    }
    async getCustomer(id) {
        const response = await this.api.get(`/customers/${id}`);
        return response.data;
    }
    async createSubscription(data) {
        const response = await this.api.post('/subscriptions', data);
        return response.data;
    }
    async getSubscription(id) {
        const response = await this.api.get(`/subscriptions/${id}`);
        return response.data;
    }
    async cancelSubscription(id) {
        await this.api.delete(`/subscriptions/${id}`);
    }
    async getPayment(id) {
        const response = await this.api.get(`/payments/${id}`);
        return response.data;
    }
    async getSubscriptionPayments(subscriptionId) {
        const response = await this.api.get(`/subscriptions/${subscriptionId}/payments`);
        return response.data.data || [];
    }
    async createPaymentLink(data) {
        const response = await this.api.post('/payments', data);
        return response.data;
    }
    async getPaymentLink(paymentId) {
        const payment = await this.getPayment(paymentId);
        return payment.invoiceUrl || payment.boletoUrl || '';
    }
}
export const asaasService = new AsaasService();
//# sourceMappingURL=asaas.service.js.map