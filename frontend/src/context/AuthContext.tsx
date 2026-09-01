//responsible for creating context so that we dont need to pass down the user, session an loading state down elem
import { createContext, useContext, useEffect, useState } from "react";
import type { Session } from "@supabase/supabase-js";
import { supabase } from "../lib/supabaseClient";
import type { User } from "../types/user";
import { api } from "../lib/api";
import { setCurrentSession } from "../lib/authStore";

type AuthContextType = {
  session: Session | null;
  user: User | null;
  loading: boolean;
};

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [loading, setLoading] = useState(true);
  const [user, setUser] = useState<User | null>(null);
  const [session, setSession] = useState<Session | null>(null);

  async function loadUser() {
    try {
      const currentUser = await api.request<User>("/users/me");
      setUser(currentUser);
    } catch (error) {
      console.error("Failed to load user:", error);
      setUser(null);
    }
  }

  useEffect(() => {
    supabase.auth.getSession().then(async ({ data }) => {
      const session = data.session;

      setSession(session);
      setCurrentSession(session);

      if (session) {
        await loadUser();
      }
      setLoading(false);
    });
    //handle a session change
    const {
      data: { subscription },
    } = supabase.auth.onAuthStateChange((_event, session) => {
      setTimeout(async () => {
        // loading has to go back up while the new session's user is fetched.
        // Without it there is a render where session is set but user is still
        // null and loading is already false, which ProtectedRoute reads as
        // "logged in but no profile" and bounces to /signin.
        setLoading(true);
        setSession(session);
        setCurrentSession(session);
        if (session) {
          await loadUser();
        } else {
          setUser(null);
        }
        setLoading(false);
      }, 0);
    });
    return () => {
      subscription.unsubscribe();
    };
  }, []);

  return (
    <AuthContext.Provider value={{ session, user, loading }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);

  if (context === undefined) {
    throw new Error("useAuth must be used inisde and AuthProvider");
  }

  return context;
}
