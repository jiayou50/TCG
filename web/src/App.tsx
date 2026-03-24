import { useCallback, useEffect, useState } from "react";

type PlayerState = {
  lifeTotal: number;
  library: string[];
  hand: string[];
  battlefield: string[];
  graveyard: string[];
  tappedPermanents: string[];
  summoningSickCreatures: string[];
  manaPool: Record<string, number>;
};

type CardState = {
  name: string;
  ownerId: string;
  manaCost: string;
  cardType: string;
  oracleText?: string | null;
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

type ActionGroup = {
  key: string;
  label: string;
  actions: Action[];
};

type SorceryActionOption = {
  action: Action;
  label: string;
};

const actionGroupDefinitions: {
  key: string;
  label: string;
  matches: (action: Action, cards: Record<string, CardState>) => boolean;
}[] = [
  {
    key: "turn-flow",
    label: "Turn Flow",
    matches: (action) => ["pass_priority", "pass_turn", "next_phase", "draw"].includes(action.kind),
  },
  {
    key: "mana",
    label: "Tap Lands for Mana",
    matches: (action) => ["tap_land_for_mana", "tap_all_lands_for_mana"].includes(action.kind),
  },
  {
    key: "play-creatures",
    label: "Play Creatures",
    matches: (action, cards) =>
      action.kind === "play_card" &&
      !!action.cardId &&
      cards[action.cardId]?.cardType.toLowerCase() === "creature",
  },
  {
    key: "play-lands",
    label: "Play Lands",
    matches: (action) => action.kind === "play_land",
  },
  {
    key: "attacks",
    label: "Declare Attacks",
    matches: (action) => action.kind === "attack_with_creature",
  },
  {
    key: "blocks",
    label: "Declare Blocks",
    matches: (action) => action.kind === "block_with_creature",
  },
];

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

const getSorceryActionKey = (action: Action): string => `${action.actorId}:${action.cardId ?? "none"}`;

const formatTargetLabel = (action: Action, cards: Record<string, CardState>): string => {
  if (!action.targetId) {
    return "No target";
  }

  return cards[action.targetId]?.name ?? action.targetId;
};

const formatCardName = (
  cardId: string,
  cards: Record<string, CardState>,
  tappedCardIds: Set<string> = new Set(),
  summoningSickCardIds: Set<string> = new Set(),
): string => {
  const card = cards[cardId];
  const tappedSuffix = tappedCardIds.has(cardId) ? " [tapped]" : "";
  const summoningSickSuffix = summoningSickCardIds.has(cardId) ? " [summoning sickness]" : "";
  if (!card) {
    return `${cardId}${tappedSuffix}${summoningSickSuffix}`;
  }

  const isCreature = card.cardType.toLowerCase() === "creature";
  const isSorcery = card.cardType.toLowerCase() === "sorcery";
  if (!isCreature) {
    if (isSorcery && card.oracleText) {
      return `${card.name} — ${card.oracleText}`;
    }
    return `${card.name}${tappedSuffix}`;
  }

  const powerToughness =
    card.power !== null && card.toughness !== null ? `${card.power}/${card.toughness}` : "?/?";
  return `${card.name} (${card.manaCost}) (${powerToughness})${tappedSuffix}${summoningSickSuffix}`;
};

const getBattlefieldCardIdsGroupedByType = (
  cardIds: string[],
  cards: Record<string, CardState>,
): string[] => {
  const cardTypeRank = (cardId: string): number => {
    const cardType = cards[cardId]?.cardType.toLowerCase();
    if (cardType === "creature") {
      return 0;
    }
    if (cardType === "land") {
      return 1;
    }
    return 2;
  };

  return [...cardIds].sort((cardIdA, cardIdB) => cardTypeRank(cardIdA) - cardTypeRank(cardIdB));
};

const formatManaPool = (manaPool: Record<string, number>): string => {
  const manaOrder = ["W", "U", "B", "R", "G", "C"];
  const orderedSymbols: string[] = [];
  const remainingSymbols = new Set(Object.keys(manaPool));

  manaOrder.forEach((symbol) => {
    const amount = manaPool[symbol] ?? 0;
    if (amount > 0) {
      orderedSymbols.push(symbol.repeat(amount));
      remainingSymbols.delete(symbol);
    }
  });

  [...remainingSymbols]
    .sort((symbolA, symbolB) => symbolA.localeCompare(symbolB))
    .forEach((symbol) => {
      const amount = manaPool[symbol];
      if (amount > 0) {
        orderedSymbols.push(symbol.repeat(amount));
      }
    });

  return orderedSymbols.length > 0 ? orderedSymbols.join("") : "Empty";
};

function App() {
  const [status, setStatus] = useState("Loading game state from backend...");
  const [gameState, setGameState] = useState<GameStateResponse | null>(null);
  const [legalActions, setLegalActions] = useState<Action[]>([]);
  const [actionsForPlayer, setActionsForPlayer] = useState<string | null>(null);
  const [isApplyingAction, setIsApplyingAction] = useState(false);
  const [selectedSorceryTargets, setSelectedSorceryTargets] = useState<Record<string, string>>({});

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

  const startNewGameAction =
    legalActions.find((action) => action.kind.toLowerCase() === "start_new_game") ?? null;
  const inGameActions = legalActions.filter((action) => action !== startNewGameAction);
  const cards = gameState?.cards ?? {};
  const sorceryPlayActions = inGameActions.filter(
    (action) =>
      action.kind === "play_card" &&
      !!action.cardId &&
      cards[action.cardId]?.cardType.toLowerCase() === "sorcery",
  );
  const sorceryActionOptionsByCard = sorceryPlayActions.reduce<Record<string, SorceryActionOption[]>>(
    (optionsByCard, action) => {
      const key = getSorceryActionKey(action);
      const nextOption: SorceryActionOption = {
        action,
        label: formatTargetLabel(action, cards),
      };
      if (!optionsByCard[key]) {
        optionsByCard[key] = [nextOption];
      } else {
        optionsByCard[key].push(nextOption);
      }
      return optionsByCard;
    },
    {},
  );

  useEffect(() => {
    setSelectedSorceryTargets((currentSelection) => {
      const nextSelection: Record<string, string> = {};
      Object.entries(sorceryActionOptionsByCard).forEach(([cardKey, options]) => {
        const priorSelection = currentSelection[cardKey];
        const stillExists = options.some((option) => option.action.targetId === priorSelection);
        nextSelection[cardKey] = stillExists ? priorSelection : options[0].action.targetId ?? "";
      });
      const sameKeys =
        Object.keys(currentSelection).length === Object.keys(nextSelection).length &&
        Object.keys(currentSelection).every((key) => key in nextSelection);
      const sameValues =
        sameKeys &&
        Object.entries(currentSelection).every(([key, value]) => nextSelection[key] === value);
      return sameValues ? currentSelection : nextSelection;
    });
  }, [sorceryActionOptionsByCard]);

  const inGameActionsWithoutSorceries = inGameActions.filter(
    (action) => !sorceryPlayActions.includes(action),
  );
  const groupedActions = actionGroupDefinitions.reduce<ActionGroup[]>(
    (groups, groupDefinition) => {
      const matchingActions = inGameActionsWithoutSorceries.filter((action) =>
        groupDefinition.matches(action, cards),
      );
      if (matchingActions.length > 0) {
        groups.push({
          key: groupDefinition.key,
          label: groupDefinition.label,
          actions: matchingActions,
        });
      }
      return groups;
    },
    [],
  );

  const uncategorizedActions = inGameActionsWithoutSorceries.filter(
    (action) => !actionGroupDefinitions.some((groupDefinition) => groupDefinition.matches(action, cards)),
  );
  if (uncategorizedActions.length > 0) {
    groupedActions.push({
      key: "other",
      label: "Other Actions",
      actions: uncategorizedActions,
    });
  }

  return (
    <main className="app-shell">
      <h1>TCG Frontend (React + TypeScript)</h1>
      <p>Use action buttons or sorcery target dropdowns to send actions to the backend.</p>
      <p id="output">{status}</p>

      <section className="actions-panel" aria-live="polite">
        {startNewGameAction ? (
          <button
            className="action-button start-new-game-button"
            onClick={() => void handleActionClick(startNewGameAction)}
            disabled={isApplyingAction}
          >
            {formatActionLabel(startNewGameAction, gameState?.cards ?? {})}
          </button>
        ) : null}
        <h2>
          Legal Actions ({actionsForPlayer ?? "-"} - {gameState?.phase ?? "-"})
        </h2>
        {inGameActions.length > 0 ? (
          <div className="action-groups">
            {Object.entries(sorceryActionOptionsByCard).map(([cardKey, options]) => {
              const selectedTargetId = selectedSorceryTargets[cardKey];
              const selectedAction =
                options.find((option) => option.action.targetId === selectedTargetId)?.action ??
                options[0]?.action;
              if (!selectedAction?.cardId) {
                return null;
              }

              const cardName = cards[selectedAction.cardId]?.name ?? selectedAction.cardId;
              return (
                <div className="action-group-row" key={`sorcery-${cardKey}`}>
                  <h3 className="action-group-heading">Play Sorceries</h3>
                  <div className="sorcery-action-row">
                    <label htmlFor={`sorcery-target-${cardKey}`}>{cardName}</label>
                    <select
                      id={`sorcery-target-${cardKey}`}
                      className="sorcery-target-select"
                      value={selectedTargetId ?? ""}
                      disabled={isApplyingAction}
                      onChange={(event) => {
                        const { value } = event.target;
                        setSelectedSorceryTargets((currentSelection) => ({
                          ...currentSelection,
                          [cardKey]: value,
                        }));
                      }}
                    >
                      {options.map((option) => (
                        <option
                          key={`${option.action.targetId ?? "none"}`}
                          value={option.action.targetId ?? ""}
                        >
                          {option.label}
                        </option>
                      ))}
                    </select>
                    <button
                      className="action-button"
                      onClick={() => selectedAction && void handleActionClick(selectedAction)}
                      disabled={isApplyingAction || !selectedAction}
                    >
                      Confirm
                    </button>
                  </div>
                </div>
              );
            })}
            {groupedActions.map((group) => (
              <div className="action-group-row" key={group.key}>
                <h3 className="action-group-heading">{group.label}</h3>
                <div className="actions-list">
                  {group.actions.map((action) => {
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
              </div>
            ))}
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
              {Object.entries(gameState.players).map(([playerId, player]) => {
                const tappedPermanents = new Set(player.tappedPermanents);
                const summoningSickCreatures = new Set(player.summoningSickCreatures);

                const isActivePlayer = playerId === gameState.activePlayerId;

                return (
                  <article
                    className={`player-summary ${isActivePlayer ? "player-summary-active" : ""}`}
                    key={playerId}
                  >
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
                      <strong>Mana pool:</strong> {formatManaPool(player.manaPool)}
                    </p>
                    <div className="card-zone">
                      <strong>Hand:</strong>
                      {player.hand.length > 0 ? (
                        <ul>
                          {player.hand.map((cardId) => (
                            <li key={`hand-${playerId}-${cardId}`}>
                              {formatCardName(cardId, gameState.cards)}
                            </li>
                          ))}
                        </ul>
                      ) : (
                        <p>None</p>
                      )}
                    </div>
                    <div className="card-zone">
                      <strong>Battlefield:</strong>
                      {player.battlefield.length > 0 ? (
                        <ul>
                          {getBattlefieldCardIdsGroupedByType(player.battlefield, gameState.cards).map(
                            (cardId) => (
                              <li key={`battlefield-${playerId}-${cardId}`}>
                                {formatCardName(
                                  cardId,
                                  gameState.cards,
                                  tappedPermanents,
                                  summoningSickCreatures,
                                )}
                              </li>
                            ),
                          )}
                        </ul>
                      ) : (
                        <p>None</p>
                      )}
                    </div>
                  </article>
                );
              })}
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
