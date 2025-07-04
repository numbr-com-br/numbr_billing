import { configure } from '@vendia/serverless-express';
import { app } from './app';
let serverlessExpressInstance;
export const handler = async (event, context) => {
    if (!serverlessExpressInstance) {
        serverlessExpressInstance = configure({ app });
    }
    return serverlessExpressInstance(event, context);
};
//# sourceMappingURL=lambda-handler.js.map