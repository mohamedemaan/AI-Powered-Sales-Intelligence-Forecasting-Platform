'use client'

import React, { useState, useRef } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import api from '../../lib/api'
import {
  BookOpen,
  UploadCloud,
  FileText,
  Search,
  MessageSquare,
  Sparkles,
  Trash2,
  RefreshCw,
  Layers,
  CheckCircle2,
  AlertTriangle,
  FileCheck,
  ExternalLink,
  ChevronRight,
  ShieldCheck,
  Loader2,
  Info,
  X
} from 'lucide-react'

interface RagDocument {
  id: string
  tenant_id: string
  title: string
  original_filename: string
  file_size: number
  mime_type: string
  file_type: string
  status: string
  total_chunks: number
  error_message: string | null
  created_at: string
  updated_at: string | null
}

interface RagChunk {
  id: string
  document_id: string
  chunk_index: number
  chunk_text: string
  token_count: number
  page_number: number | null
  section_title: string | null
}

interface RagCitation {
  citation_id: string
  document_id: string
  document_title: string
  filename: string
  page_number: number | null
  section_title: string | null
  snippet: string
  similarity_score: number
}

interface ChatMessage {
  id: string
  sender: 'user' | 'assistant'
  text: string
  intent?: string
  citations?: RagCitation[]
  hasContext?: boolean
  model?: string
  timeMs?: number
  timestamp: string
}

export default function KnowledgeBaseRAGPage() {
  const queryClient = useQueryClient()
  const fileInputRef = useRef<HTMLInputElement>(null)

  // State
  const [activeTab, setActiveTab] = useState<'chat' | 'documents'>('chat')
  const [queryInput, setQueryInput] = useState('')
  const [selectedDocId, setSelectedDocId] = useState<string>('ALL')
  const [similarityThreshold, setSimilarityThreshold] = useState<number>(0.60)
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: 'welcome',
      sender: 'assistant',
      text: 'Hello! I am your SalesMind AI Knowledge Assistant. Ask me anything about your business policies, sales playbooks, supplier contracts, or combined sales analytics. Upload knowledge documents anytime to expand my verified context.',
      hasContext: true,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    }
  ])
  const [isAsking, setIsAsking] = useState(false)
  const [uploadFile, setUploadFile] = useState<File | null>(null)
  const [customTitle, setCustomTitle] = useState('')
  const [uploadError, setUploadError] = useState<string | null>(null)
  const [feedbackMsg, setFeedbackMsg] = useState<string | null>(null)

  // Modals
  const [inspectDoc, setInspectDoc] = useState<RagDocument | null>(null)
  const [inspectChunks, setInspectChunks] = useState<RagChunk[]>([])
  const [isLoadingChunks, setIsLoadingChunks] = useState(false)
  const [selectedCitation, setSelectedCitation] = useState<RagCitation | null>(null)

  // 1. Fetch authorized documents
  const { data: docList, isLoading: isLoadingDocs, refetch: refetchDocs } = useQuery<{ total: number; documents: RagDocument[] }>({
    queryKey: ['rag-documents'],
    queryFn: async () => {
      const res = await api.get('/api/v1/rag/documents')
      return res.data
    }
  })

  // 2. Fetch RAG health
  const { data: health } = useQuery({
    queryKey: ['rag-health'],
    queryFn: async () => {
      const res = await api.get('/api/v1/rag/health')
      return res.data
    }
  })

  // Document upload mutation
  const uploadMutation = useMutation({
    mutationFn: async (formData: FormData) => {
      const res = await api.post('/api/v1/rag/documents', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      })
      return res.data
    },
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['rag-documents'] })
      queryClient.invalidateQueries({ queryKey: ['rag-health'] })
      setUploadFile(null)
      setCustomTitle('')
      setUploadError(null)
      setFeedbackMsg(`Successfully indexed "${data.title}" (${data.total_chunks} chunks)!`)
      setTimeout(() => setFeedbackMsg(null), 5000)
    },
    onError: (err: any) => {
      const msg = err.response?.data?.detail || err.message || 'Failed to upload document.'
      setUploadError(msg)
    }
  })

  // Delete mutation
  const deleteMutation = useMutation({
    mutationFn: async (id: string) => {
      await api.delete(`/api/v1/rag/documents/${id}`)
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['rag-documents'] })
      queryClient.invalidateQueries({ queryKey: ['rag-health'] })
      setFeedbackMsg('Document deleted and vector index synchronized.')
      setTimeout(() => setFeedbackMsg(null), 5000)
    }
  })

  // Reindex mutation
  const reindexMutation = useMutation({
    mutationFn: async (id: string) => {
      const res = await api.post(`/api/v1/rag/documents/${id}/reindex`)
      return res.data
    },
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['rag-documents'] })
      setFeedbackMsg(`Reindexed "${data.title}" successfully.`)
      setTimeout(() => setFeedbackMsg(null), 5000)
    }
  })

  // Seed sample documents mutation
  const seedMutation = useMutation({
    mutationFn: async () => {
      const res = await api.post('/api/v1/rag/seed-sample-knowledge')
      return res.data
    },
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['rag-documents'] })
      queryClient.invalidateQueries({ queryKey: ['rag-health'] })
      setFeedbackMsg(`Successfully indexed standard corporate policy documents (${data.total} documents)!`)
      setTimeout(() => setFeedbackMsg(null), 5000)
    },
    onError: (err: any) => {
      const msg = err.response?.data?.detail || err.message || 'Failed to seed sample documents.'
      setUploadError(msg)
    }
  })

  const handleUploadSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (!uploadFile) return
    setUploadError(null)

    const formData = new FormData()
    formData.append('file', uploadFile)
    if (customTitle.trim()) {
      formData.append('title', customTitle.trim())
    }
    uploadMutation.mutate(formData)
  }

  const handleAskQuestion = async (promptText?: string) => {
    const q = (promptText || queryInput).trim()
    if (!q || isAsking) return

    const userMsg: ChatMessage = {
      id: `user-${Date.now()}`,
      sender: 'user',
      text: q,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    }

    setMessages((prev) => [...prev, userMsg])
    setQueryInput('')
    setIsAsking(true)

    try {
      const payload = {
        query: q,
        top_k: 4,
        similarity_threshold: similarityThreshold,
        document_id: selectedDocId !== 'ALL' ? selectedDocId : undefined
      }

      const res = await api.post('/api/v1/rag/chat', payload, { timeout: 60000 })
      const data = res.data

      const assistantMsg: ChatMessage = {
        id: `ast-${Date.now()}`,
        sender: 'assistant',
        text: data.answer,
        intent: data.intent,
        citations: data.citations || [],
        hasContext: data.has_sufficient_context,
        model: data.model,
        timeMs: data.execution_time_ms,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
      }

      setMessages((prev) => [...prev, assistantMsg])
    } catch (err: any) {
      const errText = err.response?.data?.detail || err.message || 'Error executing RAG search.'
      const errorMsg: ChatMessage = {
        id: `err-${Date.now()}`,
        sender: 'assistant',
        text: `Error: ${errText}. Please ensure your backend is running.`,
        hasContext: false,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
      }
      setMessages((prev) => [...prev, errorMsg])
    } finally {
      setIsAsking(false)
    }
  }

  const handleOpenDocChunks = async (doc: RagDocument) => {
    setInspectDoc(doc)
    setIsLoadingChunks(true)
    try {
      const res = await api.get(`/api/v1/rag/documents/${doc.id}`)
      setInspectChunks(res.data.chunks || [])
    } catch (err) {
      setInspectChunks([])
    } finally {
      setIsLoadingChunks(false)
    }
  }

  const promptSuggestions = [
    'What is our return and restocking fee policy?',
    'Summarize wholesale bulk discount thresholds',
    'What are the guidelines for warranty claims on hardware?',
    'Why did sales drop, and what does our sales policy recommend?'
  ]

  return (
    <div className="max-w-7xl mx-auto space-y-6 select-text">
      {/* Top Header */}
      <header className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4 bg-surface p-6 rounded-2xl border border-slate-700 shadow-xl">
        <div>
          <div className="flex items-center gap-3 mb-1">
            <div className="p-2.5 rounded-xl bg-primary/10 border border-primary/20 text-primary">
              <BookOpen className="w-6 h-6" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h1 className="text-2xl font-bold text-white tracking-tight">Knowledge Assistant & RAG Studio</h1>
                <span className="text-xs bg-gradient-to-r from-blue-500 to-indigo-600 text-white font-semibold px-2.5 py-0.5 rounded-full shadow-sm">
                  Grounded Intelligence
                </span>
              </div>
              <p className="text-xs text-slate-400 mt-0.5">
                Semantic retrieval over verified business documents, policies, and ledger actuals powered by Google Gemini.
              </p>
            </div>
          </div>
        </div>

        {/* Live Vector Engine Status & Quick Actions */}
        <div className="flex flex-wrap items-center gap-3">
          <button
            onClick={() => seedMutation.mutate()}
            disabled={seedMutation.isPending}
            className="flex items-center gap-2 bg-slate-800 hover:bg-slate-700 border border-slate-600 text-slate-200 hover:text-white px-3.5 py-2.5 rounded-xl text-xs font-semibold shadow-sm transition-all disabled:opacity-50 cursor-pointer"
            title="Seed standard return policies, wholesale discount schedules, and product catalog docs into your vector store"
          >
            {seedMutation.isPending ? (
              <Loader2 className="w-4 h-4 animate-spin text-primary" />
            ) : (
              <Sparkles className="w-4 h-4 text-amber-400" />
            )}
            <span>Seed Sample Policies</span>
          </button>

          <div className="flex items-center gap-3 bg-background/80 px-4 py-2.5 rounded-xl border border-slate-700 text-xs">
            <div className="w-2.5 h-2.5 rounded-full bg-emerald-500 animate-pulse" />
            <div>
              <div className="font-semibold text-white">Dual-Layer Vector Store</div>
              <div className="text-[11px] text-slate-400">
                {health?.total_documents ?? docList?.total ?? 0} Docs • {health?.total_chunks ?? 0} Chunks • FAISS Accelerated
              </div>
            </div>
          </div>
        </div>
      </header>

      {/* Notification Toast */}
      {feedbackMsg && (
        <div className="bg-emerald-950/80 border border-emerald-700/60 text-emerald-200 px-4 py-3 rounded-xl flex items-center justify-between text-xs animate-in fade-in duration-300">
          <div className="flex items-center gap-2">
            <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
            <span>{feedbackMsg}</span>
          </div>
          <button onClick={() => setFeedbackMsg(null)} className="text-emerald-400 hover:text-white">
            <X className="w-4 h-4" />
          </button>
        </div>
      )}

      {/* Tabs */}
      <div className="flex gap-2 border-b border-slate-700 pb-3">
        <button
          onClick={() => setActiveTab('chat')}
          className={`flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-semibold transition-all ${
            activeTab === 'chat'
              ? 'bg-primary text-white shadow-lg shadow-primary/20'
              : 'text-slate-400 hover:text-white hover:bg-surface'
          }`}
        >
          <MessageSquare className="w-4 h-4" />
          Knowledge Assistant Chat
        </button>
        <button
          onClick={() => setActiveTab('documents')}
          className={`flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-semibold transition-all ${
            activeTab === 'documents'
              ? 'bg-primary text-white shadow-lg shadow-primary/20'
              : 'text-slate-400 hover:text-white hover:bg-surface'
          }`}
        >
          <Layers className="w-4 h-4" />
          Document Ingestion & Index ({docList?.total ?? 0})
        </button>
      </div>

      {/* TAB 1: KNOWLEDGE CHAT */}
      {activeTab === 'chat' && (
        <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
          {/* Main Chat Feed */}
          <div className="lg:col-span-3 flex flex-col bg-surface border border-slate-700 rounded-2xl h-[700px] shadow-xl overflow-hidden">
            {/* Chat Control Bar */}
            <div className="p-3.5 bg-slate-900/60 border-b border-slate-700/80 flex flex-wrap items-center justify-between gap-3 text-xs">
              <div className="flex items-center gap-2">
                <span className="text-slate-400 font-medium">Document Scope:</span>
                <select
                  value={selectedDocId}
                  onChange={(e) => setSelectedDocId(e.target.value)}
                  className="bg-background text-white text-xs px-2.5 py-1.5 rounded-lg border border-slate-600 focus:outline-none focus:border-primary"
                >
                  <option value="ALL">Entire Knowledge Base (All Documents)</option>
                  {docList?.documents.map((d) => (
                    <option key={d.id} value={d.id}>
                      {d.title} ({d.file_type.toUpperCase()})
                    </option>
                  ))}
                </select>
              </div>

              <div className="flex items-center gap-3 text-[11px] text-slate-400">
                <span>Similarity Threshold: <strong>{(similarityThreshold * 100).toFixed(0)}%</strong></span>
                <input
                  type="range"
                  min="0.30"
                  max="0.90"
                  step="0.05"
                  value={similarityThreshold}
                  onChange={(e) => setSimilarityThreshold(parseFloat(e.target.value))}
                  className="w-20 accent-primary cursor-pointer"
                />
              </div>
            </div>

            {/* Messages Scroll Area */}
            <div className="flex-1 p-5 overflow-y-auto space-y-4">
              {messages.map((m) => (
                <div
                  key={m.id}
                  className={`flex flex-col ${m.sender === 'user' ? 'items-end' : 'items-start'}`}
                >
                  <div
                    className={`max-w-[85%] rounded-2xl p-4 text-xs leading-relaxed shadow-md ${
                      m.sender === 'user'
                        ? 'bg-primary text-white rounded-br-xs'
                        : 'bg-background/90 text-slate-200 border border-slate-700/90 rounded-bl-xs'
                    }`}
                  >
                    {/* Assistant Metadata Badge */}
                    {m.sender === 'assistant' && (
                      <div className="flex items-center gap-2 mb-2 pb-2 border-b border-slate-700/60 text-[10px]">
                        <span className="flex items-center gap-1 font-semibold text-primary">
                          <Sparkles className="w-3 h-3" />
                          {m.model || 'SalesMind Grounded AI'}
                        </span>
                        {m.intent && (
                          <span
                            className={`px-2 py-0.5 rounded-full font-mono uppercase text-[9px] font-bold ${
                              m.intent === 'LEDGER_ANALYTICS'
                                ? 'bg-emerald-950 text-emerald-300 border border-emerald-700'
                                : m.intent === 'HYBRID'
                                ? 'bg-purple-950 text-purple-300 border border-purple-700'
                                : 'bg-blue-950 text-blue-300 border border-blue-700'
                            }`}
                          >
                            {m.intent.replace('_', ' ')}
                          </span>
                        )}
                        {m.timeMs && <span className="text-slate-500 ml-auto">{m.timeMs}ms</span>}
                      </div>
                    )}

                    {/* Message Body */}
                    <div className="whitespace-pre-wrap">{m.text}</div>

                    {/* Insufficient Evidence Warning Banner */}
                    {m.sender === 'assistant' && !m.hasContext && (
                      <div className="mt-3 p-2.5 rounded-xl bg-amber-950/40 border border-amber-800/60 text-amber-200 text-[11px] flex items-center gap-2">
                        <AlertTriangle className="w-4 h-4 text-amber-400 shrink-0" />
                        <span>No direct evidence in knowledge base. The assistant honestly abstained rather than fabricating facts.</span>
                      </div>
                    )}

                    {/* Source Citations Tray */}
                    {m.citations && m.citations.length > 0 && (
                      <div className="mt-3 pt-3 border-t border-slate-700/60">
                        <div className="text-[10px] font-semibold uppercase tracking-wider text-slate-400 mb-1.5 flex items-center gap-1">
                          <ShieldCheck className="w-3 h-3 text-emerald-400" />
                          Grounded Source Citations ({m.citations.length})
                        </div>
                        <div className="flex flex-wrap gap-1.5">
                          {m.citations.map((c) => (
                            <button
                              key={c.citation_id}
                              onClick={() => setSelectedCitation(c)}
                              className="group flex items-center gap-1 px-2.5 py-1 rounded-lg bg-surface/90 border border-slate-600 hover:border-primary text-slate-300 hover:text-white transition-all text-[11px]"
                            >
                              <span className="font-mono text-primary font-bold">[{c.citation_id}]</span>
                              <span className="max-w-[120px] truncate">{c.document_title}</span>
                              {c.page_number && <span className="text-slate-400 text-[10px]">p.{c.page_number}</span>}
                              <span className="text-emerald-400 text-[10px]">{(c.similarity_score * 100).toFixed(0)}%</span>
                            </button>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                  <span className="text-[10px] text-slate-500 mt-1 px-1">{m.timestamp}</span>
                </div>
              ))}

              {isAsking && (
                <div className="flex items-center gap-2 text-slate-400 text-xs bg-background/60 p-3 rounded-xl border border-slate-700 w-fit">
                  <Loader2 className="w-4 h-4 animate-spin text-primary" />
                  <span>Retrieving knowledge chunks and querying Google Gemini...</span>
                </div>
              )}
            </div>

            {/* Prompt Suggestions */}
            <div className="px-5 py-2 bg-slate-900/40 border-t border-slate-800 flex items-center gap-2 overflow-x-auto text-[11px]">
              <span className="text-slate-500 shrink-0">Try:</span>
              {promptSuggestions.map((s, idx) => (
                <button
                  key={idx}
                  onClick={() => handleAskQuestion(s)}
                  className="px-2.5 py-1 rounded-full bg-slate-800/80 hover:bg-slate-700 text-slate-300 hover:text-white whitespace-nowrap transition-colors border border-slate-700/60"
                >
                  {s}
                </button>
              ))}
            </div>

            {/* Input Form */}
            <form
              onSubmit={(e) => {
                e.preventDefault()
                handleAskQuestion()
              }}
              className="p-3 bg-surface border-t border-slate-700 flex items-center gap-2"
            >
              <input
                type="text"
                value={queryInput}
                onChange={(e) => setQueryInput(e.target.value)}
                placeholder="Ask about sales policies, return guidelines, or sales performance explanations..."
                disabled={isAsking}
                className="flex-1 bg-background text-white text-xs px-4 py-3 rounded-xl border border-slate-700 focus:outline-none focus:border-primary disabled:opacity-50"
              />
              <button
                type="submit"
                disabled={isAsking || !queryInput.trim()}
                className="bg-primary hover:bg-blue-600 disabled:opacity-50 text-white text-xs font-semibold px-5 py-3 rounded-xl shadow-lg shadow-primary/20 transition-all flex items-center gap-2 shrink-0 cursor-pointer"
              >
                {isAsking ? <Loader2 className="w-4 h-4 animate-spin" /> : <Sparkles className="w-4 h-4" />}
                Ask Assistant
              </button>
            </form>
          </div>

          {/* Right Column: Knowledge Base Sidebar */}
          <div className="space-y-4">
            <div className="bg-surface p-5 rounded-2xl border border-slate-700 shadow-xl space-y-4">
              <h3 className="text-sm font-bold text-white flex items-center gap-2">
                <Layers className="w-4 h-4 text-primary" />
                Indexed Knowledge Base
              </h3>
              <p className="text-xs text-slate-400">
                {docList?.total ?? 0} documents currently indexed and searchable in your active organization workspace.
              </p>

              <div className="space-y-2 max-h-[380px] overflow-y-auto pr-1">
                {isLoadingDocs ? (
                  <div className="text-center py-6 text-slate-500 text-xs">
                    <Loader2 className="w-4 h-4 animate-spin mx-auto mb-1 text-primary" />
                    Loading indexed documents...
                  </div>
                ) : docList?.documents && docList.documents.length > 0 ? (
                  docList.documents.map((d) => (
                    <div
                      key={d.id}
                      className="p-3 rounded-xl bg-background/80 border border-slate-700/80 hover:border-slate-600 transition-all text-xs space-y-1.5"
                    >
                      <div className="flex items-center justify-between">
                        <span className="font-semibold text-white truncate max-w-[140px]" title={d.title}>
                          {d.title}
                        </span>
                        <span className="px-1.5 py-0.5 rounded text-[10px] font-mono uppercase bg-slate-800 text-slate-300 font-bold">
                          {d.file_type}
                        </span>
                      </div>
                      <div className="flex items-center justify-between text-[11px] text-slate-400">
                        <span>{d.total_chunks} chunks</span>
                        <span>{(d.file_size / 1024).toFixed(0)} KB</span>
                      </div>
                      <div className="flex items-center gap-2 pt-1">
                        <button
                          onClick={() => handleOpenDocChunks(d)}
                          className="text-[11px] text-primary hover:underline flex items-center gap-1"
                        >
                          View Chunks
                        </button>
                        <span className="text-slate-600">•</span>
                        <button
                          onClick={() => setSelectedDocId(d.id)}
                          className="text-[11px] text-slate-400 hover:text-white"
                        >
                          Filter to Doc
                        </button>
                      </div>
                    </div>
                  ))
                ) : (
                  <div className="text-center py-6 text-slate-500 text-xs bg-background/50 rounded-xl border border-dashed border-slate-700">
                    No documents indexed yet. Click "Ingest New Document" below.
                  </div>
                )}
              </div>

              <button
                onClick={() => setActiveTab('documents')}
                className="w-full bg-slate-800 hover:bg-slate-700 text-white text-xs font-semibold py-2.5 rounded-xl border border-slate-600 transition-colors flex items-center justify-center gap-2 cursor-pointer"
              >
                <UploadCloud className="w-4 h-4 text-primary" />
                Ingest New Document
              </button>
            </div>

            {/* Citation Snippet Modal / Popover */}
            {selectedCitation && (
              <div className="bg-surface p-4 rounded-2xl border border-primary/40 shadow-2xl space-y-2 animate-in fade-in duration-200">
                <div className="flex items-center justify-between border-b border-slate-700 pb-2">
                  <div className="flex items-center gap-1.5">
                    <span className="font-mono text-primary font-bold text-xs">[{selectedCitation.citation_id}]</span>
                    <span className="font-semibold text-white text-xs truncate max-w-[150px]">
                      {selectedCitation.document_title}
                    </span>
                  </div>
                  <button onClick={() => setSelectedCitation(null)} className="text-slate-400 hover:text-white">
                    <X className="w-4 h-4" />
                  </button>
                </div>
                <div className="text-[11px] text-slate-400 space-y-1">
                  <div>Section: <strong className="text-slate-200">{selectedCitation.section_title}</strong></div>
                  {selectedCitation.page_number && <div>Page: <strong className="text-slate-200">{selectedCitation.page_number}</strong></div>}
                  <div>Cosine Relevance: <strong className="text-emerald-400">{(selectedCitation.similarity_score * 100).toFixed(1)}%</strong></div>
                </div>
                <div className="p-2.5 rounded-lg bg-background text-[11px] text-slate-300 font-serif leading-relaxed max-h-36 overflow-y-auto border border-slate-800">
                  "{selectedCitation.snippet}"
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* TAB 2: DOCUMENT INGESTION & LEDGER */}
      {activeTab === 'documents' && (
        <div className="space-y-6">
          {/* Upload Dropzone Card */}
          <div className="bg-surface p-6 rounded-2xl border border-slate-700 shadow-xl space-y-4">
            <h3 className="text-base font-bold text-white flex items-center gap-2">
              <UploadCloud className="w-5 h-5 text-primary" />
              Ingest Knowledge Base Document
            </h3>
            <p className="text-xs text-slate-400">
              Upload documents to automatically extract, chunk, embed, and index into your workspace vector store.
              Supported formats: <strong>PDF, DOCX, TXT, Markdown (.md), CSV, TSV, JSON</strong> (up to 25MB).
            </p>

            <form onSubmit={handleUploadSubmit} className="space-y-4">
              <div
                onClick={() => fileInputRef.current?.click()}
                className={`border-2 border-dashed rounded-2xl p-8 text-center cursor-pointer transition-all ${
                  uploadFile
                    ? 'border-primary bg-primary/5'
                    : 'border-slate-700 hover:border-slate-500 bg-background/50'
                }`}
              >
                <input
                  ref={fileInputRef}
                  type="file"
                  accept=".pdf,.docx,.txt,.md,.markdown,.csv,.tsv,.json,.jsonl"
                  onChange={(e) => {
                    if (e.target.files && e.target.files[0]) {
                      setUploadFile(e.target.files[0])
                      setUploadError(null)
                    }
                  }}
                  className="hidden"
                />
                <div className="flex flex-col items-center gap-2">
                  <div className="p-3 rounded-full bg-slate-800 text-primary">
                    <FileText className="w-8 h-8" />
                  </div>
                  {uploadFile ? (
                    <div>
                      <div className="font-semibold text-white text-sm">{uploadFile.name}</div>
                      <div className="text-xs text-slate-400">{(uploadFile.size / 1024).toFixed(1)} KB • Ready for indexing</div>
                    </div>
                  ) : (
                    <div>
                      <div className="text-sm font-semibold text-white">Click or drag & drop a file here</div>
                      <div className="text-xs text-slate-400 mt-1">PDF, DOCX, TXT, MD, CSV, TSV, JSON</div>
                    </div>
                  )}
                </div>
              </div>

              {/* Optional Custom Title */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="text-xs font-medium text-slate-300 block mb-1">Document Display Title (Optional)</label>
                  <input
                    type="text"
                    value={customTitle}
                    onChange={(e) => setCustomTitle(e.target.value)}
                    placeholder="e.g. Corporate Hardware Return Policy 2026"
                    className="w-full bg-background text-white text-xs px-3.5 py-2.5 rounded-xl border border-slate-700 focus:outline-none focus:border-primary"
                  />
                </div>
                <div className="flex items-end">
                  <button
                    type="submit"
                    disabled={!uploadFile || uploadMutation.isPending}
                    className="w-full bg-primary hover:bg-blue-600 disabled:opacity-50 text-white text-xs font-semibold py-2.5 rounded-xl shadow-lg shadow-primary/20 transition-all flex items-center justify-center gap-2 cursor-pointer"
                  >
                    {uploadMutation.isPending ? (
                      <>
                        <Loader2 className="w-4 h-4 animate-spin" />
                        Extracting, Chunking & Indexing...
                      </>
                    ) : (
                      <>
                        <UploadCloud className="w-4 h-4" />
                        Ingest & Index Document
                      </>
                    )}
                  </button>
                </div>
              </div>

              {uploadError && (
                <div className="p-3 rounded-xl bg-rose-950/60 border border-rose-800 text-rose-300 text-xs flex items-center gap-2">
                  <AlertTriangle className="w-4 h-4 text-rose-400 shrink-0" />
                  <span>{uploadError}</span>
                </div>
              )}
            </form>
          </div>

          {/* Document Inventory Table */}
          <div className="bg-surface p-6 rounded-2xl border border-slate-700 shadow-xl space-y-4">
            <div className="flex items-center justify-between">
              <h3 className="text-base font-bold text-white flex items-center gap-2">
                <FileCheck className="w-5 h-5 text-emerald-400" />
                Active Knowledge Document Ledger
              </h3>
              <button
                onClick={() => refetchDocs()}
                className="text-xs text-slate-400 hover:text-white flex items-center gap-1.5 transition-colors"
              >
                <RefreshCw className="w-3.5 h-3.5" />
                Refresh
              </button>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs border-collapse">
                <thead>
                  <tr className="border-b border-slate-700 text-slate-400 font-semibold bg-background/50">
                    <th className="py-3 px-4">Document Title</th>
                    <th className="py-3 px-4">Filename</th>
                    <th className="py-3 px-4">Format</th>
                    <th className="py-3 px-4">Chunks</th>
                    <th className="py-3 px-4">Size</th>
                    <th className="py-3 px-4">Status</th>
                    <th className="py-3 px-4 text-right">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800">
                  {isLoadingDocs ? (
                    <tr>
                      <td colSpan={7} className="text-center py-8 text-slate-500">
                        <Loader2 className="w-5 h-5 animate-spin mx-auto mb-2 text-primary" />
                        Loading document ledger...
                      </td>
                    </tr>
                  ) : docList?.documents && docList.documents.length > 0 ? (
                    docList.documents.map((doc) => (
                      <tr key={doc.id} className="hover:bg-slate-800/40 transition-colors">
                        <td className="py-3 px-4 font-semibold text-white">{doc.title}</td>
                        <td className="py-3 px-4 text-slate-400">{doc.original_filename}</td>
                        <td className="py-3 px-4">
                          <span className="px-2 py-0.5 rounded text-[10px] font-mono uppercase bg-slate-800 text-slate-300 font-bold border border-slate-700">
                            {doc.file_type}
                          </span>
                        </td>
                        <td className="py-3 px-4 font-mono text-slate-300">{doc.total_chunks}</td>
                        <td className="py-3 px-4 text-slate-400">{(doc.file_size / 1024).toFixed(1)} KB</td>
                        <td className="py-3 px-4">
                          <span
                            className={`px-2 py-0.5 rounded-full text-[10px] font-semibold ${
                              doc.status === 'INDEXED'
                                ? 'bg-emerald-950 text-emerald-300 border border-emerald-700'
                                : doc.status === 'PROCESSING'
                                ? 'bg-amber-950 text-amber-300 border border-amber-700 animate-pulse'
                                : 'bg-rose-950 text-rose-300 border border-rose-700'
                            }`}
                          >
                            {doc.status}
                          </span>
                        </td>
                        <td className="py-3 px-4 text-right space-x-2">
                          <button
                            onClick={() => handleOpenDocChunks(doc)}
                            className="px-2 py-1 rounded bg-slate-800 hover:bg-slate-700 text-slate-300 hover:text-white transition-colors"
                            title="Inspect semantic chunks"
                          >
                            Chunks
                          </button>
                          <button
                            onClick={() => reindexMutation.mutate(doc.id)}
                            disabled={reindexMutation.isPending}
                            className="px-2 py-1 rounded bg-slate-800 hover:bg-slate-700 text-slate-300 hover:text-white transition-colors"
                            title="Reindex document"
                          >
                            Reindex
                          </button>
                          <button
                            onClick={() => {
                              if (confirm(`Are you sure you want to delete "${doc.title}"?`)) {
                                deleteMutation.mutate(doc.id)
                              }
                            }}
                            className="px-2 py-1 rounded bg-rose-950/60 hover:bg-rose-900 text-rose-300 hover:text-white transition-colors"
                            title="Delete document"
                          >
                            <Trash2 className="w-3.5 h-3.5 inline" />
                          </button>
                        </td>
                      </tr>
                    ))
                  ) : (
                    <tr>
                      <td colSpan={7} className="text-center py-10 text-slate-400">
                        <div className="flex flex-col items-center justify-center space-y-3">
                          <p className="text-xs">No documents currently indexed in this workspace. Upload your first document above or seed default corporate policies.</p>
                          <button
                            onClick={() => seedMutation.mutate()}
                            disabled={seedMutation.isPending}
                            className="inline-flex items-center gap-2 bg-primary/20 hover:bg-primary/30 text-primary border border-primary/40 px-4 py-2 rounded-xl text-xs font-semibold transition-all cursor-pointer disabled:opacity-50"
                          >
                            {seedMutation.isPending ? (
                              <Loader2 className="w-3.5 h-3.5 animate-spin" />
                            ) : (
                              <Sparkles className="w-3.5 h-3.5 text-amber-400" />
                            )}
                            Seed Standard Sales Playbook & Return Policies
                          </button>
                        </div>
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {/* INSPECT CHUNKS MODAL */}
      {inspectDoc && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-xs p-4 animate-in fade-in duration-200">
          <div className="bg-surface border border-slate-700 rounded-2xl max-w-3xl w-full max-h-[85vh] flex flex-col shadow-2xl">
            {/* Modal Header */}
            <div className="p-4 border-b border-slate-700 flex items-center justify-between">
              <div>
                <h3 className="text-sm font-bold text-white flex items-center gap-2">
                  <Layers className="w-4 h-4 text-primary" />
                  Semantic Chunk Explorer: {inspectDoc.title}
                </h3>
                <p className="text-[11px] text-slate-400">
                  {inspectDoc.total_chunks} discrete chunks indexed in FAISS vector store.
                </p>
              </div>
              <button
                onClick={() => setInspectDoc(null)}
                className="text-slate-400 hover:text-white p-1 rounded-lg hover:bg-slate-800"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Modal Body */}
            <div className="p-5 overflow-y-auto space-y-3 flex-1 text-xs">
              {isLoadingChunks ? (
                <div className="text-center py-12 text-slate-400">
                  <Loader2 className="w-6 h-6 animate-spin mx-auto mb-2 text-primary" />
                  Loading semantic chunks...
                </div>
              ) : inspectChunks.length > 0 ? (
                inspectChunks.map((c) => (
                  <div key={c.id} className="p-3.5 rounded-xl bg-background border border-slate-700/80 space-y-1.5">
                    <div className="flex items-center justify-between text-[11px]">
                      <span className="font-mono text-primary font-bold">Chunk #{c.chunk_index + 1}</span>
                      <div className="flex items-center gap-2 text-slate-400">
                        {c.section_title && <span>Section: <strong>{c.section_title}</strong></span>}
                        {c.page_number && <span>Page: <strong>{c.page_number}</strong></span>}
                        <span>~{c.token_count} tokens</span>
                      </div>
                    </div>
                    <div className="text-slate-300 font-serif leading-relaxed bg-slate-900/60 p-2.5 rounded-lg border border-slate-800/80 whitespace-pre-wrap">
                      {c.chunk_text}
                    </div>
                  </div>
                ))
              ) : (
                <div className="text-center py-12 text-slate-500">
                  No chunks found for this document.
                </div>
              )}
            </div>

            {/* Modal Footer */}
            <div className="p-4 border-t border-slate-700 flex justify-end">
              <button
                onClick={() => setInspectDoc(null)}
                className="px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-white text-xs font-semibold cursor-pointer"
              >
                Close Explorer
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

