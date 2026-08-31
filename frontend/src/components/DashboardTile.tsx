// components/DashboardTile.tsx
import { Link } from "react-router-dom";
import "../pages/dashboard/Dashboard.css";

type DashboardTileProps = {
  title: string;
  icon: React.ReactNode;
  status?: string; // e.g. "MWLCHE003", "No current tasks", "Not Available"
  to?: string; // route to navigate to; omit if disabled
  disabled?: boolean;
};

export default function DashboardTile({
  title,
  icon,
  status,
  to,
  disabled,
}: DashboardTileProps) {
  const content = (
    <div className={`dashboard-tile ${disabled ? "disabled" : ""}`}>
      <h3 className="tile-title">{title}</h3>
      <div className="tile-title">{icon}</div>
      {status && <p className="dashboard-tile-status">{status}</p>}
    </div>
  );

  if (disabled || !to) return content;

  return <Link to={to}>{content}</Link>;
}
