const serverlessExpress = require('@codegenie/serverless-express');

let cachedServer;

async function bootstrapServer() {
  if (!cachedServer) {
    const { app } = await import('./app.js');
    cachedServer = serverlessExpress({ app });
  }
  return cachedServer;
}

module.exports.handler = async (event, context) => {
  const server = await bootstrapServer();
  return server(event, context);
};