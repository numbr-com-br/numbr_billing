"use strict";
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
exports.handler = void 0;
const express_1 = __importDefault(require("express"));
const serverless_http_1 = __importDefault(require("serverless-http"));
const asaas_webhook_1 = require("./webhooks/asaas.webhook");
const checkout_route_1 = require("./routes/checkout.route");
const prisma_service_1 = require("./services/prisma.service");
const app = (0, express_1.default)();
app.use(express_1.default.json());
app.use(express_1.default.urlencoded({ extended: true }));
// Routes
app.use('/webhooks', asaas_webhook_1.webhookRouter);
app.use('/api/checkout', checkout_route_1.checkoutRouter);
// Health check
app.get('/health', (_req, res) => {
    res.json({
        status: 'ok',
        timestamp: new Date().toISOString(),
        environment: process.env.NODE_ENV || 'production'
    });
});
// Initialize database connection
(0, prisma_service_1.connectDatabase)().catch(console.error);
exports.handler = (0, serverless_http_1.default)(app);
//# sourceMappingURL=lambda-simple.js.map