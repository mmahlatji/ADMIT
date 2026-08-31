export type Role = "admin" | "convenor" | "committee" | null;

export type User = {
  user_id: string;
  employee_id: string | null;
  first_name: string | null;
  last_name: string | null;
  email: string;
  role: Role | null;
  approved_at: string | null;
  created_at: string;
};
