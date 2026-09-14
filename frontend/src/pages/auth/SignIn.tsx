import { useState } from "react";
import { Alert, Anchor, Button, PasswordInput, Stack, TextInput } from "@mantine/core";
import { useForm } from "@mantine/form";
import { zod4Resolver } from "mantine-form-zod-resolver";
import { CircleAlert } from "lucide-react";
import { Link, Navigate, useNavigate } from "react-router-dom";
import { useAuth } from "../../context/AuthContext";
import { signIn } from "../../lib/auth";
import { signInSchema, type SignInFormData } from "../../schemas/auth";
import AuthLayout from "./AuthLayout";

export default function SignIn() {
  const { session } = useAuth();
  const navigate = useNavigate();
  const [authError, setAuthError] = useState<string | null>(null);

  const form = useForm<SignInFormData>({
    mode: "uncontrolled",
    initialValues: { email: "", password: "" },
    validate: zod4Resolver(signInSchema),
  });

  async function onSubmit(values: SignInFormData) {
    setAuthError(null);
    try {
      await signIn(values.email, values.password);
      navigate("/");
    } catch (error) {
      console.error(error);
      // Deliberately not distinguishing unknown email from wrong password:
      // that difference tells an outsider which addresses have accounts.
      setAuthError("Incorrect email or password.");
    }
  }

  // <Navigate> rather than calling navigate() during render. The old version
  // redirected as a side effect of rendering, which paired with ProtectedRoute
  // to make an infinite /signin <-> /dashboard loop whenever a session existed
  // but the user had not been fetched yet.
  if (session) return <Navigate to="/" replace />;

  return (
    <AuthLayout title="Sign in" subtitle="Use your UCT account.">
      <form onSubmit={form.onSubmit(onSubmit)} noValidate>
        <Stack gap="md">
          {authError && (
            <Alert
              color="red"
              variant="light"
              icon={<CircleAlert size={18} />}
              title="Could not sign you in"
            >
              {authError}
            </Alert>
          )}

          <TextInput
            withAsterisk
            label="Email"
            type="email"
            autoComplete="email"
            placeholder="you@uct.ac.za"
            key={form.key("email")}
            {...form.getInputProps("email")}
          />

          <PasswordInput
            withAsterisk
            label="Password"
            autoComplete="current-password"
            key={form.key("password")}
            {...form.getInputProps("password")}
          />

          <Button type="submit" loading={form.submitting} fullWidth mt="xs">
            Sign in
          </Button>

          <Anchor component={Link} to="/signup" size="sm" ta="center">
            No account yet? Create one
          </Anchor>
        </Stack>
      </form>
    </AuthLayout>
  );
}
