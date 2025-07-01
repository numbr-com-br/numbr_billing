import express from 'express'
import AdminJS from 'adminjs'
import AdminJSExpress from '@adminjs/express'
import session from 'express-session'
import { Database, Resource, getModelByName } from '@adminjs/prisma'
import { DMMFClass } from '@prisma/client/runtime/library'

import { config, validateEnv } from './config/env.js'
import { prisma, connectDatabase } from './services/prisma.service.js'
import { setupAdminResources } from './admin/resources.js'
import { webhookRouter } from './webhooks/asaas.webhook.js'
import { checkoutRouter } from './routes/checkout.route.js'
import { Dashboard } from './admin/dashboard.js'

validateEnv()

AdminJS.registerAdapter({ Database, Resource })

export const app = express()

app.use(express.json())
app.use(express.urlencoded({ extended: true }))

app.use('/webhooks', webhookRouter)
app.use('/api/checkout', checkoutRouter)

const setupApp = async () => {
  await connectDatabase()

  const dmmf = (prisma as any)._dmmf as DMMFClass

  const admin = new AdminJS({
    resources: setupAdminResources(dmmf),
    rootPath: '/admin',
    dashboard: Dashboard,
    branding: {
      companyName: 'Numbr Billing',
      logo: false,
      theme: {
        colors: {
          primary100: '#4B5563',
          primary80: '#6B7280',
          primary60: '#9CA3AF',
          primary40: '#D1D5DB',
          primary20: '#F3F4F6',
          grey100: '#374151',
          grey80: '#6B7280',
          grey60: '#9CA3AF',
          grey40: '#D1D5DB',
          grey20: '#F3F4F6',
          filterBg: '#F9FAFB',
          accent: '#3B82F6',
          hoverBg: '#EBF5FF',
        },
      },
    },
  })

  const adminRouter = AdminJSExpress.buildAuthenticatedRouter(
    admin,
    {
      authenticate: async (email, password) => {
        if (email === config.admin.email && password === config.admin.password) {
          return { email }
        }
        return null
      },
      cookieName: 'adminjs',
      cookiePassword: 'session-secret-numbr-billing-2024',
    },
    null,
    {
      store: session.MemoryStore ? new session.MemoryStore() : undefined,
      resave: true,
      saveUninitialized: true,
      secret: 'session-secret-numbr-billing-2024',
      cookie: {
        httpOnly: true,
        secure: false,
      },
    }
  )
  
  app.use(admin.options.rootPath, adminRouter)

  app.get('/health', (req, res) => {
    res.json({ status: 'ok', timestamp: new Date().toISOString() })
  })
}

// Setup app
setupApp().catch((error) => {
  console.error('Failed to setup app:', error)
  if (!process.env.IS_LAMBDA) {
    process.exit(1)
  }
})

// Only start server if not running in Lambda
if (!process.env.IS_LAMBDA) {
  app.listen(config.port, () => {
    console.log(`Server running on http://localhost:${config.port}`)
    console.log(`AdminJS panel available at http://localhost:${config.port}/admin`)
  })
}