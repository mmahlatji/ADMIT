import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { signIn } from "../../lib/auth";
import "./SignIn.css";
import { useNavigate } from "react-router-dom";
import { useState } from "react";
import { useAuth } from "../../context/AuthContext";

import { signInSchema, type SignInFormData } from "../../schemas/auth";

export default function SignIn() {
  const { session } = useAuth();
  const navigate = useNavigate();

  if (session) {
    navigate("/dashboard");
  }
  const [authError, setAuthError] = useState<string | null>(null);
  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<SignInFormData>({
    resolver: zodResolver(signInSchema),
  });

  async function onSubmit(data: SignInFormData) {
    try {
      await signIn(data.email, data.password);
      navigate("/dashboard");
    } catch (error) {
      console.error(error);
      setAuthError("Incorrect email or password");
    }
  }

  return (
    <div className="sign-in-page">
      <div className="sign-in-card">
        <div className="sign-in-header">
          <h1>Sign In</h1>
        </div>
        <form onSubmit={handleSubmit(onSubmit)} className="sign-in-form">
          {authError && <p className="error-message auth-error">{authError}</p>}
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
          <div className="btn-group">
            <p>
              Don't have an account? <a href="/signup">sign up</a>
            </p>

            <button
              type="submit"
              disabled={isSubmitting}
              className="auth-button"
            >
              {isSubmitting ? "Signing In..." : "Sign In"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
