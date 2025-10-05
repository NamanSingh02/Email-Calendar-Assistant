import Button from "./Button";
import { startAuth } from "../api";

export default function Header({ connected, onLogout }) {
  const connect = async () => {
    const { auth_url } = await startAuth();
    window.location.href = auth_url;
  };

  return (
    <header className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
      <div>
        <h1 className="h1">Email-Calendar-Assistant</h1>
        <p className="subtle mt-1">
          Summarize emails, extract action tasks, and plan your week.
        </p>
      </div>

      <div className="flex items-center gap-2">
        {connected ? (
          <Button variant="secondary" onClick={onLogout}>Log out</Button>
        ) : (
          <Button onClick={connect}>Connect Google</Button>
        )}
      </div>
    </header>
  );
}
