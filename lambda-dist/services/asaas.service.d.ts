export interface AsaasCustomer {
    id: string;
    name: string;
    email: string;
    cpfCnpj?: string;
    phone?: string;
}
export interface AsaasSubscription {
    id: string;
    customer: string;
    billingType: 'BOLETO' | 'CREDIT_CARD' | 'PIX';
    value: number;
    nextDueDate: string;
    cycle: 'WEEKLY' | 'BIWEEKLY' | 'MONTHLY' | 'QUARTERLY' | 'SEMIANNUALLY' | 'YEARLY';
    description?: string;
    status: string;
}
export interface AsaasPayment {
    id: string;
    customer: string;
    subscription?: string;
    value: number;
    dueDate: string;
    status: string;
    billingType: string;
    invoiceUrl?: string;
    boletoUrl?: string;
    pixQrCode?: string;
}
declare class AsaasService {
    private api;
    constructor();
    createCustomer(data: {
        name: string;
        email: string;
        cpfCnpj?: string;
        phone?: string;
    }): Promise<AsaasCustomer>;
    getCustomer(id: string): Promise<AsaasCustomer>;
    createSubscription(data: {
        customer: string;
        billingType: 'BOLETO' | 'CREDIT_CARD' | 'PIX';
        value: number;
        nextDueDate: string;
        cycle: string;
        description?: string;
    }): Promise<AsaasSubscription>;
    getSubscription(id: string): Promise<AsaasSubscription>;
    cancelSubscription(id: string): Promise<void>;
    getPayment(id: string): Promise<AsaasPayment>;
    getSubscriptionPayments(subscriptionId: string): Promise<AsaasPayment[]>;
    createPaymentLink(data: {
        customer: string;
        billingType: 'BOLETO' | 'CREDIT_CARD' | 'PIX';
        value: number;
        dueDate: string;
        description?: string;
    }): Promise<AsaasPayment>;
    getPaymentLink(paymentId: string): Promise<string>;
}
export declare const asaasService: AsaasService;
export {};
//# sourceMappingURL=asaas.service.d.ts.map