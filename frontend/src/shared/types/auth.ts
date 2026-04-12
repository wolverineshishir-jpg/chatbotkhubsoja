export type MembershipRole = "owner" | "admin";
export type MembershipStatus = "active" | "invited" | "revoked";
export type UserStatus = "active" | "invited" | "disabled";
export type UserRole = MembershipRole | "superAdmin";

export type MembershipSummary = {
  id: number;
  account_id: number;
  account_name: string;
  account_slug: string;
  role: MembershipRole;
  status: MembershipStatus;
};

export type AuthUser = {
  id: number;
  email: string;
  full_name: string | null;
  status: UserStatus;
  user_role: UserRole;
  is_superuser: boolean;
  permissions: string[];
  memberships: MembershipSummary[];
};

export type AuthSession = {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
  user: AuthUser;
};
