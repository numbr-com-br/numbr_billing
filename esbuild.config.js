import esbuild from 'esbuild'

await esbuild.build({
  entryPoints: ['src/lambda.ts'],
  bundle: true,
  outfile: 'dist/lambda.js',
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