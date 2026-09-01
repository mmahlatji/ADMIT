import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import CreateAccount from "./pages/auth/CreateAccount";
import SignIn from "./pages/auth/SignIn";
import { AuthProvider, useAuth } from "./context/AuthContext";
import Dashboard from "./pages/dashboard/Dashboard";
import { FileUpload } from "./pages/uploads/FileUpload";
import Decisions from "./pages/work/Decisions";
import Reviews from "./pages/work/Reviews";
import Workspace from "./pages/work/Workspace";
import Roles from "./pages/work/Roles";
import RulesPage from "./pages/work/Rules";

function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { session, user, loading } = useAuth();

  if (loading) return <div>Loading...</div>; //for now
  if (!session) return <Navigate to="/signin" replace />;
  // no user means /users/me failed, not that they're allowed through: the old
  // `user && user.role === null` check skipped entirely when user was null,
  // so a failed lookup rendered the page as if the person were approved
  if (!user) return <Navigate to="/signin" replace />;
  if (user.role === null) return <Navigate to="/signup" replace />;
  return <>{children}</>;
}

function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <Routes>
          <Route path="/signup" element={<CreateAccount />} />
          <Route path="/signin" element={<SignIn />} />
          <Route
            path="/dashboard"
            element={
              <ProtectedRoute>
                <Dashboard />
              </ProtectedRoute>
            }
          />
          <Route
            path="/file-upload"
            element={
              <ProtectedRoute>
                <FileUpload />
              </ProtectedRoute>
            }
          />
          <Route
            path="/decisions"
            element={
              <ProtectedRoute>
                <Decisions />
              </ProtectedRoute>
            }
          />
          <Route
            path="/matching-reviews"
            element={
              <ProtectedRoute>
                <Reviews />
              </ProtectedRoute>
            }
          />
          <Route
            path="/workspace"
            element={
              <ProtectedRoute>
                <Workspace />
              </ProtectedRoute>
            }
          />
          <Route
            path="/assign"
            element={
              <ProtectedRoute>
                <Roles />
              </ProtectedRoute>
            }
          />
          <Route
            path="/rules"
            element={
              <ProtectedRoute>
                <RulesPage />
              </ProtectedRoute>
            }
          />
          {/* Anything unrecognised goes back to the dashboard rather than
              rendering a blank screen. */}
          <Route path="*" element={<Navigate to="/dashboard" replace />} />
        </Routes>
      </AuthProvider>
    </BrowserRouter>
  );
}

export default App;
