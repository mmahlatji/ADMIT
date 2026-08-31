import { z } from "zod";

export const createAccountSchema = z
  .object({
    employeeId: z
      .string()
      .regex(/^\d{7}$/, "Employee ID must be exactly 7 digits"),
    firstName: z
      .string()
      .min(1, "First name is required")
      .regex(/^[^\d]*$/, "First name cannot contain digits"),
    lastName: z
      .string()
      .min(1, "Surname is required")
      .regex(/^[^\d]*$/, "Surname cannot contain digits"),
    email: z
      .string()
      .email("Please enter a valid email address")
      .refine(
        (email) =>
          email.endsWith("@myuct.ac.za") || email.endsWith("@uct.ac.za"),
        "Please use a valid UCT email address.",
      ),
    password: z
      .string()
      .min(8, "Password must be at least 8 characters")
      .regex(/[A-Z]/, "Password must contain at least one uppercase letter")
      .regex(/[a-z]/, "Password must contain at least one lowercase letter")
      .regex(/\d/, "Password must contain at least one number"),
    confirmPassword: z.string(),
  })
  .refine((data) => data.password === data.confirmPassword, {
    message: "Passwords do not match",
    path: ["confirmPassword"],
  });

export type CreateAccountFormData = z.infer<typeof createAccountSchema>;

export const signInSchema = z.object({
  email: z.string().email("Please enter a valid email address"),
  password: z.string().min(1, "Password is required"),
});

export type SignInFormData = z.infer<typeof signInSchema>;
