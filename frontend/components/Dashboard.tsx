'use client';

import { FormEvent, useEffect, useRef, useState } from "react";

type Source = {
  filename: string;
  page_number: number | null;
  score: number;
  content: string;
};

type Document = {
  id: string;
  filename: string;
  status: string;
};

type Message = {
  role: "user" | "assistant";
  content: string;
  sources?: Source[];
};

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export default function Dashboard() {
  const [documents, setDocuments] = useState<Document[]>([]);
  const [messages, setMessages] = useState<Message[]>([]);
  const [question, setQuestion] = useState("");
  const [loading, setLoading] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [conversationId, setConversationId] = useState<string | null>(null);

  // Reference to the chat messages container
  const messagesEndRef = useRef<HTMLDivElement>(null);

  async function loadDocuments() {
    const res = await fetch(`${API}/api/documents`);

    if (res.ok) {
      setDocuments(await res.json());
    }
  }

  useEffect(() => {
    loadDocuments();
  }, []);

  // Automatically scroll chat to the newest message
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({
      behavior: "smooth",
    });
  }, [messages, loading]);

  async function upload(file: File) {
    setUploading(true);

    try {
      const form = new FormData();
      form.append("file", file);

      const res = await fetch(`${API}/api/documents/upload`, {
        method: "POST",
        body: form,
      });

      if (!res.ok) {
        const error = await res.json().catch(() => ({}));
        alert(error.detail || "Upload failed.");
        return;
      }

      await loadDocuments();
    } finally {
      setUploading(false);
    }
  }

  async function ask(e: FormEvent) {
    e.preventDefault();

    if (!question.trim() || loading) {
      return;
    }

    const current = question;

    setQuestion("");

    setMessages((m) => [
      ...m,
      {
        role: "user",
        content: current,
      },
    ]);

    setLoading(true);

    try {
      const res = await fetch(`${API}/api/chat`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          question: current,
          conversation_id: conversationId,
        }),
      });

      const data = await res.json();

      if (!res.ok) {
        setMessages((m) => [
          ...m,
          {
            role: "assistant",
            content: data.detail || "Something went wrong.",
          },
        ]);

        return;
      }

      setConversationId(data.conversation_id);

      setMessages((m) => [
        ...m,
        {
          role: "assistant",
          content: data.answer,
          sources: data.sources,
        },
      ]);
    } catch (error) {
      setMessages((m) => [
        ...m,
        {
          role: "assistant",
          content: "Unable to connect to the backend.",
        },
      ]);
    } finally {
      setLoading(false);
    }
  }

  async function removeDocument(id: string) {
    await fetch(`${API}/api/documents/${id}`, {
      method: "DELETE",
    });

    await loadDocuments();
  }

  return (
    <main className="h-screen overflow-hidden bg-gray-50">

      {/* Header */}
      <header className="h-[73px] border-b bg-white">
        <div className="mx-auto flex h-full max-w-7xl items-center justify-between px-6">
          <div>
            <h1 className="text-2xl font-bold">
              KnowFlow
            </h1>

            {/* <p className="text-sm text-gray-500">
              AI-powered knowledge management
            </p> */}
          </div>

          {/* <span className="rounded-full bg-gray-100 px-3 py-1 text-xs">
            RAG + PostgreSQL
          </span> */}
        </div>
      </header>

      {/* Main content */}
      <div className="mx-auto h-[calc(100vh-73px)] max-w-7xl p-6">

        <div className="grid h-full grid-cols-1 gap-6 lg:grid-cols-[320px_1fr]">

          {/* Knowledge Base */}
          <aside className="flex min-h-0 flex-col overflow-hidden rounded-2xl border bg-white p-5 shadow-sm">

            <h2 className="font-semibold">
              Knowledge base
            </h2>

            <p className="mt-1 text-sm text-gray-500">
              Upload documents
            </p>

            {/* Upload */}
            <label className="mt-5 flex shrink-0 cursor-pointer items-center justify-center rounded-xl border-2 border-dashed p-6 text-center text-sm hover:bg-gray-50">
              {uploading
                ? "Processing..."
                : "Click to upload"}

              <input
                type="file"
                accept=".pdf,.docx,.xlsx,.xls,.xlsm,.csv,.tsv,.pptx,.txt,.md,.html,.htm,.xml,.json,.jsonl"
                className="hidden"
                disabled={uploading}
                onChange={(e) => {
                  const file = e.target.files?.[0];

                  if (file) {
                    upload(file);
                  }
                }}
              />
            </label>

            {/* Documents scroll area */}
            <div className="mt-6 min-h-0 flex-1 space-y-2 overflow-y-auto pr-1">

              {documents.length === 0 && (
                <p className="text-sm text-gray-400">
                  No documents yet.
                </p>
              )}

              {documents.map((doc) => (
                <div
                  key={doc.id}
                  className="flex items-center justify-between rounded-lg bg-gray-50 p-3"
                >
                  <div className="min-w-0">
                    <p className="truncate text-sm font-medium">
                      {doc.filename}
                    </p>

                    <p className="text-xs text-gray-500">
                      {doc.status}
                    </p>
                  </div>

                  <button
                    onClick={() => removeDocument(doc.id)}
                    className="ml-2 shrink-0 text-xs text-red-500 hover:text-red-700"
                  >
                    Delete
                  </button>
                </div>
              ))}

            </div>
          </aside>

          {/* Chat */}
          <section className="flex min-h-0 h-full flex-col overflow-hidden rounded-2xl border bg-white shadow-sm">

            {/* Chat header */}
            <div className="shrink-0 border-b p-5">
              <h2 className="font-semibold">
                Ask your knowledge base
              </h2>

              <p className="text-sm text-gray-500">
                Local LLM + RAG
              </p>
            </div>

            {/* Messages - ONLY THIS AREA SCROLLS */}
            <div className="min-h-0 flex-1 overflow-y-auto p-6">

              <div className="space-y-5">

                {messages.length === 0 && (
                  <div className="mx-auto mt-20 max-w-lg text-center">
                    <h3 className="text-xl font-semibold">
                      What do you want to know?
                    </h3>

                    <p className="mt-2 text-gray-500">
                      Upload a document and ask a question.
                      KnowFlow retrieves relevant chunks and cites
                      sources.
                    </p>
                  </div>
                )}

                {messages.map((message, index) => (
                  <div key={index}>

                    {/* Message */}
                    <div
                      className={`max-w-3xl rounded-2xl p-4 ${
                        message.role === "user"
                          ? "ml-auto bg-black text-white"
                          : "bg-gray-100"
                      }`}
                    >
                      <p className="whitespace-pre-wrap text-sm leading-6">
                        {message.content}
                      </p>
                    </div>

                    {/* Sources */}
                    {message.sources &&
                      message.sources.length > 0 && (
                        <div className="mt-3 grid max-w-3xl gap-2">

                          <p className="text-xs font-semibold uppercase text-gray-500">
                            Sources
                          </p>

                          {message.sources.map((source, i) => (
                            <div
                              key={i}
                              className="rounded-xl border bg-white p-3 text-xs"
                            >
                              <div className="font-medium">
                                [{i + 1}] {source.filename}

                                {source.page_number
                                  ? ` · Page ${source.page_number}`
                                  : ""}
                              </div>

                              <div className="mt-1 text-gray-500">
                                Similarity: {source.score}
                              </div>
                            </div>
                          ))}

                        </div>
                      )}

                  </div>
                ))}

                {/* Loading */}
                {loading && (
                  <div className="w-fit rounded-2xl bg-gray-100 p-4 text-sm text-gray-500">
                    Searching documents and generating answer...
                  </div>
                )}

                {/* Scroll target */}
                <div ref={messagesEndRef} />

              </div>

            </div>

            {/* Input - ALWAYS stays at bottom */}
            <form
              onSubmit={ask}
              className="shrink-0 border-t bg-white p-4"
            >
              <div className="flex gap-3">

                <input
                  value={question}
                  onChange={(e) => setQuestion(e.target.value)}
                  placeholder="Ask a question about your documents..."
                  className="flex-1 rounded-xl border px-4 py-3 text-sm outline-none focus:ring-2 focus:ring-black"
                />

                <button
                  type="submit"
                  disabled={loading}
                  className="rounded-xl bg-black px-6 py-3 text-sm font-medium text-white disabled:opacity-50"
                >
                  Ask
                </button>

              </div>
            </form>

          </section>

        </div>

      </div>

    </main>
  );
}