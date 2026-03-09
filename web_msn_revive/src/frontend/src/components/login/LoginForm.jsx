import { APP_NAME } from "../../appname";

function LoginForm({
  isSignup,
  username,
  password,
  error,
  onUsernameChange,
  onPasswordChange,
  onSubmit,
  onToggleMode,
  onForgotPassword,
}) {
  return (
    <>
      <div id="topavatar" style={{ marginBottom: "16px" }}>
        <img className="avatar" src="/images/chat-window/1531.png" alt="" />
        <img className="frame" src="/images/background/frame_96.png" alt="" />
      </div>

      <div id="logon-screen">
        <div
          className="logon-header"
          id="signin-header"
          style={{ display: isSignup ? "none" : "block" }}
        >
          <img
            src="/images/general/live_logo.png"
            alt="Windows Live"
            style={{ height: "24px", marginBottom: "8px" }}
          />
          <h1>Sign in to {APP_NAME}</h1>
          <p className="logon-subtitle">Connect with friends and family</p>
          Don't have an account?{" "}
          <a
            href="#"
            id="signup"
            onClick={(e) => {
              e.preventDefault();
              onToggleMode();
            }}
          >
            Sign up
          </a>
        </div>
        <div
          className="logon-header"
          id="signup-header"
          style={{ display: isSignup ? "block" : "none" }}
        >
          <img
            src="/images/general/live_logo.png"
            alt="Windows Live"
            style={{ height: "24px", marginBottom: "8px" }}
          />
          <h1>Create your account</h1>
          <p className="logon-subtitle">Join {APP_NAME} today</p>
          Already have an account?{" "}
          <a
            href="#"
            id="signin"
            onClick={(e) => {
              e.preventDefault();
              onToggleMode();
            }}
          >
            Sign in
          </a>
        </div>

        <form className="logon-form" onSubmit={onSubmit}>
          <fieldset className="logon-fieldset">
            <input
              type="text"
              name="username"
              placeholder="Username"
              required
              maxLength={32}
              value={username}
              onChange={(e) => onUsernameChange(e.target.value)}
            />
            <input
              type="password"
              name="password"
              placeholder="Password"
              required
              maxLength={128}
              value={password}
              onChange={(e) => onPasswordChange(e.target.value)}
            />
            <a
              href="#"
              id="forgot-password"
              onClick={(e) => {
                e.preventDefault();
                onForgotPassword();
              }}
            >
              Forgot your password?
            </a>
          </fieldset>
          <div>
            <button className="win7-btn" type="submit" id="TheButton">
              {isSignup ? "Sign up" : "Sign in"}
            </button>
          </div>
        </form>
      </div>

      {error && (
        <div id="error-message" style={{ color: "red" }}>
          {error}
        </div>
      )}
    </>
  );
}

export default LoginForm;
