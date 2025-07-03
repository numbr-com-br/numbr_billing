// CommonJS wrapper for ES Module Lambda handler
exports.handler = async (event, context) => {
  const { handler } = await import('./lambda.js');
  return handler(event, context);
};