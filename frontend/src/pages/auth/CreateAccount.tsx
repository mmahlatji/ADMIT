import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import {
  createAccountSchema,
  type CreateAccountFormData,
} from "../../schemas/auth";
import { signUp } from "../../lib/auth";
import { useNavigate } from "react-router-dom";
import "./CreateAccount.css";

export default function CreateAccount() {
  const navigate = useNavigate();
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<CreateAccountFormData>({
    resolver: zodResolver(createAccountSchema),
  });

  async function onSubmit(data: CreateAccountFormData) {
    try {
      const result = await signUp(
        data.email,
        data.password,
        data.firstName,
        data.lastName,
        data.employeeId,
      );
      console.log(result);

      if (result.session) {
        navigate("/dashboard");
      }
    } catch (error) {
      console.error("Failed to create account", error);
    }
  }

  return (
    <div className="create-account-page">
      <div className="create-account-card">
        <div className="create-account-header">
          <h1>Create Account</h1>
          <p>Create an account for convenor approval</p>
        </div>
        <form onSubmit={handleSubmit(onSubmit)} className="create-account-form">
          <div className="form-group">
            {" "}
            <label htmlFor="emloyeeId">Employee ID</label>
            <input {...register("employeeId")} placeholder="Employee ID" />
            {errors.employeeId && (
              <p className="error-message">{errors.employeeId.message}</p>
            )}
          </div>

          <div className="form-group">
            {" "}
            <label htmlFor="firstName">First Name</label>
            <input {...register("firstName")} placeholder="First name" />
            {errors.firstName && (
              <p className="error-message">{errors.firstName.message}</p>
            )}
          </div>

          <div className="form-group">
            {" "}
            <label htmlFor="lastName">Last Name</label>
            <input {...register("lastName")} placeholder="Last Name" />
            {errors.lastName && (
              <p className="error-message">{errors.lastName.message}</p>
            )}
          </div>

          <div className="form-group">
            {" "}
            <label htmlFor="email">Email</label>
            <input {...register("email")} placeholder="Email" type="email" />
            {errors.email && (
              <p className="error-message">{errors.email.message}</p>
            )}
          </div>

          <div className="form-group">
            {" "}
            <label htmlFor="password">Password</label>
            <input
              {...register("password")}
              placeholder="Password"
              type="password"
            />
            {errors.password && (
              <p className="error-message">{errors.password.message}</p>
            )}
          </div>

          <div className="form-group">
            {" "}
            <label htmlFor="confirmPassword">Confirm password</label>
            <input
              {...register("confirmPassword")}
              placeholder="Confirm password"
              type="password"
            />
            {errors.confirmPassword && (
              <p className="error-message">{errors.confirmPassword.message}</p>
            )}
          </div>

          <button type="submit" className="auth-button">
            Create Account
          </button>
        </form>
      </div>
    </div>
  );
}
