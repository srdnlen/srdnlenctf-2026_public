import { useState } from "react";
import LoginForm from "../components/login/LoginForm";
import LoadingScreen from "../components/login/LoadingScreen";
import AlertDialog from "../components/login/AlertDialog";
import { login as apiLogin, register, getCurrentUser } from "../utils/api";
import { useAuth } from "../contexts/AuthContext";
import "../styles/defaults.css";
import "../styles/login.css";

function LoginPage() {
  const { login } = useAuth();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [isSignup, setIsSignup] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState("");
  const [alertMessage, setAlertMessage] = useState("");

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");

    if (!username || !password) {
      setError("Please enter username and password");
      return;
    }

    setIsLoading(true);

    try {
      const { response, data } = isSignup
        ? await register(username, password)
        : await apiLogin(username, password);

      if (!response.ok || !data.ok) {
        const errorMessage =
          data.error_code === "INVALID_CREDENTIALS"
            ? "Invalid username or password"
            : data.error_code === "USERNAME_TAKEN"
              ? "Username already taken"
              : data.error_code === "MISSING_FIELDS"
                ? "Please enter username and password"
                : "An error occurred. Please try again.";

        setError(errorMessage);
        setIsLoading(false);
        return;
      }

      if (isSignup) {
        setAlertMessage(
          "Registration successful! Please log in with your credentials.",
        );
        setIsSignup(false);
        setPassword("");
        setIsLoading(false);
        return;
      }

      const { response: meResp, data: meData } = await getCurrentUser();

      if (!meResp.ok || !meData.ok) {
        setError("Login successful but failed to get user info");
        setIsLoading(false);
        return;
      }

      login({
        id: meData.data.id,
        username: meData.data.username,
      });
    } catch (err) {
      setError("Network error. Please check if the server is running.");
      setIsLoading(false);
    }
  };

  const handleForgotPassword = () => {
    setAlertMessage(
      <>
        Try contacting <strong>justlel</strong>... but he's probably busy doing
        some experiments on the team's infrastructure 🔧💥
      </>,
    );
  };

  return (
    <div className="main logon">
      {!isLoading ? (
        <LoginForm
          isSignup={isSignup}
          username={username}
          password={password}
          error={error}
          onUsernameChange={setUsername}
          onPasswordChange={setPassword}
          onSubmit={handleSubmit}
          onToggleMode={() => setIsSignup(!isSignup)}
          onForgotPassword={handleForgotPassword}
        />
      ) : (
        <LoadingScreen />
      )}

      <AlertDialog message={alertMessage} onClose={() => setAlertMessage("")} />
    </div>
  );
}

export default LoginPage;
