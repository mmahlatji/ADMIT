import { supabase } from "./supabaseClient";

export async function signUp(
  email: string,
  password: string,
  firstName: string,
  lastName: string,
  employeeId: string,
) {
  const { data, error } = await supabase.auth.signUp({
    email,
    password,
    options: {
      data: {
        employee_id: employeeId,
        first_name: firstName,
        last_name: lastName,
      },
    },
  });

  if (error) {
    throw error;
  }

  //account not created
  if (!data.user) {
    throw new Error("Account was not created.");
  }

  return data;
}

//sign in
export async function signIn(email: string, password: string) {
  const { error } = await supabase.auth.signInWithPassword({
    email: email,
    password: password,
  });

  if (error) {
    throw error;
  }
}
