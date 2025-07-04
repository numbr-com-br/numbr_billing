const { configure } = require('serverless-express');

let serverlessExpress;

async function getServerlessExpress() {
  if (!serverlessExpress) {
    const module = await import('./app.js');
    serverlessExpress = configure({ app: module.app });
  }
  return serverlessExpress;
}

module.exports.handler = async (event, context) => {
  const serverlessExpress = await getServerlessExpress();
  return serverlessExpress(event, context);
};