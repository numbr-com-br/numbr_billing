import React from 'react';
import { Box, H2, H3, Text, Table, TableBody, TableCell, TableHead, TableRow } from '@adminjs/design-system';
const Dashboard = ({ data }) => {
    return (<Box variant="grey" p="xl">
      <Box mb="xl">
        <H2>Dashboard</H2>
      </Box>

      <Box flex flexWrap="wrap" mb="xl">
        <Box width={[1, 1 / 2, 1 / 4]} p="lg">
          <Box variant="white" p="xl">
            <H3>Total Customers</H3>
            <Text fontSize="xl" fontWeight="bold">{data.totalCustomers}</Text>
          </Box>
        </Box>

        <Box width={[1, 1 / 2, 1 / 4]} p="lg">
          <Box variant="white" p="xl">
            <H3>Active Subscriptions</H3>
            <Text fontSize="xl" fontWeight="bold">{data.activeSubscriptions}</Text>
          </Box>
        </Box>

        <Box width={[1, 1 / 2, 1 / 4]} p="lg">
          <Box variant="white" p="xl">
            <H3>Total Revenue</H3>
            <Text fontSize="xl" fontWeight="bold">R$ {data.totalRevenue.toFixed(2)}</Text>
          </Box>
        </Box>

        <Box width={[1, 1 / 2, 1 / 4]} p="lg">
          <Box variant="white" p="xl">
            <H3>Pending Payments</H3>
            <Text fontSize="xl" fontWeight="bold">{data.pendingPayments}</Text>
          </Box>
        </Box>
      </Box>

      <Box mb="xl">
        <Box variant="white" p="xl">
          <H3 mb="lg">Metrics</H3>
          <Box flex>
            <Box mr="xl">
              <Text>Monthly Recurring Revenue (MRR)</Text>
              <Text fontSize="lg" fontWeight="bold">R$ {data.metrics.mrr.toFixed(2)}</Text>
            </Box>
            <Box>
              <Text>Payment Distribution</Text>
              {Object.entries(data.metrics.paymentCycles).map(([cycle, count]) => (<Text key={cycle}>{cycle}: {count}</Text>))}
            </Box>
          </Box>
        </Box>
      </Box>

      <Box variant="white" p="xl">
        <H3 mb="lg">Recent Payments</H3>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>Customer</TableCell>
              <TableCell>Amount</TableCell>
              <TableCell>Status</TableCell>
              <TableCell>Date</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {data.recentPayments.map((payment) => (<TableRow key={payment.id}>
                <TableCell>{payment.customer.name}</TableCell>
                <TableCell>R$ {payment.amount}</TableCell>
                <TableCell>{payment.status}</TableCell>
                <TableCell>{new Date(payment.createdAt).toLocaleDateString()}</TableCell>
              </TableRow>))}
          </TableBody>
        </Table>
      </Box>
    </Box>);
};
export default Dashboard;
//# sourceMappingURL=Dashboard.js.map