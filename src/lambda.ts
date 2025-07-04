const { configure } = require('serverless-express')
import { app } from './app'

export const handler = configure({ app })