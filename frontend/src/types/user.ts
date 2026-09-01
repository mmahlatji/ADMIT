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

export type ApplicationStatus =
  | "Applied"
  | "Reviewed"
  | "Conditional Offer"
  | "Accepted"
  | "Ready to Register"
  | "Denied"
  | "Cancelled";

export type DenyReason =
  | "Not competitive"
  | "Requirements not met"
  | "Duplicate application"
  | "Incorrect program";

export type Application = {
  application_id: string;
  application_number: string;
  campus_id: string;
  academic_program_code: string;
  academic_plan1: string;
  choice: string;
  application_status: ApplicationStatus;
  application_status_reason: DenyReason | null;
  incorrect_plan: boolean;
  duplicate_application: boolean;
  requires_plan_correction: boolean;
  application_date: string;
  effective_date: string;
};

export type Applicant = {
  campus_id: string;
  employee_id: string;
  title: string;
  first_name: string;
  last_name: string;
  email: string | null;
  citizenship_residency: string;
};

export type ApplicantMark = {
  campus_id: string;
  course_code: string;
  mark: number;
  result_code: string;
};

export type ApplicantDetail = Applicant & {
  applications: Application[];
  applicant_marks: ApplicantMark[];
  motivation: { motivation: string | null } | null;
  notes: { note_id: string; content: string; author_id: string }[];
};

export type MatchingReview = {
  match_id: string;
  staging_row_id: string;
  status: "pending" | "resolved";
  reason: string | null;
  resolution: "merge" | "reject" | null;
  resolved_by: string | null;
  resolved_at: string | null;
};

export type Rule = {
  rule_id: string;
  institution: string;
  intake_year: number;
  version: number;
  rule: string;
  status: string;
  created_by: string;
  created_at: string;
};

export type RulePreview = {
  first_rule: boolean;
  after: number;
  pass_rate_after: number;
  not_evaluable: number;
  before: number | null;
  change: number | null;
  pct_change: number | null;
  pass_rate_before: number | null;
};
