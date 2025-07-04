import express from 'express'
import AdminJS from 'adminjs'
import AdminJSExpress from '@adminjs/express'
import session from 'express-session'
// @ts-ignore
import { Database, Resource } from '@adminjs/prisma'

import { config, validateEnv } from './config/env'
import { prisma, connectDatabase } from './services/prisma.service'
import { setupAdminResources } from './admin/resources'
import { webhookRouter } from './webhooks/asaas.webhook'
import { checkoutRouter } from './routes/checkout.route'
import { Dashboard } from './admin/dashboard'

validateEnv()

AdminJS.registerAdapter({ Database, Resource })

export const app = express()

app.use(express.json())
app.use(express.urlencoded({ extended: true }))

app.use('/webhooks', webhookRouter)
app.use('/api/checkout', checkoutRouter)

const setupApp = async () => {
  await connectDatabase()

  // Add health check endpoint
  app.get('/health', (_req, res) => {
    res.json({ status: 'ok', timestamp: new Date().toISOString() })
  })

  // Import Prisma client to get DMMF
  const PrismaClient = await import('@prisma/client')
  const dmmf = (PrismaClient as any).Prisma?.dmmf
  
  if (!dmmf || !dmmf.datamodel) {
    throw new Error('Unable to get DMMF from Prisma - no datamodel found')
  }

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
}

// Setup app
const appSetupPromise = setupApp().catch((error) => {
  console.error('Failed to setup app:', error)
  if (!process.env.IS_LAMBDA) {
    process.exit(1)
  }
})

// Export the setup promise so Lambda can wait for it
export { appSetupPromise }

// Only start server if not running in Lambda
if (!process.env.IS_LAMBDA) {
  app.listen(config.port, () => {
    console.log(`Server running on http://localhost:${config.port}`)
    console.log(`AdminJS panel available at http://localhost:${config.port}/admin`)
  })
}