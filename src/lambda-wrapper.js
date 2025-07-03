// CommonJS wrapper for ES modules
const serverless = require('serverless-http');

let app;

// Lazy load the app to handle ES modules
async function getApp() {
  if (!app) {
    const module = await import('./app.js');
    app = module.app;
  }
  return app;
}

module.exports.handler = async (event, context) => {
  const app = await getApp();
  const handler = serverless(app);
  return handler(event, context);
};