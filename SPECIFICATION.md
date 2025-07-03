# Especificação Funcional - Sistema de Billing SaaS

## 1. Visão Geral

Sistema completo de gerenciamento de assinaturas e pagamentos recorrentes para SaaS, permitindo a criação de planos flexíveis, addons complementares e gestão completa do ciclo de vida das assinaturas.

## 2. Modelos de Dados

### 2.1 Planos (Plans)

Os planos representam os produtos base oferecidos pelo sistema.

**Atributos:**
- **Nome**: Identificação do plano
- **Descrição**: Detalhamento do que o plano oferece
- **Preço**: Valor monetário do plano (suporta até 2 casas decimais)
- **Ciclo de Cobrança**: 
  - Semanal (WEEKLY)
  - Quinzenal (BIWEEKLY)
  - Mensal (MONTHLY)
  - Trimestral (QUARTERLY)
  - Semestral (SEMIANNUALLY)
  - Anual (YEARLY)
- **Features**: Lista de funcionalidades incluídas no plano (formato JSON)
- **Status**: Ativo ou Inativo

### 2.2 Addons

Recursos adicionais que podem ser contratados junto aos planos.

**Tipos de Addon:**
- **Recorrente (RECURRING)**: Cobrado em cada ciclo de faturamento
- **Único (ONE_TIME)**: Cobrado apenas uma vez na contratação

**Atributos:**
- **Nome**: Identificação do addon
- **Descrição**: Detalhamento do addon
- **Preço**: Valor monetário
- **Tipo**: Recorrente ou Único
- **Status**: Ativo ou Inativo

### 2.3 Clientes (Customers)

Informações dos contratantes dos serviços.

**Dados Armazenados:**
- **Nome Completo**
- **Email** (único no sistema)
- **Telefone** (opcional)
- **CPF/CNPJ** (opcional)
- **Data de Cadastro**

### 2.4 Assinaturas (Subscriptions)

Representa a contratação de um plano por um cliente.

**Estados da Assinatura:**
- **PENDING**: Aguardando confirmação do primeiro pagamento
- **ACTIVE**: Assinatura ativa e em dia
- **INACTIVE**: Assinatura pausada ou inativa temporariamente
- **CANCELED**: Assinatura cancelada pelo cliente ou administrador
- **EXPIRED**: Assinatura expirada por falta de pagamento

**Atributos:**
- **Cliente**: Referência ao cliente contratante
- **Plano**: Plano base contratado
- **Data de Início**: Quando a assinatura foi criada
- **Próximo Vencimento**: Data da próxima cobrança
- **Data de Cancelamento**: Quando foi cancelada (se aplicável)
- **Addons Associados**: Lista de addons contratados

### 2.5 Pagamentos (Payments)

Registro de todas as cobranças geradas pelo sistema.

**Estados do Pagamento:**
- **PENDING**: Aguardando pagamento
- **CONFIRMED**: Pagamento confirmado
- **RECEIVED**: Pagamento recebido
- **OVERDUE**: Pagamento vencido
- **REFUNDED**: Pagamento reembolsado
- **FAILED**: Pagamento falhou

**Tipos de Pagamento Suportados:**
- Boleto Bancário
- Cartão de Crédito
- PIX

**Atributos:**
- **Assinatura**: Referência à assinatura
- **Valor**: Montante a ser pago
- **Data de Vencimento**: Prazo para pagamento
- **Data de Pagamento**: Quando foi pago (se aplicável)
- **Tipo de Pagamento**: Forma de pagamento utilizada
- **Link de Pagamento**: URL para realizar o pagamento
- **Número da Fatura**: Identificador único

## 3. Funcionalidades Principais

### 3.1 Sistema de Checkout

Fluxo completo para contratação de novos planos:

1. **Seleção de Plano**: Cliente escolhe o plano base desejado
2. **Addons Opcionais**: Possibilidade de adicionar recursos extras
3. **Dados do Cliente**: Coleta de informações pessoais
4. **Forma de Pagamento**: Escolha entre Boleto, Cartão ou PIX
5. **Confirmação**: Geração de link de pagamento e criação da assinatura

### 3.2 Gestão de Planos

- Criar novos planos com diferentes ciclos de cobrança
- Editar preços e características
- Definir lista de features incluídas
- Ativar ou desativar planos
- Visualizar assinaturas vinculadas

### 3.3 Gestão de Addons

- Criar addons recorrentes ou de pagamento único
- Definir preços independentes
- Ativar ou desativar conforme necessidade
- Associar a assinaturas existentes

### 3.4 Acompanhamento de Assinaturas

- Visualizar todas as assinaturas por status
- Acompanhar datas de vencimento
- Identificar assinaturas em atraso
- Gerenciar cancelamentos
- Visualizar histórico de pagamentos

### 3.5 Controle de Pagamentos

- Monitorar status de todos os pagamentos
- Identificar pagamentos pendentes ou vencidos
- Acompanhar receita por período
- Visualizar detalhes de cada transação

## 4. Painel Administrativo

### 4.1 Dashboard Principal

Visão geral com métricas importantes:
- Total de assinaturas ativas
- Receita recorrente mensal (MRR)
- Taxa de cancelamento (Churn)
- Pagamentos pendentes

### 4.2 Módulo de Planos

Interface para gerenciamento completo de planos:
- Listagem com filtros por status e ciclo
- Formulário de criação/edição
- Editor JSON para features
- Visualização de métricas por plano

### 4.3 Módulo de Addons

Gestão de recursos adicionais:
- Listagem com filtros por tipo e status
- Criação de novos addons
- Controle de preços
- Relatório de addons mais contratados

### 4.4 Módulo de Clientes

Gerenciamento de base de clientes:
- Listagem com busca por nome/email
- Visualização de assinaturas por cliente
- Histórico de pagamentos
- Dados de contato

### 4.5 Módulo de Assinaturas

Controle do ciclo de vida das assinaturas:
- Filtros por status e período
- Detalhes completos de cada assinatura
- Gestão de addons associados
- Ações de cancelamento/reativação

### 4.6 Módulo de Pagamentos

Acompanhamento financeiro:
- Listagem de todos os pagamentos
- Filtros por status, data e valor
- Exportação de relatórios
- Links para comprovantes

## 5. Regras de Negócio

### 5.1 Criação de Assinaturas

- Cliente é criado automaticamente se não existir no sistema
- Email é único e obrigatório para cada cliente
- Primeira cobrança é gerada com vencimento em 7 dias
- Ciclo de cobrança segue a configuração do plano escolhido
- Status inicial é sempre PENDING até confirmação do pagamento

### 5.2 Cálculo de Valores

- **Valor da Assinatura** = Preço do Plano + Soma dos Addons
- **Addons Recorrentes**: Incluídos em todas as cobranças
- **Addons Únicos**: Cobrados apenas na primeira fatura
- Valores suportam até 2 casas decimais
- Não há rateio em caso de cancelamento

### 5.3 Ciclo de Vida da Assinatura

1. **Criação**: Status PENDING
2. **Ativação**: Status ACTIVE após primeiro pagamento confirmado
3. **Manutenção**: Cobranças automáticas conforme ciclo
4. **Inadimplência**: Status INACTIVE após período de tolerância
5. **Cancelamento**: Status CANCELED (mantém histórico)
6. **Expiração**: Status EXPIRED após período sem pagamento

### 5.4 Políticas de Cobrança

- Cobranças são geradas automaticamente conforme ciclo
- Tolerância de 7 dias para pagamento após vencimento
- Após tolerância, assinatura pode ser suspensa
- Reativação mediante quitação de pendências
- Histórico completo é mantido para auditoria

### 5.5 Gestão de Addons

- Addons só podem ser adicionados a assinaturas ativas
- Remoção de addon recorrente vale a partir do próximo ciclo
- Addons únicos não podem ser removidos após cobrança
- Quantidade padrão é 1, mas pode ser ajustada

## 6. APIs Disponíveis

### 6.1 Consulta de Planos e Addons
**GET /api/checkout/plans**
- Retorna todos os planos e addons ativos
- Ordenados por preço crescente
- Formato JSON com detalhes completos

### 6.2 Iniciar Checkout
**POST /api/checkout/start**
- Cria nova assinatura com plano e addons selecionados
- Registra ou atualiza dados do cliente
- Retorna link para pagamento da primeira parcela

### 6.3 Consultar Assinatura
**GET /api/checkout/subscription/:id**
- Retorna dados completos da assinatura
- Inclui informações do plano, cliente e addons
- Mostra último pagamento realizado

## 7. Considerações de Segurança

- Autenticação obrigatória para acesso ao painel admin
- Validação de dados em todas as entradas
- Logs de auditoria para ações críticas
- Proteção contra duplicação de cobranças
- Criptografia de dados sensíveis