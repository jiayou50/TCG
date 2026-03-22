import { useCallback, useEffect, useState } from "react";

type PlayerState = {
  lifeTotal: number;
  library: string[];
  hand: string[];
  battlefield: string[];
  graveyard: string[];
  tappedPermanents: string[];
  manaPool: Record<string, number>;
};

type CardState = {
  name: string;
  ownerId: string;
  manaCost: string;
  cardType: string;
  power: number | null;
  toughness: number | null;
  producesMana: string[];
};

type GameStateResponse = {
  turnNumber: number;
  phase: string;
  activePlayerId: string;
  priorityPlayerId: string;
  declaredAttackers: string[];
  declaredBlocks: Record<string, string>;
  eventLog: string[];
  players: Record<string, PlayerState>;
  cards: Record<string, CardState>;
};

type Action = {
  kind: string;
  actorId: string;
  cardId: string | null;
  targetId: string | null;
};

type LegalActionsResponse = {
  playerId: string;
  actions: Action[];
};

const formatActionLabel = (action: Action, cards: Record<string, CardState>): string => {
  const cardName = action.cardId ? cards[action.cardId]?.name ?? action.cardId : null;
  const targetName = action.targetId ? cards[action.targetId]?.name ?? action.targetId : null;
  const readableKind = action.kind.replace(/_/g, " ");

  if (cardName && targetName) {
    return `${readableKind}: ${cardName} → ${targetName}`;
  }

  if (cardName) {
    return `${readableKind}: ${cardName}`;
  }

  return readableKind;
};

const formatCardNames = (
  cardIds: string[],
  cards: Record<string, CardState>,
  tappedCardIds: Set<string> = new Set(),
): string => {
  if (cardIds.length === 0) {
    return "None";
  }

  return cardIds
    .map((cardId) => {
      const card = cards[cardId];
      const tappedSuffix = tappedCardIds.has(cardId) ? " [tapped]" : "";
      if (!card) {
        return `${cardId}${tappedSuffix}`;
      }

      const isCreature = card.cardType.toLowerCase() === "creature";
      if (!isCreature) {
        return `${card.name}${tappedSuffix}`;
      }

      const powerToughness =
        card.power !== null && card.toughness !== null ? `${card.power}/${card.toughness}` : "?/?";
      return `${card.name} (${card.manaCost}) (${powerToughness})${tappedSuffix}`;
    })
    .join(", ");
};

function App() {
  const [status, setStatus] = useState("Loading game state from backend...");
  const [gameState, setGameState] = useState<GameStateResponse | null>(null);
  const [legalActions, setLegalActions] = useState<Action[]>([]);
  const [actionsForPlayer, setActionsForPlayer] = useState<string | null>(null);
  const [isApplyingAction, setIsApplyingAction] = useState(false);

  const fetchStateAndLegalActions = useCallback(async () => {
    const gameStateResponse = await fetch("/api/game-state");
    if (!gameStateResponse.ok) {
      throw new Error(`Failed to load game state (${gameStateResponse.status})`);
    }

    const gameStatePayload = (await gameStateResponse.json()) as GameStateResponse;
    setGameState(gameStatePayload);

    const legalActionsResponse = await fetch(
      `/api/players/${gameStatePayload.priorityPlayerId}/legal-actions`,
    );
    if (!legalActionsResponse.ok) {
      throw new Error(`Failed to load legal actions (${legalActionsResponse.status})`);
    }

    const legalActionsPayload = (await legalActionsResponse.json()) as LegalActionsResponse;
    setActionsForPlayer(legalActionsPayload.playerId);
    setLegalActions(legalActionsPayload.actions);
  }, []);

  useEffect(() => {
    const loadData = async () => {
      try {
        await fetchStateAndLegalActions();
        setStatus("Game state and legal actions loaded.");
      } catch (error) {
        const message = error instanceof Error ? error.message : "Unknown error";
        setStatus(`Failed to load data: ${message}`);
      }
    };

    void loadData();
  }, [fetchStateAndLegalActions]);

  const handleActionClick = useCallback(
    async (action: Action) => {
      setIsApplyingAction(true);
      setStatus(`Applying action: ${action.kind}...`);

      try {
        const response = await fetch("/api/actions", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify(action),
        });

        if (!response.ok) {
          const errorPayload = (await response.json().catch(() => null)) as
            | { detail?: string }
            | null;
          throw new Error(errorPayload?.detail ?? `Backend responded with ${response.status}`);
        }

        await fetchStateAndLegalActions();
        setStatus("Action applied. Game state and legal actions refreshed.");
      } catch (error) {
        const message = error instanceof Error ? error.message : "Unknown error";
        setStatus(`Failed to apply action: ${message}`);
      } finally {
        setIsApplyingAction(false);
      }
    },
    [fetchStateAndLegalActions],
  );

  return (
    <main className="app-shell">
      <h1>TCG Frontend (React + TypeScript)</h1>
      <p>Click an action button to send it to the backend and refresh the game.</p>
      <p id="output">{status}</p>

      <section className="actions-panel" aria-live="polite">
        <h2>
          Legal Actions ({actionsForPlayer ?? "-"})
        </h2>
        {legalActions.length > 0 ? (
          <div className="actions-list">
            {legalActions.map((action) => {
              const key = `${action.kind}:${action.actorId}:${action.cardId ?? "none"}:${action.targetId ?? "none"}`;
              return (
                <button
                  className="action-button"
                  key={key}
                  onClick={() => void handleActionClick(action)}
                  disabled={isApplyingAction}
                >
                  {formatActionLabel(action, gameState?.cards ?? {})}
                </button>
              );
            })}
          </div>
        ) : (
          <p>No legal actions available.</p>
        )}
      </section>

      <section className="game-summary-panel" aria-live="polite">
        <h2>Game Summary</h2>
        {gameState ? (
          <>
            <p className="turn-phase">
              <strong>Turn:</strong> {gameState.turnNumber} · <strong>Phase:</strong> {gameState.phase}
            </p>
            <div className="players-grid">
              {Object.entries(gameState.players).map(([playerId, player]) => (
                <article className="player-summary" key={playerId}>
                  <h3>{playerId}</h3>
                  <p>
                    <strong>Life:</strong> {player.lifeTotal}
                  </p>
                  <p>
                    <strong>Library:</strong> {player.library.length} cards
                  </p>
                  <p>
                    <strong>Graveyard:</strong> {player.graveyard.length} cards
                  </p>
                  <p>
                    <strong>Hand:</strong> {formatCardNames(player.hand, gameState.cards)}
                  </p>
                  <p>
                    <strong>Battlefield:</strong>{" "}
                    {formatCardNames(
                      player.battlefield,
                      gameState.cards,
                      new Set(player.tappedPermanents),
                    )}
                  </p>
                </article>
              ))}
            </div>
          </>
        ) : (
          <p>No game summary available.</p>
        )}
      </section>

      <pre className="game-state-text">
        {gameState ? JSON.stringify(gameState, null, 2) : "No game state available."}
      </pre>
    </main>
  );
}

export default App;
