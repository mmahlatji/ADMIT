import { useState } from "react";
import {
  Alert,
  Anchor,
  Button,
  Group,
  PasswordInput,
  Stack,
  Text,
  TextInput,
} from "@mantine/core";
import { useForm } from "@mantine/form";
import { zod4Resolver } from "mantine-form-zod-resolver";
import { CircleAlert, MailCheck } from "lucide-react";
import { Link, useNavigate } from "react-router-dom";
import { signUp } from "../../lib/auth";
import {
  createAccountSchema,
  type CreateAccountFormData,
} from "../../schemas/auth";
import AuthLayout from "./AuthLayout";

export default function CreateAccount() {
  const navigate = useNavigate();
  const [error, setError] = useState<string | null>(null);
  const [confirmEmail, setConfirmEmail] = useState<string | null>(null);

  const form = useForm<CreateAccountFormData>({
    mode: "uncontrolled",
    initialValues: {
      employeeId: "",
      firstName: "",
      lastName: "",
      email: "",
      password: "",
      confirmPassword: "",
    },
    validate: zod4Resolver(createAccountSchema),
  });

  async function onSubmit(values: CreateAccountFormData) {
    setError(null);
    try {
      // employee_id, first_name and last_name go into the Supabase user's
      // metadata, and the backend reads them straight off the JWT claims in
      // get_or_create_user. Without employee_id every request 403s, and it is
      // the id notes, rules, imports and audit entries are attributed to.
      const result = await signUp(
        values.email,
        values.password,
        values.firstName,
        values.lastName,
        values.employeeId,
      );

      if (result.session) {
        navigate("/", { replace: true });
        return;
      }

      // No session means the project requires email confirmation. The old
      // build fell through silently here and looked like nothing happened.
      setConfirmEmail(values.email);
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Could not create the account.",
      );
    }
  }

  if (confirmEmail) {
    return (
      <AuthLayout
        title="Check your email"
        subtitle="One step left before a convenor can approve you."
      >
        <Alert
          color="uct"
          variant="light"
          icon={<MailCheck size={18} />}
          title="Confirm your address"
        >
          <Text size="sm">
            We sent a confirmation link to <strong>{confirmEmail}</strong>.
            Open it, then sign in. A convenor assigns your role after that.
          </Text>
        </Alert>
        <Button component={Link} to="/signin" variant="default" fullWidth>
          Back to sign in
        </Button>
      </AuthLayout>
    );
  }

  return (
    <AuthLayout
      title="Create account"
      subtitle="Accounts start with no access. A convenor grants your role once the account exists."
    >
      <form onSubmit={form.onSubmit(onSubmit)} noValidate>
        <Stack gap="md">
          {error && (
            <Alert
              color="red"
              variant="light"
              icon={<CircleAlert size={18} />}
              title="Could not create the account"
            >
              {error}
            </Alert>
          )}

          <TextInput
            withAsterisk
            label="Employee ID"
            description="Seven digits, as it appears on your staff card"
            inputMode="numeric"
            maxLength={7}
            placeholder="1234567"
            key={form.key("employeeId")}
            {...form.getInputProps("employeeId")}
          />

          <Group grow align="flex-start">
            <TextInput
              withAsterisk
              label="First name"
              autoComplete="given-name"
              key={form.key("firstName")}
              {...form.getInputProps("firstName")}
            />
            <TextInput
              withAsterisk
              label="Surname"
              autoComplete="family-name"
              key={form.key("lastName")}
              {...form.getInputProps("lastName")}
            />
          </Group>

          <TextInput
            withAsterisk
            label="Email"
            type="email"
            autoComplete="email"
            description="A uct.ac.za or myuct.ac.za address"
            placeholder="you@uct.ac.za"
            key={form.key("email")}
            {...form.getInputProps("email")}
          />

          <PasswordInput
            withAsterisk
            label="Password"
            autoComplete="new-password"
            description="At least 8 characters, with an uppercase letter, a lowercase letter and a number"
            key={form.key("password")}
            {...form.getInputProps("password")}
          />

          <PasswordInput
            withAsterisk
            label="Confirm password"
            autoComplete="new-password"
            key={form.key("confirmPassword")}
            {...form.getInputProps("confirmPassword")}
          />

          <Button type="submit" loading={form.submitting} fullWidth mt="xs">
            Create account
          </Button>

          <Anchor component={Link} to="/signin" size="sm" ta="center">
            Already have an account? Sign in
          </Anchor>
        </Stack>
      </form>
    </AuthLayout>
  );
}
