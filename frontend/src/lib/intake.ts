// What counts as an intake year, in one place so the pages that default to it
// cannot drift apart. Mirrors intake_year_bounds in
// backend/app/queries/applications.py: an intake is applied for during the
// year before it starts, so the cycle being worked on now is next year's.
export function currentIntakeYear(today: Date = new Date()): number {
  return today.getFullYear() + 1;
}
