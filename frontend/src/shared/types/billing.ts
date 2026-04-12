export type BillingInterval = "monthly" | "yearly";
export type SubscriptionStatus = "trialing" | "active" | "past_due" | "canceled" | "expired";
export type BillingTransactionStatus = "pending" | "succeeded" | "failed" | "refunded" | "canceled";
export type BillingTransactionType = "subscription" | "token_purchase" | "adjustment" | "refund";
export type TokenWalletStatus = "active" | "frozen" | "closed";
export type TokenLedgerEntryType = "credit" | "debit" | "reserve" | "release" | "expire" | "adjustment";
export type TokenAllocationType = "monthly_free" | "purchased" | "manual";

export type FeatureCatalogItem = {
  id: number;
  code: string;
  name: string;
  description: string | null;
  value_type: string;
  unit_label: string | null;
  is_active: boolean;
  metadata_json: Record<string, unknown>;
  created_at: string;
  updated_at: string;
};

export type PlanFeature = {
  feature: FeatureCatalogItem;
  included_value: string;
  overage_price_usd: string | null;
  config_json: Record<string, unknown>;
};

export type BillingPlan = {
  id: number;
  code: string;
  name: string;
  description: string | null;
  billing_interval: BillingInterval;
  setup_fee_usd: string;
  price_usd: string;
  monthly_token_credit: number;
  is_active: boolean;
  metadata_json: Record<string, unknown>;
  created_at: string;
  updated_at: string;
  features: PlanFeature[];
};

export type BillingPlanList = {
  items: BillingPlan[];
  total: number;
};

export type FeatureCatalogList = {
  items: FeatureCatalogItem[];
  total: number;
};

export type AccountSubscription = {
  id: number;
  account_id: number;
  billing_plan_id: number;
  status: SubscriptionStatus;
  starts_at: string;
  ends_at: string | null;
  renews_at: string | null;
  canceled_at: string | null;
  external_subscription_id: string | null;
  metadata_json: Record<string, unknown>;
  created_at: string;
  updated_at: string;
  plan: BillingPlan;
};

export type TokenPackage = {
  id: number;
  code: string;
  name: string;
  description: string | null;
  token_amount: number;
  bonus_tokens: number;
  price_usd: string;
  currency: string;
  is_active: boolean;
  metadata_json: Record<string, unknown>;
  created_at: string;
  updated_at: string;
};

export type TokenPackageList = {
  items: TokenPackage[];
  total: number;
};

export type BillingTransaction = {
  id: number;
  account_id: number;
  account_subscription_id: number | null;
  token_purchase_package_id: number | null;
  transaction_type: BillingTransactionType;
  status: BillingTransactionStatus;
  provider_name: string | null;
  external_reference: string | null;
  currency: string;
  amount_usd: string;
  tax_usd: string;
  total_amount_usd: string;
  occurred_at: string;
  paid_at: string | null;
  failed_at: string | null;
  metadata_json: Record<string, unknown>;
  created_at: string;
  updated_at: string;
};

export type BillingTransactionList = {
  items: BillingTransaction[];
  total: number;
};

export type TokenLedgerEntry = {
  id: number;
  token_wallet_id: number;
  account_id: number;
  account_subscription_id: number | null;
  billing_transaction_id: number | null;
  entry_type: TokenLedgerEntryType;
  source_type: string;
  allocation_type: TokenAllocationType | null;
  delta_tokens: number;
  balance_before: number;
  balance_after: number;
  remaining_tokens: number | null;
  expires_at: string | null;
  expired_at: string | null;
  is_expired: boolean;
  unit_price_usd: string | null;
  total_price_usd: string | null;
  reference_type: string | null;
  reference_id: string | null;
  notes: string | null;
  occurred_at: string;
  metadata_json: Record<string, unknown>;
  created_at: string;
  updated_at: string;
};

export type TokenLedgerList = {
  items: TokenLedgerEntry[];
  total: number;
};

export type TokenWallet = {
  id: number;
  account_id: number;
  status: TokenWalletStatus;
  balance_tokens: number;
  reserved_tokens: number;
  lifetime_credited_tokens: number;
  lifetime_debited_tokens: number;
  metadata_json: Record<string, unknown>;
  created_at: string;
  updated_at: string;
};

export type TokenBalanceBreakdown = {
  available_monthly_free_tokens: number;
  available_purchased_tokens: number;
  available_manual_tokens: number;
  total_available_tokens: number;
  expiring_next_tokens: number;
};

export type WalletBalance = {
  wallet: TokenWallet;
  breakdown: TokenBalanceBreakdown;
};
