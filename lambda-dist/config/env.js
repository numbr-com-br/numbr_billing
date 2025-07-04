import dotenv from 'dotenv';
dotenv.config();
export const config = {
    port: parseInt(process.env.PORT || '3000', 10),
    database: {
        url: process.env.DATABASE_URL || '',
    },
    asaas: {
        apiKey: process.env.ASAAS_API_KEY || '',
        apiUrl: process.env.ASAAS_API_URL || 'https://sandbox.asaas.com/api/v3',
        webhookToken: process.env.ASAAS_WEBHOOK_TOKEN || '',
    },
    admin: {
        email: process.env.ADMIN_EMAIL || 'admin@numbr.com',
        password: process.env.ADMIN_PASSWORD || 'admin123',
    },
};
export function validateEnv() {
    const required = ['DATABASE_URL', 'ASAAS_API_KEY'];
    const missing = required.filter((key) => !process.env[key]);
    if (missing.length > 0) {
        throw new Error(`Missing required environment variables: ${missing.join(', ')}`);
    }
}
//# sourceMappingURL=env.js.map