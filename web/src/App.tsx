import { useEffect, useState } from "react";

type GameStateResponse = {
  turnNumber: number;
  phase: string;
  activePlayerId: string;
  priorityPlayerId: string;
  eventLog: string[];
  players: Record<
    string,
    {
      lifeTotal: number;
      library: string[];
      hand: string[];
      battlefield: string[];
      graveyard: string[];
    }
  >;
};

function App() {
  const [status, setStatus] = useState("Loading game state from backend...");
  const [gameState, setGameState] = useState<GameStateResponse | null>(null);

  useEffect(() => {
    const fetchGameState = async () => {
      try {
        const response = await fetch("/api/game-state");
        if (!response.ok) {
          throw new Error(`Backend responded with ${response.status}`);
        }
        const payload = (await response.json()) as GameStateResponse;
        setGameState(payload);
        setStatus("Game state loaded.");
      } catch (error) {
        const message = error instanceof Error ? error.message : "Unknown error";
        setStatus(`Failed to load game state: ${message}`);
      }
    };

    void fetchGameState();
  }, []);

  return (
    <main className="app-shell">
      <h1>TCG Frontend (React + TypeScript)</h1>
      <p>Frontend is connected to FastAPI and displays a default game state.</p>
      <p id="output">{status}</p>
      <pre className="game-state-text">
        {gameState ? JSON.stringify(gameState, null, 2) : "No game state available."}
      </pre>
    </main>
  );
}

export default App;
