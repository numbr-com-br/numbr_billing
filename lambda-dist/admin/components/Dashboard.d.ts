import React from 'react';
interface DashboardData {
    totalCustomers: number;
    activeSubscriptions: number;
    totalRevenue: number;
    pendingPayments: number;
    recentPayments: Array<{
        id: string;
        customer: {
            name: string;
        };
        amount: number;
        status: string;
        createdAt: string;
    }>;
    metrics: {
        mrr: number;
        paymentCycles: Record<string, number>;
    };
}
declare const Dashboard: ({ data }: {
    data: DashboardData;
}) => React.JSX.Element;
export default Dashboard;
//# sourceMappingURL=Dashboard.d.ts.map