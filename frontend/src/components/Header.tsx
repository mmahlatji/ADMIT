import { useAuth } from "../context/AuthContext";
import "./Header.css";

export default function Header({ title = "ADMIT" }: { title?: string }) {
  const { user } = useAuth(); // expects { firstName, lastName, role }

  const initials = user
    ? `${user.first_name?.[0] ?? ""}${user.last_name?.[0] ?? ""}`.toUpperCase()
    : "";

  return (
    <header className="app-header">
      <div className="app-header__brand">
        <a href="/dashboard">
          <span className="app-header__title">{title}</span>
        </a>
      </div>
      <div>
        <span className="app-header__subtitle">University of Cape Town</span>
      </div>

      {user && (
        <div className="app-header__user">
          <div className="app-header__user-info">
            <span className="app-header__user-name">
              {user.first_name} {user.last_name}
            </span>
            <span className="app-header__user-role">{user.role}</span>
          </div>
          <div className="app-header__avatar">{initials}</div>
        </div>
      )}
    </header>
  );
}
