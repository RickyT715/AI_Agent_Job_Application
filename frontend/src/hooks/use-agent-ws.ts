/** WebSocket hook for agent status updates. */

import useWebSocket from "react-use-websocket";
import { useAgentStore } from "../stores/agent-store";
import type { AgentStatusMessage } from "../types/api";

const WS_URL = `${window.location.protocol === "https:" ? "wss" : "ws"}://${window.location.host}/api/agent/ws/agent-status`;

export function useAgentWebSocket(jobId: number | null) {
  const setStatus = useAgentStore((s) => s.setStatus);

  const { lastJsonMessage, readyState } = useWebSocket<AgentStatusMessage>(
    jobId !== null ? WS_URL : null,
    {
      onMessage: (event) => {
        try {
          const data = JSON.parse(event.data) as AgentStatusMessage;
          setStatus(data);
        } catch {
          // Ignore non-JSON messages
        }
      },
      shouldReconnect: () => true,
      reconnectAttempts: 5,
      reconnectInterval: 3000,
    },
  );

  return { lastJsonMessage, readyState };
}
