import { prisma } from '../src/services/prisma.service'

beforeAll(async () => {
  await prisma.$connect()
})

afterAll(async () => {
  await prisma.$disconnect()
})

afterEach(async () => {
  const tables = await prisma.$queryRaw<
    Array<{ TABLE_NAME: string }>
  >`SELECT TABLE_NAME FROM information_schema.tables WHERE table_schema = DATABASE() AND table_type = 'BASE TABLE'`

  const tableNames = tables
    .map(({ TABLE_NAME }) => TABLE_NAME)
    .filter((name) => name !== '_prisma_migrations')

  for (const tableName of tableNames) {
    await prisma.$executeRawUnsafe(`SET FOREIGN_KEY_CHECKS = 0;`)
    await prisma.$executeRawUnsafe(`TRUNCATE TABLE \`${tableName}\`;`)
    await prisma.$executeRawUnsafe(`SET FOREIGN_KEY_CHECKS = 1;`)
  }
})