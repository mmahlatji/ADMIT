import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import CreateAccount from "./pages/auth/CreateAccount";
import SignIn from "./pages/auth/SignIn";
import { AuthProvider, useAuth } from "./context/AuthContext";
import Dashboard from "./pages/dashboard/Dashboard";
import { FileUpload } from "./pages/uploads/FileUpload";

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
          {/* Several dashboard tiles point at pages that aren't built yet.
              Without this they render a blank screen, since no route matches. */}
          <Route path="*" element={<Navigate to="/dashboard" replace />} />
        </Routes>
      </AuthProvider>
    </BrowserRouter>
  );
}

export default App;
