'use client';

import { useCallback, useRef } from 'react';
import { useAgentStore, ActivityLogEntry } from '../store/useAgentStore';

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8000';

interface SSEEvent {
  type: 'status' | 'token' | 'tool_start' | 'tool_end' | 'done' | 'error';
  content?: string;
  phase?: string;
  name?: string;
  message?: string;
}

/**
 * Parses raw SSE text into individual event objects.
 * Handles partial chunks that may split across reads.
 */
function parseSSEChunk(raw: string): { events: SSEEvent[]; remainder: string } {
  const events: SSEEvent[] = [];
  const lines = raw.split('\n');
  let remainder = '';

  for (let i = 0; i < lines.length; i++) {
    const line = lines[i].trim();

    if (line.startsWith('data: ')) {
      try {
        const parsed = JSON.parse(line.slice(6));
        events.push(parsed);
      } catch {
        // Incomplete JSON — save as remainder for next chunk
        if (i === lines.length - 1 || i === lines.length - 2) {
          remainder = line;
        }
      }
    }
  }

  return { events, remainder };
}

export function useSSEStream() {
  const {
    appendToMessage,
    pushActivityLog,
    updateLastActivityDuration,
    setStreamPhase,
    finalizeStream,
    addMessage,
  } = useAgentStore();

  const abortRef = useRef<AbortController | null>(null);
  const toolTimers = useRef<Map<string, number>>(new Map());

  const streamMessage = useCallback(
    async (
      endpoint: string,
      headers: HeadersInit,
      body: object,
      streamingMessageId: string,
    ) => {
      abortRef.current = new AbortController();
      toolTimers.current.clear();

      try {
        const res = await fetch(endpoint, {
          method: 'POST',
          headers: {
            ...headers,
            Accept: 'text/event-stream',
          },
          body: JSON.stringify(body),
          signal: abortRef.current.signal,
        });

        if (!res.ok) {
          const text = await res.text();
          throw new Error(`Stream request failed (${res.status}): ${text.slice(0, 200)}`);
        }

        const reader = res.body?.getReader();
        if (!reader) throw new Error('No readable stream available');

        const decoder = new TextDecoder();
        let buffer = '';

        while (true) {
          const { done, value } = await reader.read();
          if (done) break;

          buffer += decoder.decode(value, { stream: true });
          const { events, remainder } = parseSSEChunk(buffer);
          buffer = remainder;

          for (const event of events) {
            switch (event.type) {
              case 'status': {
                if (event.phase) {
                  setStreamPhase(event.phase as any);
                  const phaseLabels: Record<string, string> = {
                    routing: 'Routing intent',
                    thinking: 'Activating neural engine',
                    executing: 'Executing tools',
                    generating: 'Synthesizing response',
                  };
                  const label = phaseLabels[event.phase] || event.phase;
                  pushActivityLog(streamingMessageId, {
                    type: 'status',
                    label,
                    timestamp: Date.now(),
                  });
                }
                break;
              }

              case 'token': {
                if (event.content) {
                  appendToMessage(streamingMessageId, event.content);
                }
                break;
              }

              case 'tool_start': {
                if (event.name) {
                  toolTimers.current.set(event.name, Date.now());
                  pushActivityLog(streamingMessageId, {
                    type: 'tool_start',
                    label: event.name,
                    timestamp: Date.now(),
                  });
                }
                break;
              }

              case 'tool_end': {
                if (event.name) {
                  const startTime = toolTimers.current.get(event.name);
                  const duration = startTime ? Date.now() - startTime : 0;
                  toolTimers.current.delete(event.name);

                  updateLastActivityDuration(streamingMessageId, event.name, duration);
                  pushActivityLog(streamingMessageId, {
                    type: 'tool_end',
                    label: event.name,
                    timestamp: Date.now(),
                    duration,
                  });
                }
                break;
              }

              case 'done': {
                finalizeStream();
                return;
              }

              case 'error': {
                finalizeStream();
                addMessage({
                  id: crypto.randomUUID(),
                  role: 'system',
                  content: `Error: ${event.message || 'Stream encountered an error'}`,
                  timestamp: new Date().toISOString(),
                });
                return;
              }
            }
          }
        }

        // If we exit the loop without a 'done' event, finalize anyway
        finalizeStream();
      } catch (error: any) {
        finalizeStream();

        if (error.name === 'AbortError') return;

        addMessage({
          id: crypto.randomUUID(),
          role: 'system',
          content: `Error: ${error.message || 'Failed to connect to agent stream.'}`,
          timestamp: new Date().toISOString(),
        });
      }
    },
    [appendToMessage, pushActivityLog, updateLastActivityDuration, setStreamPhase, finalizeStream, addMessage],
  );

  const abort = useCallback(() => {
    abortRef.current?.abort();
  }, []);

  return { streamMessage, abort };
}
