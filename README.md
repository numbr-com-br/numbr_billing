# Numbr Billing - Sistema de Billing SaaS

Sistema de billing completo para SaaS com integração Asaas, painel administrativo e checkout transparente.

## Recursos

- ✅ Gestão de planos e módulos extras (add-ons)
- ✅ Integração completa com Asaas (assinaturas e pagamentos)
- ✅ Painel administrativo com AdminJS
- ✅ Dashboard com métricas (MRR, assinaturas ativas, etc)
- ✅ Webhook para notificações de pagamento
- ✅ API de checkout público
- ✅ Autenticação no painel admin
- ✅ Testes unitários e de integração

## Tecnologias

- Node.js + TypeScript
- Express.js
- Prisma ORM (MySQL)
- AdminJS
- Asaas API
- Jest + Supertest (Testes)

## Instalação

1. Clone o repositório
2. Instale as dependências:
```bash
npm install
```

3. Configure o banco de dados MySQL

4. Copie o arquivo `.env.example` para `.env` e configure:
```bash
cp .env.example .env
```

5. Configure as variáveis de ambiente:
- `DATABASE_URL`: URL de conexão do MySQL (ex: mysql://root:password@localhost:3306/numbr_billing)
- `ASAAS_API_KEY`: Chave da API do Asaas
- `ASAAS_API_URL`: URL da API do Asaas (sandbox ou produção)
- `ASAAS_WEBHOOK_TOKEN`: Token para validar webhooks
- `ADMIN_EMAIL` e `ADMIN_PASSWORD`: Credenciais do admin

6. Execute as migrations do Prisma:
```bash
npm run prisma:generate
npm run prisma:migrate
```

## Uso

### Desenvolvimento
```bash
npm run dev
```

### Produção
```bash
npm run build
npm start
```

### Acessar o painel admin
Acesse `http://localhost:3000/admin` com as credenciais configuradas no `.env`

### Testes

```bash
# Executar todos os testes
npm test

# Testes em modo watch
npm run test:watch

# Testes com cobertura
npm run test:coverage

# Apenas testes unitários
npm run test:unit

# Apenas testes de integração
npm run test:integration
```

**Importante**: Configure um banco MySQL separado para testes no arquivo `.env.test`

## API Endpoints

### Checkout Público
- `GET /api/checkout/plans` - Lista planos e add-ons disponíveis
- `POST /api/checkout/start` - Inicia processo de checkout
- `GET /api/checkout/subscription/:id` - Consulta status da assinatura

### Webhook
- `POST /webhooks/asaas` - Recebe notificações do Asaas

## Estrutura do Projeto

```
src/
├── admin/          # Configurações do AdminJS
├── config/         # Configurações e variáveis de ambiente
├── models/         # Modelos Prisma (definidos em prisma/schema.prisma)
├── routes/         # Rotas da API
├── services/       # Serviços (Asaas, Prisma)
├── webhooks/       # Handlers de webhook
└── app.ts          # Arquivo principal
```

## Fluxo de Checkout

1. Cliente seleciona plano e add-ons
2. Sistema cria/busca cliente no Asaas
3. Cria assinatura no Asaas
4. Gera link de pagamento
5. Cliente é redirecionado para checkout do Asaas
6. Webhook notifica sobre status do pagamento
7. Sistema atualiza status da assinatura

## Segurança

- Autenticação obrigatória no painel admin
- Validação de token nos webhooks
- Variáveis sensíveis em ambiente
- Sem exposição de chaves da API

## Deploy AWS

O projeto está configurado para deploy automático na AWS usando GitHub Actions, API Gateway e Lambda.

### Ambientes

- **develop** → Development (dev)
- **staging** → Staging (stg)
- **main** → Production (prod)

### Configuração GitHub Secrets

Configure os seguintes secrets no GitHub:

**Por ambiente (DEV, STG, PROD):**
- `AWS_ROLE_ARN_{ENV}` - ARN da role IAM para deploy
- `DATABASE_URL_{ENV}` - URL de conexão MySQL
- `ASAAS_API_KEY_{ENV}` - Chave API do Asaas
- `ASAAS_WEBHOOK_TOKEN_{ENV}` - Token validação webhook
- `ADMIN_EMAIL_{ENV}` - Email do admin
- `ADMIN_PASSWORD_{ENV}` - Senha do admin

**Globais:**
- `AWS_REGION` - Região AWS (ex: us-east-1)
- `AWS_ACCOUNT_ID` - ID da conta AWS

### Deploy Manual

Para fazer deploy manual:

```bash
# Build do Lambda
./scripts/build-lambda.sh dev

# Deploy CloudFormation
aws cloudformation deploy \
  --template-file cloudformation/template.yaml \
  --stack-name numbr-billing-dev \
  --parameter-overrides Environment=dev \
  --capabilities CAPABILITY_IAM
```

### Arquitetura AWS

- **API Gateway**: REST API com proxy para Lambda
- **Lambda Function**: Node.js 20.x com Express
- **Lambda Layer**: Dependências pesadas compartilhadas
- **CloudWatch Logs**: Logs centralizados
- **Secrets Manager**: Gerenciamento de credenciais

### URLs por Ambiente

Após o deploy, as URLs serão:
- Dev: `https://{api-id}.execute-api.{region}.amazonaws.com/dev`
- Staging: `https://{api-id}.execute-api.{region}.amazonaws.com/stg`
- Production: `https://{api-id}.execute-api.{region}.amazonaws.com/prod`

O painel admin estará disponível em: `{url}/admin`