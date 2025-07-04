export declare const dashboardHandler: () => Promise<{
    totalCustomers: number;
    activeSubscriptions: number;
    totalRevenue: number;
    pendingPayments: number;
    recentPayments: {
        id: string;
        customerName: string;
        planName: string;
        amount: number;
        paidAt: string;
    }[];
    mrr: number;
    metrics: {
        mrr: number;
        paymentCycles: Record<string, number>;
    };
}>;
export declare const Dashboard: {
    handler: () => Promise<{
        totalCustomers: number;
        activeSubscriptions: number;
        totalRevenue: number;
        pendingPayments: number;
        recentPayments: {
            id: string;
            customerName: string;
            planName: string;
            amount: number;
            paidAt: string;
        }[];
        mrr: number;
        metrics: {
            mrr: number;
            paymentCycles: Record<string, number>;
        };
    }>;
};
//# sourceMappingURL=dashboard.d.ts.map