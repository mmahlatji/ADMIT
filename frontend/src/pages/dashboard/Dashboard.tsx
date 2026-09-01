import { useAuth } from "../../context/AuthContext";
import { dashboardTiles } from "../../config/dashboardTiles";
import DashboardTile from "../../components/DashboardTile";
import "./Dashboard.css";
import Header from "../../components/Header";

export default function Dashboard() {
  const { user } = useAuth();

  if (!user || !user.role) {
    // shouldn't normally hit this if ProtectedRoute is doing its job,
    // but a safe fallback is cheap insurance
    return null;
  }

  // Filtering was commented out, so every role saw every tile: a committee
  // member was shown Assign roles and Upload documents, both of which the API
  // refuses. Showing someone a door that will not open is worse than not
  // showing it, and the tile config already says who each one is for.
  const visibleTiles = dashboardTiles.filter((tile) =>
    tile.roles.includes(user.role!),
  );

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
