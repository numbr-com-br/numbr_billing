# Numbr Billing

Sistema de cobrança SaaS com integração Asaas, desenvolvido em Python com FastAPI.

## Stack Tecnológica

- **FastAPI**: Framework web moderno e rápido
- **SQLAlchemy 2.0**: ORM com suporte async
- **Alembic**: Migrations de banco de dados
- **Pydantic**: Validação de dados
- **httpx**: Cliente HTTP async
- **AWS Lambda**: Deploy serverless com Mangum

## Instalação

```bash
# Instalar Poetry
curl -sSL https://install.python-poetry.org | python3 -

# Instalar dependências
poetry install

# Copiar arquivo de ambiente
cp .env.example .env
# Editar .env com suas configurações
```

## Desenvolvimento

```bash
# Ativar ambiente virtual
poetry shell

# Executar migrations
alembic upgrade head

# Rodar servidor de desenvolvimento
poetry run python -m src.main

# Ou com uvicorn diretamente
uvicorn src.main:app --reload --port 3000
```

## Migrations

```bash
# Criar nova migration
alembic revision --autogenerate -m "descrição da mudança"

# Aplicar migrations
alembic upgrade head

# Reverter última migration
alembic downgrade -1
```

## Testes

```bash
# Rodar todos os testes
poetry run pytest

# Rodar com coverage
poetry run pytest --cov=src
```

## Deploy

```bash
# Instalar dependências do serverless
npm install

# Deploy para dev
npm run deploy:dev

# Deploy para produção
npm run deploy:prod
```

## Estrutura do Projeto

```
src/
├── main.py           # App FastAPI principal
├── lambda_handler.py # Handler AWS Lambda
├── config.py         # Configurações
├── database.py       # Conexão com banco
├── enums.py          # Enumerações
├── models/           # Modelos SQLAlchemy
├── schemas/          # Schemas Pydantic
├── services/         # Serviços externos (Asaas)
└── routers/          # Rotas da API
```

## API Endpoints

### Checkout
- `GET /api/checkout/plans` - Listar planos disponíveis
- `GET /api/checkout/addons` - Listar addons disponíveis  
- `POST /api/checkout/start` - Iniciar processo de checkout

### Webhooks
- `POST /webhooks/asaas` - Receber webhooks do Asaas

### Health Check
- `GET /health` - Verificar status da aplicação