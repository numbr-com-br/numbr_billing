var __defProp = Object.defineProperty;
var __getOwnPropNames = Object.getOwnPropertyNames;
var __esm = (fn, res) => function __init() {
  return fn && (res = (0, fn[__getOwnPropNames(fn)[0]])(fn = 0)), res;
};
var __export = (target, all) => {
  for (var name in all)
    __defProp(target, name, { get: all[name], enumerable: true });
};

// src/generated/prisma/enums.ts
var enums_exports = {};
__export(enums_exports, {
  AddonType: () => AddonType,
  BillingCycle: () => BillingCycle,
  PaymentStatus: () => PaymentStatus,
  SubscriptionStatus: () => SubscriptionStatus
});
var BillingCycle, AddonType, SubscriptionStatus, PaymentStatus;
var init_enums = __esm({
  "src/generated/prisma/enums.ts"() {
    "use strict";
    BillingCycle = {
      WEEKLY: "WEEKLY",
      BIWEEKLY: "BIWEEKLY",
      MONTHLY: "MONTHLY",
      QUARTERLY: "QUARTERLY",
      SEMIANNUALLY: "SEMIANNUALLY",
      YEARLY: "YEARLY"
    };
    AddonType = {
      RECURRING: "RECURRING",
      ONE_TIME: "ONE_TIME"
    };
    SubscriptionStatus = {
      ACTIVE: "ACTIVE",
      INACTIVE: "INACTIVE",
      PENDING: "PENDING",
      CANCELED: "CANCELED",
      EXPIRED: "EXPIRED"
    };
    PaymentStatus = {
      PENDING: "PENDING",
      CONFIRMED: "CONFIRMED",
      RECEIVED: "RECEIVED",
      OVERDUE: "OVERDUE",
      REFUNDED: "REFUNDED",
      FAILED: "FAILED"
    };
  }
});

// src/generated/prisma/internal/class.ts
import * as runtime from "@prisma/client/runtime/library";
function getPrismaClientClass(dirname2) {
  config2.dirname = dirname2;
  return runtime.getPrismaClient(config2);
}
var config2;
var init_class = __esm({
  "src/generated/prisma/internal/class.ts"() {
    "use strict";
    config2 = {
      "generator": {
        "name": "client",
        "provider": {
          "fromEnvVar": null,
          "value": "prisma-client"
        },
        "output": {
          "value": "/Users/thiago/git/numbr_billing/src/generated/prisma",
          "fromEnvVar": null
        },
        "config": {
          "moduleFormat": "ESM",
          "engineType": "library"
        },
        "binaryTargets": [
          {
            "fromEnvVar": null,
            "value": "darwin",
            "native": true
          },
          {
            "fromEnvVar": null,
            "value": "rhel-openssl-3.0.x"
          },
          {
            "fromEnvVar": null,
            "value": "debian-openssl-3.0.x"
          }
        ],
        "previewFeatures": [],
        "sourceFilePath": "/Users/thiago/git/numbr_billing/prisma/schema.prisma",
        "isCustomOutput": true
      },
      "relativePath": "../../../prisma",
      "clientVersion": "6.11.1",
      "engineVersion": "f40f79ec31188888a2e33acda0ecc8fd10a853a9",
      "datasourceNames": [
        "db"
      ],
      "activeProvider": "mysql",
      "postinstall": false,
      "inlineDatasources": {
        "db": {
          "url": {
            "fromEnvVar": "DATABASE_URL",
            "value": null
          }
        }
      },
      "inlineSchema": 'generator client {\n  provider      = "prisma-client"\n  output        = "../src/generated/prisma"\n  moduleFormat  = "ESM"\n  binaryTargets = ["native", "rhel-openssl-3.0.x", "debian-openssl-3.0.x"]\n}\n\ndatasource db {\n  provider = "mysql"\n  url      = env("DATABASE_URL")\n}\n\nenum BillingCycle {\n  WEEKLY\n  BIWEEKLY\n  MONTHLY\n  QUARTERLY\n  SEMIANNUALLY\n  YEARLY\n}\n\nenum AddonType {\n  RECURRING\n  ONE_TIME\n}\n\nenum SubscriptionStatus {\n  ACTIVE\n  INACTIVE\n  PENDING\n  CANCELED\n  EXPIRED\n}\n\nenum PaymentStatus {\n  PENDING\n  CONFIRMED\n  RECEIVED\n  OVERDUE\n  REFUNDED\n  FAILED\n}\n\nmodel Plan {\n  id            String         @id @default(cuid())\n  name          String\n  description   String?\n  price         Decimal        @db.Decimal(10, 2)\n  cycle         BillingCycle\n  features      Json           @default("[]")\n  isActive      Boolean        @default(true)\n  createdAt     DateTime       @default(now())\n  updatedAt     DateTime       @updatedAt\n  subscriptions Subscription[]\n\n  @@map("plans")\n}\n\nmodel Addon {\n  id                 String              @id @default(cuid())\n  name               String\n  description        String?\n  price              Decimal             @db.Decimal(10, 2)\n  type               AddonType\n  isActive           Boolean             @default(true)\n  createdAt          DateTime            @default(now())\n  updatedAt          DateTime            @updatedAt\n  subscriptionAddons SubscriptionAddon[]\n\n  @@map("addons")\n}\n\nmodel Customer {\n  id              String         @id @default(cuid())\n  email           String         @unique\n  name            String\n  phone           String?\n  cpfCnpj         String?\n  asaasCustomerId String?        @unique\n  createdAt       DateTime       @default(now())\n  updatedAt       DateTime       @updatedAt\n  subscriptions   Subscription[]\n\n  @@map("customers")\n}\n\nmodel Subscription {\n  id                  String              @id @default(cuid())\n  customer            Customer            @relation(fields: [customerId], references: [id])\n  customerId          String\n  plan                Plan                @relation(fields: [planId], references: [id])\n  planId              String\n  asaasSubscriptionId String?             @unique\n  status              SubscriptionStatus  @default(PENDING)\n  startDate           DateTime            @default(now())\n  nextDueDate         DateTime?\n  canceledAt          DateTime?\n  createdAt           DateTime            @default(now())\n  updatedAt           DateTime            @updatedAt\n  payments            Payment[]\n  addons              SubscriptionAddon[]\n\n  @@map("subscriptions")\n}\n\nmodel SubscriptionAddon {\n  id             String       @id @default(cuid())\n  subscription   Subscription @relation(fields: [subscriptionId], references: [id])\n  subscriptionId String\n  addon          Addon        @relation(fields: [addonId], references: [id])\n  addonId        String\n  quantity       Int          @default(1)\n  createdAt      DateTime     @default(now())\n\n  @@unique([subscriptionId, addonId])\n  @@map("subscription_addons")\n}\n\nmodel Payment {\n  id                 String        @id @default(cuid())\n  subscription       Subscription  @relation(fields: [subscriptionId], references: [id])\n  subscriptionId     String\n  amount             Decimal       @db.Decimal(10, 2)\n  status             PaymentStatus @default(PENDING)\n  asaasPaymentId     String?       @unique\n  dueDate            DateTime\n  paidAt             DateTime?\n  paymentLink        String?\n  billingType        String?\n  invoiceNumber      String?\n  externalReference  String?\n  description        String?\n  transactionReceipt String?\n  createdAt          DateTime      @default(now())\n  updatedAt          DateTime      @updatedAt\n\n  @@map("payments")\n}\n\nmodel WebhookLog {\n  id          String   @id @default(cuid())\n  event       String\n  payload     Json\n  processedAt DateTime @default(now())\n  success     Boolean  @default(true)\n  error       String?\n\n  @@map("webhook_logs")\n}\n',
      "inlineSchemaHash": "48c3fc5e6d23b27f721a1b9c5450a26dbd07ffc7e35af4a454a0b0c21334af25",
      "copyEngine": true,
      "runtimeDataModel": {
        "models": {},
        "enums": {},
        "types": {}
      },
      "dirname": ""
    };
    config2.runtimeDataModel = JSON.parse('{"models":{"Plan":{"dbName":"plans","schema":null,"fields":[{"name":"id","kind":"scalar","isList":false,"isRequired":true,"isUnique":false,"isId":true,"isReadOnly":false,"hasDefaultValue":true,"type":"String","nativeType":null,"default":{"name":"cuid","args":[1]},"isGenerated":false,"isUpdatedAt":false},{"name":"name","kind":"scalar","isList":false,"isRequired":true,"isUnique":false,"isId":false,"isReadOnly":false,"hasDefaultValue":false,"type":"String","nativeType":null,"isGenerated":false,"isUpdatedAt":false},{"name":"description","kind":"scalar","isList":false,"isRequired":false,"isUnique":false,"isId":false,"isReadOnly":false,"hasDefaultValue":false,"type":"String","nativeType":null,"isGenerated":false,"isUpdatedAt":false},{"name":"price","kind":"scalar","isList":false,"isRequired":true,"isUnique":false,"isId":false,"isReadOnly":false,"hasDefaultValue":false,"type":"Decimal","nativeType":["Decimal",["10","2"]],"isGenerated":false,"isUpdatedAt":false},{"name":"cycle","kind":"enum","isList":false,"isRequired":true,"isUnique":false,"isId":false,"isReadOnly":false,"hasDefaultValue":false,"type":"BillingCycle","nativeType":null,"isGenerated":false,"isUpdatedAt":false},{"name":"features","kind":"scalar","isList":false,"isRequired":true,"isUnique":false,"isId":false,"isReadOnly":false,"hasDefaultValue":true,"type":"Json","nativeType":null,"default":"[]","isGenerated":false,"isUpdatedAt":false},{"name":"isActive","kind":"scalar","isList":false,"isRequired":true,"isUnique":false,"isId":false,"isReadOnly":false,"hasDefaultValue":true,"type":"Boolean","nativeType":null,"default":true,"isGenerated":false,"isUpdatedAt":false},{"name":"createdAt","kind":"scalar","isList":false,"isRequired":true,"isUnique":false,"isId":false,"isReadOnly":false,"hasDefaultValue":true,"type":"DateTime","nativeType":null,"default":{"name":"now","args":[]},"isGenerated":false,"isUpdatedAt":false},{"name":"updatedAt","kind":"scalar","isList":false,"isRequired":true,"isUnique":false,"isId":false,"isReadOnly":false,"hasDefaultValue":false,"type":"DateTime","nativeType":null,"isGenerated":false,"isUpdatedAt":true},{"name":"subscriptions","kind":"object","isList":true,"isRequired":true,"isUnique":false,"isId":false,"isReadOnly":false,"hasDefaultValue":false,"type":"Subscription","nativeType":null,"relationName":"PlanToSubscription","relationFromFields":[],"relationToFields":[],"isGenerated":false,"isUpdatedAt":false}],"primaryKey":null,"uniqueFields":[],"uniqueIndexes":[],"isGenerated":false},"Addon":{"dbName":"addons","schema":null,"fields":[{"name":"id","kind":"scalar","isList":false,"isRequired":true,"isUnique":false,"isId":true,"isReadOnly":false,"hasDefaultValue":true,"type":"String","nativeType":null,"default":{"name":"cuid","args":[1]},"isGenerated":false,"isUpdatedAt":false},{"name":"name","kind":"scalar","isList":false,"isRequired":true,"isUnique":false,"isId":false,"isReadOnly":false,"hasDefaultValue":false,"type":"String","nativeType":null,"isGenerated":false,"isUpdatedAt":false},{"name":"description","kind":"scalar","isList":false,"isRequired":false,"isUnique":false,"isId":false,"isReadOnly":false,"hasDefaultValue":false,"type":"String","nativeType":null,"isGenerated":false,"isUpdatedAt":false},{"name":"price","kind":"scalar","isList":false,"isRequired":true,"isUnique":false,"isId":false,"isReadOnly":false,"hasDefaultValue":false,"type":"Decimal","nativeType":["Decimal",["10","2"]],"isGenerated":false,"isUpdatedAt":false},{"name":"type","kind":"enum","isList":false,"isRequired":true,"isUnique":false,"isId":false,"isReadOnly":false,"hasDefaultValue":false,"type":"AddonType","nativeType":null,"isGenerated":false,"isUpdatedAt":false},{"name":"isActive","kind":"scalar","isList":false,"isRequired":true,"isUnique":false,"isId":false,"isReadOnly":false,"hasDefaultValue":true,"type":"Boolean","nativeType":null,"default":true,"isGenerated":false,"isUpdatedAt":false},{"name":"createdAt","kind":"scalar","isList":false,"isRequired":true,"isUnique":false,"isId":false,"isReadOnly":false,"hasDefaultValue":true,"type":"DateTime","nativeType":null,"default":{"name":"now","args":[]},"isGenerated":false,"isUpdatedAt":false},{"name":"updatedAt","kind":"scalar","isList":false,"isRequired":true,"isUnique":false,"isId":false,"isReadOnly":false,"hasDefaultValue":false,"type":"DateTime","nativeType":null,"isGenerated":false,"isUpdatedAt":true},{"name":"subscriptionAddons","kind":"object","isList":true,"isRequired":true,"isUnique":false,"isId":false,"isReadOnly":false,"hasDefaultValue":false,"type":"SubscriptionAddon","nativeType":null,"relationName":"AddonToSubscriptionAddon","relationFromFields":[],"relationToFields":[],"isGenerated":false,"isUpdatedAt":false}],"primaryKey":null,"uniqueFields":[],"uniqueIndexes":[],"isGenerated":false},"Customer":{"dbName":"customers","schema":null,"fields":[{"name":"id","kind":"scalar","isList":false,"isRequired":true,"isUnique":false,"isId":true,"isReadOnly":false,"hasDefaultValue":true,"type":"String","nativeType":null,"default":{"name":"cuid","args":[1]},"isGenerated":false,"isUpdatedAt":false},{"name":"email","kind":"scalar","isList":false,"isRequired":true,"isUnique":true,"isId":false,"isReadOnly":false,"hasDefaultValue":false,"type":"String","nativeType":null,"isGenerated":false,"isUpdatedAt":false},{"name":"name","kind":"scalar","isList":false,"isRequired":true,"isUnique":false,"isId":false,"isReadOnly":false,"hasDefaultValue":false,"type":"String","nativeType":null,"isGenerated":false,"isUpdatedAt":false},{"name":"phone","kind":"scalar","isList":false,"isRequired":false,"isUnique":false,"isId":false,"isReadOnly":false,"hasDefaultValue":false,"type":"String","nativeType":null,"isGenerated":false,"isUpdatedAt":false},{"name":"cpfCnpj","kind":"scalar","isList":false,"isRequired":false,"isUnique":false,"isId":false,"isReadOnly":false,"hasDefaultValue":false,"type":"String","nativeType":null,"isGenerated":false,"isUpdatedAt":false},{"name":"asaasCustomerId","kind":"scalar","isList":false,"isRequired":false,"isUnique":true,"isId":false,"isReadOnly":false,"hasDefaultValue":false,"type":"String","nativeType":null,"isGenerated":false,"isUpdatedAt":false},{"name":"createdAt","kind":"scalar","isList":false,"isRequired":true,"isUnique":false,"isId":false,"isReadOnly":false,"hasDefaultValue":true,"type":"DateTime","nativeType":null,"default":{"name":"now","args":[]},"isGenerated":false,"isUpdatedAt":false},{"name":"updatedAt","kind":"scalar","isList":false,"isRequired":true,"isUnique":false,"isId":false,"isReadOnly":false,"hasDefaultValue":false,"type":"DateTime","nativeType":null,"isGenerated":false,"isUpdatedAt":true},{"name":"subscriptions","kind":"object","isList":true,"isRequired":true,"isUnique":false,"isId":false,"isReadOnly":false,"hasDefaultValue":false,"type":"Subscription","nativeType":null,"relationName":"CustomerToSubscription","relationFromFields":[],"relationToFields":[],"isGenerated":false,"isUpdatedAt":false}],"primaryKey":null,"uniqueFields":[],"uniqueIndexes":[],"isGenerated":false},"Subscription":{"dbName":"subscriptions","schema":null,"fields":[{"name":"id","kind":"scalar","isList":false,"isRequired":true,"isUnique":false,"isId":true,"isReadOnly":false,"hasDefaultValue":true,"type":"String","nativeType":null,"default":{"name":"cuid","args":[1]},"isGenerated":false,"isUpdatedAt":false},{"name":"customer","kind":"object","isList":false,"isRequired":true,"isUnique":false,"isId":false,"isReadOnly":false,"hasDefaultValue":false,"type":"Customer","nativeType":null,"relationName":"CustomerToSubscription","relationFromFields":["customerId"],"relationToFields":["id"],"isGenerated":false,"isUpdatedAt":false},{"name":"customerId","kind":"scalar","isList":false,"isRequired":true,"isUnique":false,"isId":false,"isReadOnly":true,"hasDefaultValue":false,"type":"String","nativeType":null,"isGenerated":false,"isUpdatedAt":false},{"name":"plan","kind":"object","isList":false,"isRequired":true,"isUnique":false,"isId":false,"isReadOnly":false,"hasDefaultValue":false,"type":"Plan","nativeType":null,"relationName":"PlanToSubscription","relationFromFields":["planId"],"relationToFields":["id"],"isGenerated":false,"isUpdatedAt":false},{"name":"planId","kind":"scalar","isList":false,"isRequired":true,"isUnique":false,"isId":false,"isReadOnly":true,"hasDefaultValue":false,"type":"String","nativeType":null,"isGenerated":false,"isUpdatedAt":false},{"name":"asaasSubscriptionId","kind":"scalar","isList":false,"isRequired":false,"isUnique":true,"isId":false,"isReadOnly":false,"hasDefaultValue":false,"type":"String","nativeType":null,"isGenerated":false,"isUpdatedAt":false},{"name":"status","kind":"enum","isList":false,"isRequired":true,"isUnique":false,"isId":false,"isReadOnly":false,"hasDefaultValue":true,"type":"SubscriptionStatus","nativeType":null,"default":"PENDING","isGenerated":false,"isUpdatedAt":false},{"name":"startDate","kind":"scalar","isList":false,"isRequired":true,"isUnique":false,"isId":false,"isReadOnly":false,"hasDefaultValue":true,"type":"DateTime","nativeType":null,"default":{"name":"now","args":[]},"isGenerated":false,"isUpdatedAt":false},{"name":"nextDueDate","kind":"scalar","isList":false,"isRequired":false,"isUnique":false,"isId":false,"isReadOnly":false,"hasDefaultValue":false,"type":"DateTime","nativeType":null,"isGenerated":false,"isUpdatedAt":false},{"name":"canceledAt","kind":"scalar","isList":false,"isRequired":false,"isUnique":false,"isId":false,"isReadOnly":false,"hasDefaultValue":false,"type":"DateTime","nativeType":null,"isGenerated":false,"isUpdatedAt":false},{"name":"createdAt","kind":"scalar","isList":false,"isRequired":true,"isUnique":false,"isId":false,"isReadOnly":false,"hasDefaultValue":true,"type":"DateTime","nativeType":null,"default":{"name":"now","args":[]},"isGenerated":false,"isUpdatedAt":false},{"name":"updatedAt","kind":"scalar","isList":false,"isRequired":true,"isUnique":false,"isId":false,"isReadOnly":false,"hasDefaultValue":false,"type":"DateTime","nativeType":null,"isGenerated":false,"isUpdatedAt":true},{"name":"payments","kind":"object","isList":true,"isRequired":true,"isUnique":false,"isId":false,"isReadOnly":false,"hasDefaultValue":false,"type":"Payment","nativeType":null,"relationName":"PaymentToSubscription","relationFromFields":[],"relationToFields":[],"isGenerated":false,"isUpdatedAt":false},{"name":"addons","kind":"object","isList":true,"isRequired":true,"isUnique":false,"isId":false,"isReadOnly":false,"hasDefaultValue":false,"type":"SubscriptionAddon","nativeType":null,"relationName":"SubscriptionToSubscriptionAddon","relationFromFields":[],"relationToFields":[],"isGenerated":false,"isUpdatedAt":false}],"primaryKey":null,"uniqueFields":[],"uniqueIndexes":[],"isGenerated":false},"SubscriptionAddon":{"dbName":"subscription_addons","schema":null,"fields":[{"name":"id","kind":"scalar","isList":false,"isRequired":true,"isUnique":false,"isId":true,"isReadOnly":false,"hasDefaultValue":true,"type":"String","nativeType":null,"default":{"name":"cuid","args":[1]},"isGenerated":false,"isUpdatedAt":false},{"name":"subscription","kind":"object","isList":false,"isRequired":true,"isUnique":false,"isId":false,"isReadOnly":false,"hasDefaultValue":false,"type":"Subscription","nativeType":null,"relationName":"SubscriptionToSubscriptionAddon","relationFromFields":["subscriptionId"],"relationToFields":["id"],"isGenerated":false,"isUpdatedAt":false},{"name":"subscriptionId","kind":"scalar","isList":false,"isRequired":true,"isUnique":false,"isId":false,"isReadOnly":true,"hasDefaultValue":false,"type":"String","nativeType":null,"isGenerated":false,"isUpdatedAt":false},{"name":"addon","kind":"object","isList":false,"isRequired":true,"isUnique":false,"isId":false,"isReadOnly":false,"hasDefaultValue":false,"type":"Addon","nativeType":null,"relationName":"AddonToSubscriptionAddon","relationFromFields":["addonId"],"relationToFields":["id"],"isGenerated":false,"isUpdatedAt":false},{"name":"addonId","kind":"scalar","isList":false,"isRequired":true,"isUnique":false,"isId":false,"isReadOnly":true,"hasDefaultValue":false,"type":"String","nativeType":null,"isGenerated":false,"isUpdatedAt":false},{"name":"quantity","kind":"scalar","isList":false,"isRequired":true,"isUnique":false,"isId":false,"isReadOnly":false,"hasDefaultValue":true,"type":"Int","nativeType":null,"default":1,"isGenerated":false,"isUpdatedAt":false},{"name":"createdAt","kind":"scalar","isList":false,"isRequired":true,"isUnique":false,"isId":false,"isReadOnly":false,"hasDefaultValue":true,"type":"DateTime","nativeType":null,"default":{"name":"now","args":[]},"isGenerated":false,"isUpdatedAt":false}],"primaryKey":null,"uniqueFields":[["subscriptionId","addonId"]],"uniqueIndexes":[{"name":null,"fields":["subscriptionId","addonId"]}],"isGenerated":false},"Payment":{"dbName":"payments","schema":null,"fields":[{"name":"id","kind":"scalar","isList":false,"isRequired":true,"isUnique":false,"isId":true,"isReadOnly":false,"hasDefaultValue":true,"type":"String","nativeType":null,"default":{"name":"cuid","args":[1]},"isGenerated":false,"isUpdatedAt":false},{"name":"subscription","kind":"object","isList":false,"isRequired":true,"isUnique":false,"isId":false,"isReadOnly":false,"hasDefaultValue":false,"type":"Subscription","nativeType":null,"relationName":"PaymentToSubscription","relationFromFields":["subscriptionId"],"relationToFields":["id"],"isGenerated":false,"isUpdatedAt":false},{"name":"subscriptionId","kind":"scalar","isList":false,"isRequired":true,"isUnique":false,"isId":false,"isReadOnly":true,"hasDefaultValue":false,"type":"String","nativeType":null,"isGenerated":false,"isUpdatedAt":false},{"name":"amount","kind":"scalar","isList":false,"isRequired":true,"isUnique":false,"isId":false,"isReadOnly":false,"hasDefaultValue":false,"type":"Decimal","nativeType":["Decimal",["10","2"]],"isGenerated":false,"isUpdatedAt":false},{"name":"status","kind":"enum","isList":false,"isRequired":true,"isUnique":false,"isId":false,"isReadOnly":false,"hasDefaultValue":true,"type":"PaymentStatus","nativeType":null,"default":"PENDING","isGenerated":false,"isUpdatedAt":false},{"name":"asaasPaymentId","kind":"scalar","isList":false,"isRequired":false,"isUnique":true,"isId":false,"isReadOnly":false,"hasDefaultValue":false,"type":"String","nativeType":null,"isGenerated":false,"isUpdatedAt":false},{"name":"dueDate","kind":"scalar","isList":false,"isRequired":true,"isUnique":false,"isId":false,"isReadOnly":false,"hasDefaultValue":false,"type":"DateTime","nativeType":null,"isGenerated":false,"isUpdatedAt":false},{"name":"paidAt","kind":"scalar","isList":false,"isRequired":false,"isUnique":false,"isId":false,"isReadOnly":false,"hasDefaultValue":false,"type":"DateTime","nativeType":null,"isGenerated":false,"isUpdatedAt":false},{"name":"paymentLink","kind":"scalar","isList":false,"isRequired":false,"isUnique":false,"isId":false,"isReadOnly":false,"hasDefaultValue":false,"type":"String","nativeType":null,"isGenerated":false,"isUpdatedAt":false},{"name":"billingType","kind":"scalar","isList":false,"isRequired":false,"isUnique":false,"isId":false,"isReadOnly":false,"hasDefaultValue":false,"type":"String","nativeType":null,"isGenerated":false,"isUpdatedAt":false},{"name":"invoiceNumber","kind":"scalar","isList":false,"isRequired":false,"isUnique":false,"isId":false,"isReadOnly":false,"hasDefaultValue":false,"type":"String","nativeType":null,"isGenerated":false,"isUpdatedAt":false},{"name":"externalReference","kind":"scalar","isList":false,"isRequired":false,"isUnique":false,"isId":false,"isReadOnly":false,"hasDefaultValue":false,"type":"String","nativeType":null,"isGenerated":false,"isUpdatedAt":false},{"name":"description","kind":"scalar","isList":false,"isRequired":false,"isUnique":false,"isId":false,"isReadOnly":false,"hasDefaultValue":false,"type":"String","nativeType":null,"isGenerated":false,"isUpdatedAt":false},{"name":"transactionReceipt","kind":"scalar","isList":false,"isRequired":false,"isUnique":false,"isId":false,"isReadOnly":false,"hasDefaultValue":false,"type":"String","nativeType":null,"isGenerated":false,"isUpdatedAt":false},{"name":"createdAt","kind":"scalar","isList":false,"isRequired":true,"isUnique":false,"isId":false,"isReadOnly":false,"hasDefaultValue":true,"type":"DateTime","nativeType":null,"default":{"name":"now","args":[]},"isGenerated":false,"isUpdatedAt":false},{"name":"updatedAt","kind":"scalar","isList":false,"isRequired":true,"isUnique":false,"isId":false,"isReadOnly":false,"hasDefaultValue":false,"type":"DateTime","nativeType":null,"isGenerated":false,"isUpdatedAt":true}],"primaryKey":null,"uniqueFields":[],"uniqueIndexes":[],"isGenerated":false},"WebhookLog":{"dbName":"webhook_logs","schema":null,"fields":[{"name":"id","kind":"scalar","isList":false,"isRequired":true,"isUnique":false,"isId":true,"isReadOnly":false,"hasDefaultValue":true,"type":"String","nativeType":null,"default":{"name":"cuid","args":[1]},"isGenerated":false,"isUpdatedAt":false},{"name":"event","kind":"scalar","isList":false,"isRequired":true,"isUnique":false,"isId":false,"isReadOnly":false,"hasDefaultValue":false,"type":"String","nativeType":null,"isGenerated":false,"isUpdatedAt":false},{"name":"payload","kind":"scalar","isList":false,"isRequired":true,"isUnique":false,"isId":false,"isReadOnly":false,"hasDefaultValue":false,"type":"Json","nativeType":null,"isGenerated":false,"isUpdatedAt":false},{"name":"processedAt","kind":"scalar","isList":false,"isRequired":true,"isUnique":false,"isId":false,"isReadOnly":false,"hasDefaultValue":true,"type":"DateTime","nativeType":null,"default":{"name":"now","args":[]},"isGenerated":false,"isUpdatedAt":false},{"name":"success","kind":"scalar","isList":false,"isRequired":true,"isUnique":false,"isId":false,"isReadOnly":false,"hasDefaultValue":true,"type":"Boolean","nativeType":null,"default":true,"isGenerated":false,"isUpdatedAt":false},{"name":"error","kind":"scalar","isList":false,"isRequired":false,"isUnique":false,"isId":false,"isReadOnly":false,"hasDefaultValue":false,"type":"String","nativeType":null,"isGenerated":false,"isUpdatedAt":false}],"primaryKey":null,"uniqueFields":[],"uniqueIndexes":[],"isGenerated":false}},"enums":{"BillingCycle":{"values":[{"name":"WEEKLY","dbName":null},{"name":"BIWEEKLY","dbName":null},{"name":"MONTHLY","dbName":null},{"name":"QUARTERLY","dbName":null},{"name":"SEMIANNUALLY","dbName":null},{"name":"YEARLY","dbName":null}],"dbName":null},"AddonType":{"values":[{"name":"RECURRING","dbName":null},{"name":"ONE_TIME","dbName":null}],"dbName":null},"SubscriptionStatus":{"values":[{"name":"ACTIVE","dbName":null},{"name":"INACTIVE","dbName":null},{"name":"PENDING","dbName":null},{"name":"CANCELED","dbName":null},{"name":"EXPIRED","dbName":null}],"dbName":null},"PaymentStatus":{"values":[{"name":"PENDING","dbName":null},{"name":"CONFIRMED","dbName":null},{"name":"RECEIVED","dbName":null},{"name":"OVERDUE","dbName":null},{"name":"REFUNDED","dbName":null},{"name":"FAILED","dbName":null}],"dbName":null}},"types":{}}');
    config2.engineWasm = void 0;
    config2.compilerWasm = void 0;
  }
});

// src/generated/prisma/internal/prismaNamespace.ts
var prismaNamespace_exports = {};
__export(prismaNamespace_exports, {
  AddonOrderByRelevanceFieldEnum: () => AddonOrderByRelevanceFieldEnum,
  AddonScalarFieldEnum: () => AddonScalarFieldEnum,
  AnyNull: () => AnyNull,
  CustomerOrderByRelevanceFieldEnum: () => CustomerOrderByRelevanceFieldEnum,
  CustomerScalarFieldEnum: () => CustomerScalarFieldEnum,
  DbNull: () => DbNull,
  Decimal: () => Decimal2,
  JsonNull: () => JsonNull,
  JsonNullValueFilter: () => JsonNullValueFilter,
  JsonNullValueInput: () => JsonNullValueInput,
  ModelName: () => ModelName,
  NullTypes: () => NullTypes,
  NullsOrder: () => NullsOrder,
  PaymentOrderByRelevanceFieldEnum: () => PaymentOrderByRelevanceFieldEnum,
  PaymentScalarFieldEnum: () => PaymentScalarFieldEnum,
  PlanOrderByRelevanceFieldEnum: () => PlanOrderByRelevanceFieldEnum,
  PlanScalarFieldEnum: () => PlanScalarFieldEnum,
  PrismaClientInitializationError: () => PrismaClientInitializationError2,
  PrismaClientKnownRequestError: () => PrismaClientKnownRequestError2,
  PrismaClientRustPanicError: () => PrismaClientRustPanicError2,
  PrismaClientUnknownRequestError: () => PrismaClientUnknownRequestError2,
  PrismaClientValidationError: () => PrismaClientValidationError2,
  QueryMode: () => QueryMode,
  SortOrder: () => SortOrder,
  Sql: () => Sql2,
  SubscriptionAddonOrderByRelevanceFieldEnum: () => SubscriptionAddonOrderByRelevanceFieldEnum,
  SubscriptionAddonScalarFieldEnum: () => SubscriptionAddonScalarFieldEnum,
  SubscriptionOrderByRelevanceFieldEnum: () => SubscriptionOrderByRelevanceFieldEnum,
  SubscriptionScalarFieldEnum: () => SubscriptionScalarFieldEnum,
  TransactionIsolationLevel: () => TransactionIsolationLevel,
  WebhookLogOrderByRelevanceFieldEnum: () => WebhookLogOrderByRelevanceFieldEnum,
  WebhookLogScalarFieldEnum: () => WebhookLogScalarFieldEnum,
  defineExtension: () => defineExtension,
  empty: () => empty2,
  getExtensionContext: () => getExtensionContext,
  join: () => join2,
  prismaVersion: () => prismaVersion,
  raw: () => raw2,
  sql: () => sql,
  validator: () => validator
});
import * as runtime2 from "@prisma/client/runtime/library";
var validator, PrismaClientKnownRequestError2, PrismaClientUnknownRequestError2, PrismaClientRustPanicError2, PrismaClientInitializationError2, PrismaClientValidationError2, sql, empty2, join2, raw2, Sql2, Decimal2, getExtensionContext, prismaVersion, NullTypes, DbNull, JsonNull, AnyNull, ModelName, TransactionIsolationLevel, PlanScalarFieldEnum, AddonScalarFieldEnum, CustomerScalarFieldEnum, SubscriptionScalarFieldEnum, SubscriptionAddonScalarFieldEnum, PaymentScalarFieldEnum, WebhookLogScalarFieldEnum, SortOrder, JsonNullValueInput, JsonNullValueFilter, QueryMode, NullsOrder, PlanOrderByRelevanceFieldEnum, AddonOrderByRelevanceFieldEnum, CustomerOrderByRelevanceFieldEnum, SubscriptionOrderByRelevanceFieldEnum, SubscriptionAddonOrderByRelevanceFieldEnum, PaymentOrderByRelevanceFieldEnum, WebhookLogOrderByRelevanceFieldEnum, defineExtension;
var init_prismaNamespace = __esm({
  "src/generated/prisma/internal/prismaNamespace.ts"() {
    "use strict";
    validator = runtime2.Public.validator;
    PrismaClientKnownRequestError2 = runtime2.PrismaClientKnownRequestError;
    PrismaClientUnknownRequestError2 = runtime2.PrismaClientUnknownRequestError;
    PrismaClientRustPanicError2 = runtime2.PrismaClientRustPanicError;
    PrismaClientInitializationError2 = runtime2.PrismaClientInitializationError;
    PrismaClientValidationError2 = runtime2.PrismaClientValidationError;
    sql = runtime2.sqltag;
    empty2 = runtime2.empty;
    join2 = runtime2.join;
    raw2 = runtime2.raw;
    Sql2 = runtime2.Sql;
    Decimal2 = runtime2.Decimal;
    getExtensionContext = runtime2.Extensions.getExtensionContext;
    prismaVersion = {
      client: "6.11.1",
      engine: "f40f79ec31188888a2e33acda0ecc8fd10a853a9"
    };
    NullTypes = {
      DbNull: runtime2.objectEnumValues.classes.DbNull,
      JsonNull: runtime2.objectEnumValues.classes.JsonNull,
      AnyNull: runtime2.objectEnumValues.classes.AnyNull
    };
    DbNull = runtime2.objectEnumValues.instances.DbNull;
    JsonNull = runtime2.objectEnumValues.instances.JsonNull;
    AnyNull = runtime2.objectEnumValues.instances.AnyNull;
    ModelName = {
      Plan: "Plan",
      Addon: "Addon",
      Customer: "Customer",
      Subscription: "Subscription",
      SubscriptionAddon: "SubscriptionAddon",
      Payment: "Payment",
      WebhookLog: "WebhookLog"
    };
    TransactionIsolationLevel = runtime2.makeStrictEnum({
      ReadUncommitted: "ReadUncommitted",
      ReadCommitted: "ReadCommitted",
      RepeatableRead: "RepeatableRead",
      Serializable: "Serializable"
    });
    PlanScalarFieldEnum = {
      id: "id",
      name: "name",
      description: "description",
      price: "price",
      cycle: "cycle",
      features: "features",
      isActive: "isActive",
      createdAt: "createdAt",
      updatedAt: "updatedAt"
    };
    AddonScalarFieldEnum = {
      id: "id",
      name: "name",
      description: "description",
      price: "price",
      type: "type",
      isActive: "isActive",
      createdAt: "createdAt",
      updatedAt: "updatedAt"
    };
    CustomerScalarFieldEnum = {
      id: "id",
      email: "email",
      name: "name",
      phone: "phone",
      cpfCnpj: "cpfCnpj",
      asaasCustomerId: "asaasCustomerId",
      createdAt: "createdAt",
      updatedAt: "updatedAt"
    };
    SubscriptionScalarFieldEnum = {
      id: "id",
      customerId: "customerId",
      planId: "planId",
      asaasSubscriptionId: "asaasSubscriptionId",
      status: "status",
      startDate: "startDate",
      nextDueDate: "nextDueDate",
      canceledAt: "canceledAt",
      createdAt: "createdAt",
      updatedAt: "updatedAt"
    };
    SubscriptionAddonScalarFieldEnum = {
      id: "id",
      subscriptionId: "subscriptionId",
      addonId: "addonId",
      quantity: "quantity",
      createdAt: "createdAt"
    };
    PaymentScalarFieldEnum = {
      id: "id",
      subscriptionId: "subscriptionId",
      amount: "amount",
      status: "status",
      asaasPaymentId: "asaasPaymentId",
      dueDate: "dueDate",
      paidAt: "paidAt",
      paymentLink: "paymentLink",
      billingType: "billingType",
      invoiceNumber: "invoiceNumber",
      externalReference: "externalReference",
      description: "description",
      transactionReceipt: "transactionReceipt",
      createdAt: "createdAt",
      updatedAt: "updatedAt"
    };
    WebhookLogScalarFieldEnum = {
      id: "id",
      event: "event",
      payload: "payload",
      processedAt: "processedAt",
      success: "success",
      error: "error"
    };
    SortOrder = {
      asc: "asc",
      desc: "desc"
    };
    JsonNullValueInput = {
      JsonNull
    };
    JsonNullValueFilter = {
      DbNull,
      JsonNull,
      AnyNull
    };
    QueryMode = {
      default: "default",
      insensitive: "insensitive"
    };
    NullsOrder = {
      first: "first",
      last: "last"
    };
    PlanOrderByRelevanceFieldEnum = {
      id: "id",
      name: "name",
      description: "description"
    };
    AddonOrderByRelevanceFieldEnum = {
      id: "id",
      name: "name",
      description: "description"
    };
    CustomerOrderByRelevanceFieldEnum = {
      id: "id",
      email: "email",
      name: "name",
      phone: "phone",
      cpfCnpj: "cpfCnpj",
      asaasCustomerId: "asaasCustomerId"
    };
    SubscriptionOrderByRelevanceFieldEnum = {
      id: "id",
      customerId: "customerId",
      planId: "planId",
      asaasSubscriptionId: "asaasSubscriptionId"
    };
    SubscriptionAddonOrderByRelevanceFieldEnum = {
      id: "id",
      subscriptionId: "subscriptionId",
      addonId: "addonId"
    };
    PaymentOrderByRelevanceFieldEnum = {
      id: "id",
      subscriptionId: "subscriptionId",
      asaasPaymentId: "asaasPaymentId",
      paymentLink: "paymentLink",
      billingType: "billingType",
      invoiceNumber: "invoiceNumber",
      externalReference: "externalReference",
      description: "description",
      transactionReceipt: "transactionReceipt"
    };
    WebhookLogOrderByRelevanceFieldEnum = {
      id: "id",
      event: "event",
      error: "error"
    };
    defineExtension = runtime2.Extensions.defineExtension;
  }
});

// src/generated/prisma/client.ts
var client_exports = {};
__export(client_exports, {
  $Enums: () => enums_exports,
  AddonType: () => AddonType2,
  BillingCycle: () => BillingCycle2,
  PaymentStatus: () => PaymentStatus2,
  Prisma: () => prismaNamespace_exports,
  PrismaClient: () => PrismaClient,
  SubscriptionStatus: () => SubscriptionStatus2
});
import * as process2 from "node:process";
import * as path from "node:path";
import { fileURLToPath } from "node:url";
var __dirname, PrismaClient, BillingCycle2, AddonType2, SubscriptionStatus2, PaymentStatus2;
var init_client = __esm({
  "src/generated/prisma/client.ts"() {
    "use strict";
    init_enums();
    init_class();
    init_prismaNamespace();
    init_enums();
    __dirname = path.dirname(fileURLToPath(import.meta.url));
    PrismaClient = getPrismaClientClass(__dirname);
    path.join(__dirname, "libquery_engine-darwin.dylib.node");
    path.join(process2.cwd(), "src/generated/prisma/libquery_engine-darwin.dylib.node");
    path.join(__dirname, "libquery_engine-rhel-openssl-3.0.x.so.node");
    path.join(process2.cwd(), "src/generated/prisma/libquery_engine-rhel-openssl-3.0.x.so.node");
    path.join(__dirname, "libquery_engine-debian-openssl-3.0.x.so.node");
    path.join(process2.cwd(), "src/generated/prisma/libquery_engine-debian-openssl-3.0.x.so.node");
    BillingCycle2 = BillingCycle;
    AddonType2 = AddonType;
    SubscriptionStatus2 = SubscriptionStatus;
    PaymentStatus2 = PaymentStatus;
  }
});

// src/lambda.ts
import serverless from "serverless-http";

// src/app.ts
import express from "express";
import AdminJS from "adminjs";
import AdminJSExpress from "@adminjs/express";
import session from "express-session";
import { Database, Resource } from "@adminjs/prisma";

// src/config/env.ts
import dotenv from "dotenv";
dotenv.config();
var config = {
  port: parseInt(process.env.PORT || "3000", 10),
  database: {
    url: process.env.DATABASE_URL || ""
  },
  asaas: {
    apiKey: process.env.ASAAS_API_KEY || "",
    apiUrl: process.env.ASAAS_API_URL || "https://sandbox.asaas.com/api/v3",
    webhookToken: process.env.ASAAS_WEBHOOK_TOKEN || ""
  },
  admin: {
    email: process.env.ADMIN_EMAIL || "admin@numbr.com",
    password: process.env.ADMIN_PASSWORD || "admin123"
  }
};
function validateEnv() {
  const required = ["DATABASE_URL", "ASAAS_API_KEY"];
  const missing = required.filter((key) => !process.env[key]);
  if (missing.length > 0) {
    throw new Error(`Missing required environment variables: ${missing.join(", ")}`);
  }
}

// src/services/prisma.service.ts
init_client();
var prisma = new PrismaClient({
  log: process.env.NODE_ENV === "development" ? ["query", "error", "warn"] : ["error"]
});
async function connectDatabase() {
  try {
    await prisma.$connect();
    console.log("Database connected successfully");
  } catch (error) {
    console.error("Failed to connect to database:", error);
    process.exit(1);
  }
}

// src/admin/resources.ts
function setupAdminResources(dmmf) {
  const models = dmmf.datamodel.models.reduce((acc, model) => {
    acc[model.name] = model;
    return acc;
  }, {});
  return [
    {
      resource: { model: models.Plan, client: prisma },
      options: {
        navigation: {
          name: "Billing",
          icon: "CreditCard"
        },
        listProperties: ["name", "price", "cycle", "isActive", "createdAt"],
        filterProperties: ["name", "cycle", "isActive"],
        editProperties: ["name", "description", "price", "cycle", "features", "isActive"],
        showProperties: ["id", "name", "description", "price", "cycle", "features", "isActive", "createdAt", "updatedAt"],
        properties: {
          price: {
            type: "number",
            props: {
              step: 0.01
            }
          },
          features: {
            type: "mixed",
            components: {
              edit: "@adminjs/design-system/src/molecules/property-json/property-json-editor.tsx"
            }
          },
          description: {
            type: "textarea",
            props: {
              rows: 4
            }
          }
        }
      }
    },
    {
      resource: { model: models.Addon, client: prisma },
      options: {
        navigation: {
          name: "Billing",
          icon: "Plus"
        },
        listProperties: ["name", "price", "type", "isActive", "createdAt"],
        filterProperties: ["name", "type", "isActive"],
        editProperties: ["name", "description", "price", "type", "isActive"],
        showProperties: ["id", "name", "description", "price", "type", "isActive", "createdAt", "updatedAt"],
        properties: {
          price: {
            type: "number",
            props: {
              step: 0.01
            }
          },
          description: {
            type: "textarea",
            props: {
              rows: 4
            }
          }
        }
      }
    },
    {
      resource: { model: models.Customer, client: prisma },
      options: {
        navigation: {
          name: "Customers",
          icon: "User"
        },
        listProperties: ["name", "email", "phone", "asaasCustomerId", "createdAt"],
        filterProperties: ["name", "email", "phone"],
        editProperties: ["name", "email", "phone", "cpfCnpj"],
        showProperties: ["id", "name", "email", "phone", "cpfCnpj", "asaasCustomerId", "createdAt", "updatedAt"]
      }
    },
    {
      resource: { model: models.Subscription, client: prisma },
      options: {
        navigation: {
          name: "Subscriptions",
          icon: "Calendar"
        },
        listProperties: ["customer", "plan", "status", "startDate", "nextDueDate"],
        filterProperties: ["status", "startDate"],
        editProperties: ["status", "nextDueDate", "canceledAt"],
        showProperties: ["id", "customer", "plan", "asaasSubscriptionId", "status", "startDate", "nextDueDate", "canceledAt", "createdAt", "updatedAt"]
      }
    },
    {
      resource: { model: models.Payment, client: prisma },
      options: {
        navigation: {
          name: "Payments",
          icon: "Cash"
        },
        listProperties: ["subscription", "amount", "status", "dueDate", "paidAt"],
        filterProperties: ["status", "dueDate", "paidAt"],
        showProperties: ["id", "subscription", "amount", "status", "asaasPaymentId", "dueDate", "paidAt", "paymentLink", "billingType", "invoiceNumber", "description", "createdAt"],
        actions: {
          new: { isVisible: false },
          edit: { isVisible: false },
          delete: { isVisible: false }
        },
        properties: {
          amount: {
            type: "number",
            props: {
              step: 0.01
            }
          }
        }
      }
    },
    {
      resource: { model: models.WebhookLog, client: prisma },
      options: {
        navigation: {
          name: "System",
          icon: "Terminal"
        },
        listProperties: ["event", "success", "processedAt"],
        filterProperties: ["event", "success", "processedAt"],
        showProperties: ["id", "event", "payload", "success", "error", "processedAt"],
        actions: {
          new: { isVisible: false },
          edit: { isVisible: false },
          delete: { isVisible: false }
        },
        properties: {
          payload: {
            type: "mixed"
          }
        }
      }
    }
  ];
}

// src/webhooks/asaas.webhook.ts
import { Router } from "express";
init_client();
var webhookRouter = Router();
var paymentStatusMap = {
  PENDING: PaymentStatus2.PENDING,
  RECEIVED: PaymentStatus2.RECEIVED,
  CONFIRMED: PaymentStatus2.CONFIRMED,
  OVERDUE: PaymentStatus2.OVERDUE,
  REFUNDED: PaymentStatus2.REFUNDED,
  RECEIVED_IN_CASH: PaymentStatus2.RECEIVED,
  REFUND_REQUESTED: PaymentStatus2.REFUNDED,
  CHARGEBACK_REQUESTED: PaymentStatus2.FAILED,
  CHARGEBACK_DISPUTE: PaymentStatus2.FAILED,
  AWAITING_CHARGEBACK_REVERSAL: PaymentStatus2.FAILED,
  DUNNING_REQUESTED: PaymentStatus2.OVERDUE,
  DUNNING_RECEIVED: PaymentStatus2.RECEIVED,
  AWAITING_RISK_ANALYSIS: PaymentStatus2.PENDING
};
webhookRouter.post("/asaas", async (req, res) => {
  const webhookToken = req.headers["asaas-access-token"];
  if (webhookToken !== config.asaas.webhookToken) {
    res.status(401).json({ error: "Unauthorized" });
    return;
  }
  const payload = req.body;
  try {
    await prisma.webhookLog.create({
      data: {
        event: payload.event,
        payload,
        success: true
      }
    });
    switch (payload.event) {
      case "PAYMENT_CREATED":
        await handlePaymentCreated(payload);
        break;
      case "PAYMENT_UPDATED":
        await handlePaymentUpdated(payload);
        break;
      case "PAYMENT_CONFIRMED":
      case "PAYMENT_RECEIVED":
        await handlePaymentReceived(payload);
        break;
      case "PAYMENT_OVERDUE":
        await handlePaymentOverdue(payload);
        break;
      case "PAYMENT_DELETED":
        await handlePaymentDeleted(payload);
        break;
      case "PAYMENT_REFUNDED":
        await handlePaymentRefunded(payload);
        break;
      default:
        console.log(`Unhandled webhook event: ${payload.event}`);
    }
    res.status(200).json({ success: true });
  } catch (error) {
    console.error("Webhook processing error:", error);
    await prisma.webhookLog.create({
      data: {
        event: payload.event,
        payload,
        success: false,
        error: error instanceof Error ? error.message : "Unknown error"
      }
    });
    res.status(500).json({ error: "Internal server error" });
  }
});
async function handlePaymentCreated(payload) {
  if (!payload.payment) return;
  const { payment } = payload;
  if (payment.subscription) {
    const subscription = await prisma.subscription.findUnique({
      where: { asaasSubscriptionId: payment.subscription }
    });
    if (subscription) {
      await prisma.payment.create({
        data: {
          subscriptionId: subscription.id,
          asaasPaymentId: payment.id,
          amount: payment.value,
          status: paymentStatusMap[payment.status] || PaymentStatus2.PENDING,
          dueDate: new Date(payment.dueDate),
          billingType: payment.billingType,
          invoiceNumber: payment.invoiceNumber,
          externalReference: payment.externalReference,
          description: payment.description,
          paymentLink: payment.invoiceUrl
        }
      });
    }
  }
}
async function handlePaymentUpdated(payload) {
  if (!payload.payment) return;
  const { payment } = payload;
  await prisma.payment.updateMany({
    where: { asaasPaymentId: payment.id },
    data: {
      status: paymentStatusMap[payment.status] || PaymentStatus2.PENDING,
      paymentLink: payment.invoiceUrl
    }
  });
}
async function handlePaymentReceived(payload) {
  if (!payload.payment) return;
  const { payment } = payload;
  await prisma.payment.updateMany({
    where: { asaasPaymentId: payment.id },
    data: {
      status: PaymentStatus2.RECEIVED,
      paidAt: payment.paymentDate ? new Date(payment.paymentDate) : /* @__PURE__ */ new Date()
    }
  });
  if (payment.subscription) {
    await prisma.subscription.updateMany({
      where: { asaasSubscriptionId: payment.subscription },
      data: { status: SubscriptionStatus2.ACTIVE }
    });
  }
}
async function handlePaymentOverdue(payload) {
  if (!payload.payment) return;
  const { payment } = payload;
  await prisma.payment.updateMany({
    where: { asaasPaymentId: payment.id },
    data: {
      status: PaymentStatus2.OVERDUE
    }
  });
}
async function handlePaymentDeleted(payload) {
  if (!payload.payment) return;
  const { payment } = payload;
  await prisma.payment.updateMany({
    where: { asaasPaymentId: payment.id },
    data: {
      status: PaymentStatus2.FAILED
    }
  });
}
async function handlePaymentRefunded(payload) {
  if (!payload.payment) return;
  const { payment } = payload;
  await prisma.payment.updateMany({
    where: { asaasPaymentId: payment.id },
    data: {
      status: PaymentStatus2.REFUNDED
    }
  });
}

// src/routes/checkout.route.ts
import { Router as Router2 } from "express";

// src/services/asaas.service.ts
import axios from "axios";
var AsaasService = class {
  api;
  constructor() {
    this.api = axios.create({
      baseURL: config.asaas.apiUrl,
      headers: {
        "Content-Type": "application/json",
        access_token: config.asaas.apiKey
      }
    });
  }
  async createCustomer(data) {
    const response = await this.api.post("/customers", data);
    return response.data;
  }
  async getCustomer(id) {
    const response = await this.api.get(`/customers/${id}`);
    return response.data;
  }
  async createSubscription(data) {
    const response = await this.api.post("/subscriptions", data);
    return response.data;
  }
  async getSubscription(id) {
    const response = await this.api.get(`/subscriptions/${id}`);
    return response.data;
  }
  async cancelSubscription(id) {
    await this.api.delete(`/subscriptions/${id}`);
  }
  async getPayment(id) {
    const response = await this.api.get(`/payments/${id}`);
    return response.data;
  }
  async getSubscriptionPayments(subscriptionId) {
    const response = await this.api.get(`/subscriptions/${subscriptionId}/payments`);
    return response.data.data || [];
  }
  async createPaymentLink(data) {
    const response = await this.api.post("/payments", data);
    return response.data;
  }
  async getPaymentLink(paymentId) {
    const payment = await this.getPayment(paymentId);
    return payment.invoiceUrl || payment.boletoUrl || "";
  }
};
var asaasService = new AsaasService();

// src/routes/checkout.route.ts
var checkoutRouter = Router2();
checkoutRouter.post("/start", async (req, res) => {
  try {
    const { planId, addonIds = [], customer, billingType } = req.body;
    const plan = await prisma.plan.findUnique({
      where: { id: planId, isActive: true }
    });
    if (!plan) {
      res.status(404).json({ error: "Plan not found or inactive" });
      return;
    }
    const addons = addonIds.length > 0 ? await prisma.addon.findMany({
      where: { id: { in: addonIds }, isActive: true }
    }) : [];
    let existingCustomer = await prisma.customer.findUnique({
      where: { email: customer.email }
    });
    if (!existingCustomer) {
      const asaasCustomer = await asaasService.createCustomer(customer);
      existingCustomer = await prisma.customer.create({
        data: {
          ...customer,
          asaasCustomerId: asaasCustomer.id
        }
      });
    } else if (!existingCustomer.asaasCustomerId) {
      const asaasCustomer = await asaasService.createCustomer({
        name: existingCustomer.name,
        email: existingCustomer.email,
        cpfCnpj: existingCustomer.cpfCnpj || void 0,
        phone: existingCustomer.phone || void 0
      });
      existingCustomer = await prisma.customer.update({
        where: { id: existingCustomer.id },
        data: { asaasCustomerId: asaasCustomer.id }
      });
    }
    const totalValue = Number(plan.price) + addons.reduce((sum, addon) => sum + Number(addon.price), 0);
    const nextDueDate = /* @__PURE__ */ new Date();
    nextDueDate.setDate(nextDueDate.getDate() + 7);
    const asaasSubscription = await asaasService.createSubscription({
      customer: existingCustomer.asaasCustomerId,
      billingType,
      value: totalValue,
      nextDueDate: nextDueDate.toISOString().split("T")[0],
      cycle: plan.cycle,
      description: `Assinatura ${plan.name}`
    });
    const subscription = await prisma.subscription.create({
      data: {
        customerId: existingCustomer.id,
        planId: plan.id,
        asaasSubscriptionId: asaasSubscription.id,
        status: "PENDING",
        startDate: /* @__PURE__ */ new Date(),
        nextDueDate
      }
    });
    if (addons.length > 0) {
      await prisma.subscriptionAddon.createMany({
        data: addons.map((addon) => ({
          subscriptionId: subscription.id,
          addonId: addon.id,
          quantity: 1
        }))
      });
    }
    const paymentLink = await asaasService.createPaymentLink({
      customer: existingCustomer.asaasCustomerId,
      billingType,
      value: totalValue,
      dueDate: nextDueDate.toISOString().split("T")[0],
      description: `Primeira cobran\xE7a - ${plan.name}`
    });
    res.json({
      success: true,
      subscriptionId: subscription.id,
      paymentUrl: paymentLink.invoiceUrl || paymentLink.boletoUrl,
      paymentId: paymentLink.id
    });
  } catch (error) {
    console.error("Checkout error:", error);
    res.status(500).json({ error: "Failed to process checkout" });
  }
});
checkoutRouter.get("/plans", async (_req, res) => {
  try {
    const plans = await prisma.plan.findMany({
      where: { isActive: true },
      orderBy: { price: "asc" }
    });
    const addons = await prisma.addon.findMany({
      where: { isActive: true },
      orderBy: { price: "asc" }
    });
    res.json({ plans, addons });
  } catch (error) {
    console.error("Error fetching plans:", error);
    res.status(500).json({ error: "Failed to fetch plans" });
  }
});
checkoutRouter.get("/subscription/:id", async (req, res) => {
  try {
    const subscription = await prisma.subscription.findUnique({
      where: { id: req.params.id },
      include: {
        plan: true,
        customer: true,
        addons: {
          include: {
            addon: true
          }
        },
        payments: {
          orderBy: { createdAt: "desc" },
          take: 1
        }
      }
    });
    if (!subscription) {
      res.status(404).json({ error: "Subscription not found" });
      return;
    }
    res.json(subscription);
  } catch (error) {
    console.error("Error fetching subscription:", error);
    res.status(500).json({ error: "Failed to fetch subscription" });
  }
});

// src/admin/dashboard.ts
init_client();
var dashboardHandler = async () => {
  const [
    totalCustomers,
    activeSubscriptions,
    totalRevenue,
    pendingPayments,
    recentPayments
  ] = await Promise.all([
    prisma.customer.count(),
    prisma.subscription.count({
      where: { status: SubscriptionStatus2.ACTIVE }
    }),
    prisma.payment.aggregate({
      where: { status: PaymentStatus2.RECEIVED },
      _sum: { amount: true }
    }),
    prisma.payment.count({
      where: { status: PaymentStatus2.PENDING }
    }),
    prisma.payment.findMany({
      where: {
        status: PaymentStatus2.RECEIVED,
        paidAt: { not: null }
      },
      include: {
        subscription: {
          include: {
            customer: true,
            plan: true
          }
        }
      },
      orderBy: { paidAt: "desc" },
      take: 10
    })
  ]);
  const subscriptions = await prisma.subscription.findMany({
    where: { status: SubscriptionStatus2.ACTIVE },
    include: {
      plan: true,
      addons: {
        include: {
          addon: true
        }
      }
    }
  });
  const metrics = {
    mrr: calculateMRR(subscriptions),
    paymentCycles: await getPaymentCycles()
  };
  return {
    totalCustomers,
    activeSubscriptions,
    totalRevenue: Number(totalRevenue._sum.amount || 0),
    pendingPayments,
    recentPayments: recentPayments.map((payment) => ({
      id: payment.id,
      customerName: payment.subscription.customer.name,
      planName: payment.subscription.plan.name,
      amount: Number(payment.amount),
      paidAt: payment.paidAt.toISOString()
    })),
    mrr: metrics.mrr,
    metrics
  };
};
async function getPaymentCycles() {
  const plans = await prisma.plan.groupBy({
    by: ["cycle"],
    _count: { cycle: true }
  });
  return plans.reduce((acc, item) => {
    acc[item.cycle] = item._count.cycle;
    return acc;
  }, {});
}
function calculateMRR(subscriptions) {
  let mrr = 0;
  for (const subscription of subscriptions) {
    const planPrice = Number(subscription.plan.price);
    const addonPrices = subscription.addons.reduce(
      (sum, sa) => sum + Number(sa.addon.price) * sa.quantity,
      0
    );
    const totalPrice = planPrice + addonPrices;
    switch (subscription.plan.cycle) {
      case "WEEKLY":
        mrr += totalPrice * 4.33;
        break;
      case "BIWEEKLY":
        mrr += totalPrice * 2.17;
        break;
      case "MONTHLY":
        mrr += totalPrice;
        break;
      case "QUARTERLY":
        mrr += totalPrice / 3;
        break;
      case "SEMIANNUALLY":
        mrr += totalPrice / 6;
        break;
      case "YEARLY":
        mrr += totalPrice / 12;
        break;
    }
  }
  return Math.round(mrr * 100) / 100;
}
var Dashboard = {
  handler: dashboardHandler
};

// src/app.ts
validateEnv();
AdminJS.registerAdapter({ Database, Resource });
var app = express();
app.use(express.json());
app.use(express.urlencoded({ extended: true }));
app.use("/webhooks", webhookRouter);
app.use("/api/checkout", checkoutRouter);
var setupApp = async () => {
  await connectDatabase();
  app.get("/health", (_req, res) => {
    res.json({ status: "ok", timestamp: (/* @__PURE__ */ new Date()).toISOString() });
  });
  const { Prisma } = await Promise.resolve().then(() => (init_client(), client_exports));
  const dmmf = Prisma.dmmf;
  if (!dmmf || !dmmf.datamodel) {
    throw new Error("Unable to get DMMF from Prisma - no datamodel found");
  }
  const admin = new AdminJS({
    resources: setupAdminResources(dmmf),
    rootPath: "/admin",
    dashboard: Dashboard,
    branding: {
      companyName: "Numbr Billing",
      logo: false,
      theme: {
        colors: {
          primary100: "#4B5563",
          primary80: "#6B7280",
          primary60: "#9CA3AF",
          primary40: "#D1D5DB",
          primary20: "#F3F4F6",
          grey100: "#374151",
          grey80: "#6B7280",
          grey60: "#9CA3AF",
          grey40: "#D1D5DB",
          grey20: "#F3F4F6",
          filterBg: "#F9FAFB",
          accent: "#3B82F6",
          hoverBg: "#EBF5FF"
        }
      }
    }
  });
  const adminRouter = AdminJSExpress.buildAuthenticatedRouter(
    admin,
    {
      authenticate: async (email, password) => {
        if (email === config.admin.email && password === config.admin.password) {
          return { email };
        }
        return null;
      },
      cookieName: "adminjs",
      cookiePassword: "session-secret-numbr-billing-2024"
    },
    null,
    {
      store: session.MemoryStore ? new session.MemoryStore() : void 0,
      resave: true,
      saveUninitialized: true,
      secret: "session-secret-numbr-billing-2024",
      cookie: {
        httpOnly: true,
        secure: false
      }
    }
  );
  app.use(admin.options.rootPath, adminRouter);
};
var appSetupPromise = setupApp().catch((error) => {
  console.error("Failed to setup app:", error);
  if (!process.env.IS_LAMBDA) {
    process.exit(1);
  }
});
if (!process.env.IS_LAMBDA) {
  app.listen(config.port, () => {
    console.log(`Server running on http://localhost:${config.port}`);
    console.log(`AdminJS panel available at http://localhost:${config.port}/admin`);
  });
}

// src/lambda.ts
var serverlessHandler = serverless(app);
var handler = async (event, context) => {
  await appSetupPromise;
  return serverlessHandler(event, context);
};
export {
  handler
};
//# sourceMappingURL=lambda.js.map
