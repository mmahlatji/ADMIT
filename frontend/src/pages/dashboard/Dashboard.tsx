import { useAuth } from "../../context/AuthContext";
import { dashboardTiles } from "../../config/dashboardTiles";
import DashboardTile from "../../components/DashboardTile";
import "./Dashboard.css";
import Header from "../../components/Header";

export default function Dashboard() {
  const { user } = useAuth();

  // if (!user || !user.role) {
  //   // shouldn't normally hit this if ProtectedRoute is doing its job,
  //   // but a safe fallback is cheap insurance
  //   return null;
  // }

  // const visibleTiles = dashboardTiles.filter((tile) =>
  //   tile.roles.includes(user.role!),
  // );

  const visibleTiles = dashboardTiles;

  return (
    <div className="dashboard">
      <Header />
      <div className="dashboard-grid-container">
        <div className="dashboard-grid">
          {visibleTiles.map((tile) => (
            <DashboardTile
              key={tile.title}
              title={tile.title}
              icon={tile.icon}
              to={tile.to}
            />
          ))}
        </div>
      </div>
    </div>
  );
}
