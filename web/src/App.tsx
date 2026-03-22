import { useState } from "react";

function App() {
  const [status, setStatus] = useState("Click the button to verify the React app is mounted.");

  return (
    <main className="app-shell">
      <h1>TCG Frontend (React + TypeScript)</h1>
      <p>This frontend now uses React and TypeScript via Vite.</p>
      <button
        type="button"
        onClick={() => {
          setStatus(`UI ready at ${new Date().toISOString()}`);
        }}
      >
        Ping frontend
      </button>
      <p id="output">{status}</p>
    </main>
  );
}

export default App;
