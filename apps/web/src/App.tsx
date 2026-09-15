import React, { useState, useEffect } from 'react';
import { Session, Message, Artifact, HealthStatus, AgentEvent, Citation } from './types';
import {
  fetchHealth,
  fetchSessions,
  createSession,
  fetchSession,
  deleteSession,
  fetchArtifacts,
  streamChat,
} from './services/api';
import { Sidebar } from './components/Sidebar';
import { Header } from './components/Header';
import { ChatView } from './components/ChatView';
import { ArtifactViewer } from './components/ArtifactViewer';
import { ProvenanceDrawer } from './components/ProvenanceDrawer';

export const App: React.FC = () => {
  const [sessions, setSessions] = useState<Session[]>([]);
  const [activeSessionId, setActiveSessionId] = useState<string | null>(null);
  const [activeSession, setActiveSession] = useState<Session | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [artifacts, setArtifacts] = useState<Artifact[]>([]);
  const [activeArtifact, setActiveArtifact] = useState<Artifact | null>(null);
  const [health, setHealth] = useState<HealthStatus | null>(null);

  const [selectedModel, setSelectedModel] = useState<string>('llama3.1:8b');
  const [isStreaming, setIsStreaming] = useState<boolean>(false);
  const [streamingText, setStreamingText] = useState<string>('');
  const [activeEvents, setActiveEvents] = useState<AgentEvent[]>([]);

  const [showArtifactViewer, setShowArtifactViewer] = useState<boolean>(false);
  const [showProvenance, setShowProvenance] = useState<boolean>(false);
  const [selectedCitation, setSelectedCitation] = useState<Citation | null>(null);

  // Load initial health & sessions
  useEffect(() => {
    loadHealth();
    loadSessions();
  }, []);

  const loadHealth = async () => {
    try {
      const data = await fetchHealth();
      setHealth(data);
    } catch (err) {
      console.error('Failed to load health status', err);
    }
  };

  const loadSessions = async () => {
    try {
      const data = await fetchSessions();
      setSessions(data);
      if (data.length > 0 && !activeSessionId) {
        handleSelectSession(data[0].id);
      } else if (data.length === 0) {
        handleNewSession();
      }
    } catch (err) {
      console.error('Failed to load sessions', err);
    }
  };

  const handleSelectSession = async (sessionId: string) => {
    setActiveSessionId(sessionId);
    try {
      const sess = await fetchSession(sessionId);
      setActiveSession(sess);
      setMessages(sess.messages || []);

      // Load session artifacts
      const arts = await fetchArtifacts(sessionId);
      setArtifacts(arts);
      if (arts.length > 0) {
        setActiveArtifact(arts[0]);
      } else {
        setActiveArtifact(null);
        setShowArtifactViewer(false);
      }
    } catch (err) {
      console.error(`Failed to load session ${sessionId}`, err);
    }
  };

  const handleNewSession = async () => {
    try {
      const newSess = await createSession();
      setSessions((prev) => [newSess, ...prev]);
      setActiveSessionId(newSess.id);
      setActiveSession(newSess);
      setMessages([]);
      setArtifacts([]);
      setActiveArtifact(null);
      setShowArtifactViewer(false);
    } catch (err) {
      console.error('Failed to create session', err);
    }
  };

  const handleDeleteSession = async (sessionId: string, e: React.MouseEvent) => {
    e.stopPropagation();
    try {
      await deleteSession(sessionId);
      setSessions((prev) => prev.filter((s) => s.id !== sessionId));
      if (activeSessionId === sessionId) {
        const remaining = sessions.filter((s) => s.id !== sessionId);
        if (remaining.length > 0) {
          handleSelectSession(remaining[0].id);
        } else {
          handleNewSession();
        }
      }
    } catch (err) {
      console.error(`Failed to delete session ${sessionId}`, err);
    }
  };

  const handleSendMessage = async (text: string) => {
    if (!activeSessionId || isStreaming) return;

    // Optimistically add user message
    const tempUserMsg: Message = {
      id: `usr_${Date.now()}`,
      session_id: activeSessionId,
      role: 'user',
      content: text,
      created_at: new Date().toISOString(),
    };
    setMessages((prev) => [...prev, tempUserMsg]);

    setIsStreaming(true);
    setStreamingText('');
    setActiveEvents([]);

    await streamChat({
      sessionId: activeSessionId,
      message: text,
      model: selectedModel,
      provider: 'ollama',
      onEvent: (evt) => {
        setActiveEvents((prev) => [...prev, evt]);
        if (evt.type === 'artifact_created') {
          // Fetch new artifacts
          fetchArtifacts(activeSessionId).then((arts) => {
            setArtifacts(arts);
            if (arts.length > 0) {
              setActiveArtifact(arts[0]);
              setShowArtifactViewer(true);
            }
          });
        }
      },
      onDelta: (delta) => {
        setStreamingText((prev) => prev + delta);
      },
      onError: (err) => {
        console.error('Streaming error:', err);
        setIsStreaming(false);
      },
      onComplete: () => {
        setIsStreaming(false);
        // Refresh session to get server-persisted messages with citations
        if (activeSessionId) {
          fetchSession(activeSessionId).then((sess) => {
            setMessages(sess.messages || []);
          });
        }
      },
    });
  };

  const handleGenerateShip30 = () => {
    const prompt =
      "Turn this into a masterclass Ship 30 for 30 Long-Form Atomic Essay (approx 1,250 words) with exact transcript citations, bold rules, and actionable pillars. Save it as an artifact.";
    handleSendMessage(prompt);
  };

  // Collect all citations across current messages
  const allCitations: Citation[] = messages.flatMap(
    (m) => m.metadata?.citations || []
  );

  const handleSelectCitation = (citation: Citation) => {
    setSelectedCitation(citation);
    setShowProvenance(true);
  };

  return (
    <div className="app-layout">
      <Sidebar
        sessions={sessions}
        activeSessionId={activeSessionId}
        onSelectSession={handleSelectSession}
        onNewSession={handleNewSession}
        onDeleteSession={handleDeleteSession}
        selectedModel={selectedModel}
        onSelectModel={setSelectedModel}
        health={health}
      />

      <div className="main-area">
        <Header
          activeSession={activeSession}
          selectedModel={selectedModel}
          artifacts={artifacts}
          showArtifactViewer={showArtifactViewer}
          onToggleArtifactViewer={() => setShowArtifactViewer(!showArtifactViewer)}
          showProvenance={showProvenance}
          onToggleProvenance={() => setShowProvenance(!showProvenance)}
          provenanceCount={allCitations.length}
        />

        <div className="workspace-split">
          <ChatView
            messages={messages}
            isStreaming={isStreaming}
            streamingText={streamingText}
            activeEvents={activeEvents}
            onSendMessage={handleSendMessage}
            onSelectCitation={handleSelectCitation}
            onGenerateShip30={handleGenerateShip30}
          />

          {showArtifactViewer && activeArtifact && (
            <ArtifactViewer
              artifact={activeArtifact}
              onClose={() => setShowArtifactViewer(false)}
            />
          )}

          {showProvenance && (
            <ProvenanceDrawer
              citations={allCitations}
              selectedCitation={selectedCitation}
              onClose={() => setShowProvenance(false)}
            />
          )}
        </div>
      </div>
    </div>
  );
};

export default App;
