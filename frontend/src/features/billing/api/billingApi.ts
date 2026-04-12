import { apiClient } from "../../../lib/api/client";
import type {
  AccountSubscription,
  BillingPlanList,
  BillingTransaction,
  BillingTransactionList,
  FeatureCatalogList,
  SubscriptionStatus,
  TokenLedgerList,
  TokenPackage,
  TokenPackageList,
  WalletBalance,
} from "../../../shared/types/billing";

export async function listBillingPlans(): Promise<BillingPlanList> {
  const response = await apiClient.get<BillingPlanList>("/billing/plans");
  return response.data;
}

export async function listBillingFeatures(): Promise<FeatureCatalogList> {
  const response = await apiClient.get<FeatureCatalogList>("/billing/features");
  return response.data;
}

export async function getAccountSubscription(): Promise<AccountSubscription | null> {
  const response = await apiClient.get<AccountSubscription | null>("/billing/subscription");
  return response.data;
}

export async function createAccountSubscription(payload: {
  billing_plan_code: string;
  status?: SubscriptionStatus;
}): Promise<AccountSubscription> {
  const response = await apiClient.post<AccountSubscription>("/billing/subscription", payload);
  return response.data;
}

export async function updateAccountSubscription(payload: {
  billing_plan_code: string;
  status?: SubscriptionStatus;
}): Promise<AccountSubscription> {
  const response = await apiClient.put<AccountSubscription>("/billing/subscription", payload);
  return response.data;
}

export async function getWalletBalance(): Promise<WalletBalance> {
  const response = await apiClient.get<WalletBalance>("/billing/wallet");
  return response.data;
}

export async function listBillingTransactions(): Promise<BillingTransactionList> {
  const response = await apiClient.get<BillingTransactionList>("/billing/transactions");
  return response.data;
}

export async function listTokenLedgerEntries(): Promise<TokenLedgerList> {
  const response = await apiClient.get<TokenLedgerList>("/billing/token-ledger");
  return response.data;
}

export async function listTokenPackages(): Promise<TokenPackageList> {
  const response = await apiClient.get<TokenPackageList>("/billing/token-packages");
  return response.data;
}

export async function createTokenPackage(payload: {
  code: string;
  name: string;
  description?: string;
  token_amount: number;
  bonus_tokens?: number;
  price_usd: number;
  currency?: string;
}): Promise<TokenPackage> {
  const response = await apiClient.post<TokenPackage>("/billing/token-packages", payload);
  return response.data;
}

export async function purchaseTokenPackage(packageCode: string): Promise<BillingTransaction> {
  const response = await apiClient.post<BillingTransaction>("/billing/token-purchases", { package_code: packageCode });
  return response.data;
}
