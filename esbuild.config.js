import esbuild from 'esbuild'

// Build lambda.ts for Lambda (CommonJS for compatibility with Prisma)
await esbuild.build({
  entryPoints: ['src/lambda.ts'],
  bundle: true,
  outfile: 'dist/lambda.js',
  platform: 'node',
  target: 'node20',
  format: 'cjs',
  sourcemap: true,
  packages: 'external',
  mainFields: ['main', 'module'],
  resolveExtensions: ['.ts', '.js', '.json', '.node'],
  logLevel: 'info'
})

// Also build app.ts for local development (ES modules)
await esbuild.build({
  entryPoints: ['src/app.ts'],
  bundle: true,
  outfile: 'dist/app.js',
  platform: 'node',
  target: 'node20',
  format: 'esm',
  sourcemap: true,
  packages: 'external',
  mainFields: ['module', 'main'],
  conditions: ['import', 'node'],
  resolveExtensions: ['.ts', '.js', '.json', '.node'],
  logLevel: 'info'
})