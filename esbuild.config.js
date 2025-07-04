import esbuild from 'esbuild'

await esbuild.build({
  entryPoints: ['src/lambda.ts'],
  bundle: true,
  outfile: 'dist/lambda.js',
  platform: 'node',
  target: 'node20',
  format: 'esm',
  sourcemap: true,
  external: [
    // Don't bundle native modules and AWS SDK
    'aws-sdk',
    '@aws-sdk/*',
    // Don't bundle Prisma engines
    '@prisma/engines',
    '@prisma/engines-version',
    './libquery_engine-*',
    './query_engine-*',
    // Don't bundle other native dependencies
    'sharp',
    'bcrypt'
  ],
  mainFields: ['module', 'main'],
  conditions: ['import', 'node'],
  resolveExtensions: ['.ts', '.js', '.json', '.node'],
  logLevel: 'info',
  loader: {
    '.node': 'file'
  }
})