import { lazy, Suspense } from "react";
import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";
import { AuthProvider } from "./context/AuthContext";
import AppLayout from "./app/AppLayout";
import ProtectedRoute from "./app/ProtectedRoute";
import { LoadingState } from "./components/States";
import { CONVENOR_ADMIN, CONVENOR_ONLY } from "./lib/roles";

import SignIn from "./pages/auth/SignIn";
import CreateAccount from "./pages/auth/CreateAccount";
import PendingApproval from "./pages/PendingApproval";

// Split per route. The whole app in one chunk was 780 kB, and most of it is
// pages a given role never opens.
const Overview = lazy(() => import("./pages/overview/Overview"));
const Applicants = lazy(() => import("./pages/applicants/Applicants"));
const ApplicantDetail = lazy(
  () => import("./pages/applicants/ApplicantDetail"),
);
const Decisions = lazy(() => import("./pages/decisions/Decisions"));
const Rules = lazy(() => import("./pages/rules/Rules"));
const Imports = lazy(() => import("./pages/imports/Imports"));
const Conflicts = lazy(() => import("./pages/conflicts/Conflicts"));
const People = lazy(() => import("./pages/people/People"));
const Audit = lazy(() => import("./pages/audit/Audit"));

export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <Suspense fallback={<LoadingState />}>
          <Routes>
            <Route path="/signin" element={<SignIn />} />
            <Route path="/signup" element={<CreateAccount />} />
            <Route path="/pending" element={<PendingApproval />} />

            <Route
              element={
                <ProtectedRoute>
                  <AppLayout />
                </ProtectedRoute>
              }
            >
              <Route index element={<Overview />} />
              <Route path="applicants" element={<Applicants />} />
              <Route
                path="applicants/:campusId"
                element={<ApplicantDetail />}
              />
              <Route path="decisions" element={<Decisions />} />
              <Route path="rules" element={<Rules />} />
              <Route
                path="imports"
                element={
                  <ProtectedRoute allowed={CONVENOR_ADMIN}>
                    <Imports />
                  </ProtectedRoute>
                }
              />
              <Route
                path="conflicts"
                element={
                  <ProtectedRoute allowed={CONVENOR_ADMIN}>
                    <Conflicts />
                  </ProtectedRoute>
                }
              />
              <Route
                path="audit"
                element={
                  <ProtectedRoute allowed={CONVENOR_ADMIN}>
                    <Audit />
                  </ProtectedRoute>
                }
              />
              <Route
                path="people"
                element={
                  <ProtectedRoute allowed={CONVENOR_ONLY}>
                    <People />
                  </ProtectedRoute>
                }
              />
            </Route>

            {/* Anything unrecognised goes back to the overview rather than
                rendering a blank screen. */}
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </Suspense>
      </AuthProvider>
    </BrowserRouter>
  );
}
