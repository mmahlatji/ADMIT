// Mirrors app/schemas/*.py. Where a field is optional here it is optional
// there; the previous hand-written types were narrower than what the API
// actually returns, so half the applicant record was invisible to the UI.

export type Role = "admin" | "convenor" | "committee";

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

export const APPLICATION_STATUSES = [
  "Applied",
  "Reviewed",
  "Conditional Offer",
  "Accepted",
  "Ready to Register",
  "Denied",
  "Cancelled",
] as const;
export type ApplicationStatus = (typeof APPLICATION_STATUSES)[number];

// Denying without one of these is a 400 from the API, so the UI has to ask.
export const DENY_REASONS = [
  "Not competitive",
  "Requirements not met",
  "Duplicate application",
  "Incorrect program",
] as const;
export type DenyReason = (typeof DENY_REASONS)[number];

export type Choice = "FRST" | "SCND";
export type Semester = "1st Semester" | "2nd Semester" | "unspecified";
export type Title = "Mr" | "Ms" | "Miss" | "Unspecified";
export type Sex = "M" | "F";
export type CitizenshipResidency =
  | "SA Citizen"
  | "International"
  | "Permanent Resident";
export type ResultCode = "PA" | "DE" | "OSS" | "AB" | "F" | "S" | "NONE";

export type Application = {
  application_id: string;
  application_number: string;
  campus_id: string;
  academic_program_code: string;
  academic_plan1: string;
  choice: Choice;
  application_status: ApplicationStatus;
  application_date: string;
  effective_date: string;
  semester: Semester | null;
  last_registration: string | null;
  previous_application_term: number | null;
  incorrect_plan: boolean;
  duplicate_application: boolean;
  application_status_reason: DenyReason | null;
  requires_plan_correction: boolean;
  created_at: string;
};

export type Applicant = {
  applicant_id: string;
  campus_id: string;
  employee_id: string;
  title: Title;
  first_name: string;
  last_name: string;
  citizenship_residency: CitizenshipResidency;
  sex: Sex | null;
  cell_phone: string | null;
  home_phone: string | null;
  email: string | null;
  population_group: string | null;
  birth_date: string | null;
  non_sa_citizenship: string | null;
  created_at: string;
};

export type ApplicantMark = {
  mark_id: string;
  campus_id: string;
  course_code: string;
  mark: number;
  result_code: ResultCode;
  created_at: string;
};

export type Motivation = {
  motivation_id: string;
  campus_id: string;
  first_name: string;
  last_name: string;
  motivation: string | null;
};

export type Note = {
  note_id: string;
  campus_id: string;
  /** The author's employee_id, not their user_id. */
  author_id: string;
  content: string;
  created_at: string;
};

export type ApplicantDetail = Applicant & {
  applications: Application[];
  applicant_marks: ApplicantMark[];
  motivation: Motivation | null;
  notes: Note[];
};

export type VoteDecision = "yes" | "no" | "abstain";

export type Vote = {
  vote_id: string;
  application_number: string;
  campus_id: string;
  vote: VoteDecision;
  /** The voter's employee_id. */
  voter_id: string;
  voted_at: string;
};

export type MatchStatus = "pending" | "resolved";
export type MatchResolution = "merge" | "reject";

export type MatchingReview = {
  match_id: string;
  staging_row_id: string;
  status: MatchStatus;
  candidate_keys: Record<string, unknown> | null;
  match_signals: Record<string, unknown> | null;
  resolved_by: string | null;
  resolution: MatchResolution | null;
  reason: string | null;
  resolved_at: string | null;
};

export const SOURCE_TYPES = [
  "asr",
  "uct_marks",
  "motivations",
  "it_transcripts",
] as const;
export type SourceType = (typeof SOURCE_TYPES)[number];
export type ImportStatus = "pending" | "processing" | "completed" | "failed";

export type ImportRun = {
  import_run_id: string;
  source_type: SourceType;
  /** The uploader's employee_id. */
  uploaded_by: string;
  file_name: string;
  status: ImportStatus;
  rows_total: number;
  rows_loaded: number;
  rows_rejected: number;
  rows_auto_matched: number;
  rows_auto_new: number;
  rows_flagged: number;
  uploaded_at: string;
};

export type ChangeSource =
  | "import"
  | "manual_edit"
  | "merge_resolution"
  | "rules_calc"
  | "decision";

export type SystemLog = {
  log_id: string;
  entity_name: string;
  entity_id: string;
  /** The actor's employee_id. */
  changed_by: string;
  reason: ChangeSource;
  old_data: Record<string, unknown> | null;
  new_data: Record<string, unknown> | null;
  import_run_id: string | null;
  changed_at: string;
};

export type Institution = "University of Cape Town" | "University of Johannesburg";
export type RuleStatus = "active" | "inactive" | "expired";

export type Rule = {
  rule_id: string;
  institution: Institution;
  intake_year: number;
  version: number;
  rule: string;
  status: RuleStatus;
  created_by: string;
  created_at: string;
};

export type RulePreview = {
  first_rule: boolean;
  after: number;
  not_evaluable: number;
  pass_rate_after: number;
  before: number | null;
  change: number | null;
  pct_change: number | null;
  pass_rate_before: number | null;
};

/** The only variables app/services/rule_engine.py will accept. */
export const RULE_VARIABLES = [
  "csc2001f",
  "csc2002s",
  "csc3002f",
  "csc3003s",
] as const;
