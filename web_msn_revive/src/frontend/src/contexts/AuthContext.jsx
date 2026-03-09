import { createContext, useContext, useState, useEffect } from "react";
import { logout as apiLogout, getCurrentUser } from "../utils/api";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [isCheckingSession, setIsCheckingSession] = useState(true);

  useEffect(() => {
    async function checkSession() {
      try {
        const { response, data } = await getCurrentUser();

        if (response.ok && data.ok) {
          setUser({
            id: data.data.id,
            username: data.data.username,
          });
        }
      } catch (err) {
      } finally {
        setIsCheckingSession(false);
      }
    }

    checkSession();
  }, []);

  const login = (userData) => {
    setUser(userData);
  };

  const logout = async () => {
    try {
      await apiLogout();
    } catch (err) {
    } finally {
      setUser(null);
    }
  };

  const value = {
    user,
    login,
    logout,
    isCheckingSession,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
}
