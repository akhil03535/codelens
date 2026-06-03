import { useEffect, useRef, useState } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { chatApi, extractError } from "../../services/api";

interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  sources?: any[];
}

const SUGGESTIONS = [
  "Explain the overall architecture of this codebase",
  "How is authentication implemented?",
  "What are the main entry points?",
  "How is error handling done?",
  "What database models are defined?",
];

export default function ChatPanel({ repoId }: { repoId: string }) {
  const [chats, setChats] = useState<any[]>([]);
  const [activeChatId, setActiveChatId] = useState<string | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [selectedSources, setSelectedSources] = useState<any[]>([]);
  const bottomRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    chatApi.listChats(repoId).then(setChats).catch(() => {});
  }, [repoId]);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const loadChat = async (chatId: string) => {
    setActiveChatId(chatId);
    const msgs = await chatApi.getMessages(repoId, chatId);
    setMessages(msgs);
  };

  const send = async (text: string) => {
    const trimmed = text.trim();
    if (!trimmed || loading) return;

    const userMsg: Message = { id: crypto.randomUUID(), role: "user", content: trimmed };
    setMessages(prev => [...prev, userMsg]);
    setInput("");
    setLoading(true);

    try {
      const res = await chatApi.sendMessage(repoId, trimmed, activeChatId || undefined);
      if (!activeChatId) {
        setActiveChatId(res.chat_id);
        const newChats = await chatApi.listChats(repoId);
        setChats(newChats);
      }
      setMessages(prev => [
        ...prev.filter(m => m.id !== userMsg.id),
        res.user_message,
        res.assistant_message,
      ]);
    } catch (err) {
      setMessages(prev => [
        ...prev,
        { id: crypto.randomUUID(), role: "assistant", content: `Error: ${extractError(err)}` },
      ]);
    } finally {
      setLoading(false);
      inputRef.current?.focus();
    }
  };

  return (
    <div className="h-full flex">
      {/* Chat history sidebar */}
      <div className="w-56 border-r border-bg-border flex flex-col bg-bg-1 flex-shrink-0">
        <div className="p-3 border-b border-bg-border">
          <button
            onClick={() => { setActiveChatId(null); setMessages([]); setSelectedSources([]); }}
            className="btn-primary w-full text-sm py-1.5"
          >
            + New Chat
          </button>
        </div>
        <div className="flex-1 overflow-y-auto p-2 space-y-1">
          {chats.map(c => (
            <button
              key={c.id}
              onClick={() => loadChat(c.id)}
              className={`w-full text-left px-3 py-2 rounded-lg text-xs transition-colors truncate ${
                activeChatId === c.id ? "bg-accent/15 text-accent" : "text-text-dim hover:bg-bg-2 hover:text-text"
              }`}
            >
              {c.title}
            </button>
          ))}
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 flex flex-col min-w-0">
        <div className="flex-1 overflow-y-auto p-6 space-y-4">
          {messages.length === 0 ? (
            <div className="py-8">
              <p className="text-text-dim text-sm mb-4">Suggested questions:</p>
              <div className="space-y-2">
                {SUGGESTIONS.map(s => (
                  <button key={s} onClick={() => send(s)}
                    className="block w-full text-left px-4 py-3 bg-bg-1 border border-bg-border hover:border-accent/40 rounded-lg text-sm text-text-dim hover:text-text transition-colors">
                    {s}
                  </button>
                ))}
              </div>
            </div>
          ) : (
            messages.map(msg => (
              <div key={msg.id}>
                <div className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}>
                  <div className={`max-w-2xl rounded-xl px-4 py-3 text-sm ${
                    msg.role === "user"
                      ? "bg-accent-dim text-white"
                      : "bg-bg-1 border border-bg-border text-text"
                  }`}>
                    {msg.role === "assistant" ? (
                      <div className="prose prose-invert prose-sm max-w-none">
                        <ReactMarkdown remarkPlugins={[remarkGfm]}>{msg.content}</ReactMarkdown>
                      </div>
                    ) : msg.content}
                  </div>
                </div>
                {msg.sources && msg.sources.length > 0 && (
                  <div className="flex gap-2 mt-2 flex-wrap">
                    {msg.sources.slice(0, 4).map((s: any, i: number) => (
                      <button
                        key={i}
                        onClick={() => setSelectedSources(msg.sources || [])}
                        className="text-xs px-2 py-1 bg-bg-2 border border-bg-border hover:border-accent/40 rounded text-muted hover:text-text transition-colors font-mono"
                      >
                        {s.file_path.split("/").pop()} ({(s.score * 100).toFixed(0)}%)
                      </button>
                    ))}
                  </div>
                )}
              </div>
            ))
          )}
          {loading && (
            <div className="flex gap-1 px-4 py-3 bg-bg-1 border border-bg-border rounded-xl w-fit">
              {[0,1,2].map(i => (
                <div key={i} className="w-1.5 h-1.5 bg-muted rounded-full animate-bounce"
                  style={{ animationDelay: `${i * 0.15}s` }} />
              ))}
            </div>
          )}
          <div ref={bottomRef} />
        </div>

        {/* Input */}
        <div className="border-t border-bg-border p-4">
          <div className="flex gap-2">
            <textarea
              ref={inputRef}
              value={input}
              onChange={e => setInput(e.target.value)}
              onKeyDown={e => { if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); send(input); } }}
              placeholder="Ask about the codebase… (Enter to send)"
              rows={2}
              disabled={loading}
              className="input resize-none flex-1"
            />
            <button onClick={() => send(input)} disabled={loading || !input.trim()} className="btn-primary px-4">→</button>
          </div>
        </div>
      </div>

      {/* Sources panel */}
      {selectedSources.length > 0 && (
        <div className="w-80 border-l border-bg-border flex flex-col flex-shrink-0 bg-bg-1">
          <div className="p-3 border-b border-bg-border flex items-center justify-between">
            <span className="text-sm font-medium">Sources ({selectedSources.length})</span>
            <button onClick={() => setSelectedSources([])} className="text-muted hover:text-text">✕</button>
          </div>
          <div className="flex-1 overflow-y-auto p-3 space-y-3">
            {selectedSources.map((s: any, i: number) => (
              <div key={i} className="bg-bg-2 border border-bg-border rounded-lg overflow-hidden">
                <div className="px-3 py-2 flex items-center justify-between border-b border-bg-border bg-bg-3">
                  <span className="text-xs font-mono text-accent truncate max-w-[180px]">{s.file_path}</span>
                  <span className="text-xs text-muted flex-shrink-0 ml-2">{(s.score * 100).toFixed(0)}%</span>
                </div>
                <pre className="text-xs font-mono text-muted p-3 overflow-x-auto max-h-40 overflow-y-auto leading-relaxed whitespace-pre-wrap">
                  {s.content}
                </pre>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
