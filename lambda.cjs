// CommonJS wrapper for Lambda
module.exports.handler = async (event, context) => {
  const { handler } = await import('./dist/lambda.js');
  return handler(event, context);
};