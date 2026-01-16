import { DocumentInfo } from './components/DocumentList'
import { ProcessingStats, SystemStats } from './components/StatsPanel'
import { StatsPanel } from './components/StatsPanel'
import { LogPanel } from './components/LogPanel'
import { DocumentList } from './components/DocumentList'
import { CurrentDocPanel } from './components/CurrentDocPanel'
import { LLMResponsesPanel } from './components/LLMResponsesPanel'
import { Controls } from './components/Controls'
import { HistoryPanel, HistoryEntry } from './components/HistoryPanel'
import { useState, useEffect, useRef } from 'react'

// Backend API base URL
const API_BASE = '/api'

function App() {
  const [stats, setStats] = useState<ProcessingStats>({ total: 0, processed: 0, high_quality: 0, low_quality: 0, no_consensus: 0, errors: 0, skipped: 0 })
  const [sysStats, setSysStats] = useState<SystemStats | undefined>(undefined)
  const [documents, setDocuments] = useState<DocumentInfo[]>([])
  const [currentDoc, setCurrentDoc] = useState<DocumentInfo | null>(null)
  const [logs, setLogs] = useState<string[]>([])
  const [llmResponses, setLlmResponses] = useState<Record<string, string>>({})

  // History state
  const [history, setHistory] = useState<HistoryEntry[]>([])
  const [activeTab, setActiveTab] = useState<'live' | 'history'>('live')

  const [processing, setProcessing] = useState(false)
  const [paused, setPaused] = useState(false)
  const [loading, setLoading] = useState(false)

  const pollRef = useRef<number | null>(null)

  const addLog = (msg: string) => {
    const timestamp = new Date().toLocaleTimeString()
    setLogs(prev => [...prev.slice(-99), `[${timestamp}] ${msg}`])
  }

  // Fetch status from backend
  const fetchStatus = async () => {
    try {
      const resp = await fetch(`${API_BASE}/status`)
      if (!resp.ok) throw new Error('Failed to fetch status')
      const data = await resp.json()

      setProcessing(data.processing)
      setPaused(data.paused)
      setStats(data.stats)
      setCurrentDoc(data.current_doc)
      setLlmResponses(data.llm_responses || {})
      setDocuments(data.documents?.map((d: any) => ({
        id: d.id,
        title: d.title,
        content: d.content,
        status: d.status,
        new_title: d.new_title
      })) || [])

      // If history is active, we rely on the history endpoint, 
      // but status might also contain recent history if we wanted.
    } catch (e) {
      // Backend not available yet
    }
  }

  // Fetch logs from backend
  const fetchLogs = async () => {
    try {
      const resp = await fetch(`${API_BASE}/logs`)
      if (!resp.ok) return
      const data = await resp.json()
      setLogs(data.logs || [])
    } catch (e) {
      // Ignore
    }
  }

  // Fetch history
  const fetchHistory = async () => {
    try {
      const resp = await fetch(`${API_BASE}/history`)
      if (!resp.ok) return
      const data = await resp.json()
      setHistory(data.history || [])
    } catch (e) {
      // Ignore
    }
  }

  // Fetch system stats
  const fetchSysStats = async () => {
    try {
      const resp = await fetch(`${API_BASE}/system-stats`)
      if (!resp.ok) return
      const data = await resp.json()
      setSysStats(data)
    } catch (e) {
      // Ignore
    }
  }

  // Start polling on mount
  useEffect(() => {
    addLog('[System] Frontend connected. Polling backend...')

    // Initial fetch
    fetchStatus()
    fetchLogs()
    fetchHistory()
    fetchSysStats()

    // Poll every 1.5 seconds
    const interval = setInterval(() => {
      fetchStatus()
      fetchLogs()
      fetchSysStats()
      // Always fetch history to keep it updated even in background
      fetchHistory()
    }, 1500)

    pollRef.current = interval

    return () => {
      if (pollRef.current) clearInterval(pollRef.current)
    }
  }, [])

  // Control handlers - send to backend
  const startProcessing = async () => {
    setLoading(true)
    try {
      const resp = await fetch(`${API_BASE}/start`, { method: 'POST' })
      const data = await resp.json()
      addLog(`[System] ${data.message}`)
    } catch (e: any) {
      addLog(`[Error] Failed to start: ${e.message}`)
    } finally {
      setLoading(false)
    }
  }

  const stopProcessing = async () => {
    try {
      const resp = await fetch(`${API_BASE}/stop`, { method: 'POST' })
      const data = await resp.json()
      addLog(`[System] ${data.message}`)
    } catch (e: any) {
      addLog(`[Error] Failed to stop: ${e.message}`)
    }
  }

  const togglePause = async () => {
    try {
      const resp = await fetch(`${API_BASE}/pause`, { method: 'POST' })
      const data = await resp.json()
      setPaused(data.paused)
    } catch (e: any) {
      addLog(`[Error] Failed to toggle pause: ${e.message}`)
    }
  }

  return (
    <div className="flex flex-col h-screen w-full bg-background text-foreground text-sm">
      <header className="h-12 bg-secondary flex items-center px-4 font-bold border-b border-border shadow-sm z-20">
        <span className="text-primary mr-2">🤖</span>
        Document Quality Analyzer GUI

        {/* Status Badge */}
        <span className={`ml-4 px-2 py-0.5 rounded text-xs ${processing ? 'bg-green-600' : 'bg-gray-600'}`}>
          {processing ? (paused ? '⏸️ PAUSED' : '▶️ RUNNING') : '⏹️ STOPPED'}
        </span>

        {/* Tab Switcher */}
        <div className="mx-8 flex space-x-1 bg-black/20 p-1 rounded-lg">
          <button
            onClick={() => setActiveTab('live')}
            className={`px-3 py-0.5 rounded-md text-xs font-medium transition-colors ${activeTab === 'live' ? 'bg-primary text-primary-foreground shadow-sm' : 'hover:bg-white/10 text-muted-foreground'}`}
          >
            👁️ Live View
          </button>
          <button
            onClick={() => setActiveTab('history')}
            className={`flex items-center gap-2 px-3 py-0.5 rounded-md text-xs font-medium transition-colors ${activeTab === 'history' ? 'bg-primary text-primary-foreground shadow-sm' : 'hover:bg-white/10 text-muted-foreground'}`}
          >
            <span>📜 History</span>
            <span className="bg-white/20 px-1.5 rounded-full text-[10px]">{history.length}</span>
          </button>
        </div>

        <span className="ml-auto text-xs font-mono text-muted-foreground opacity-50">v2.1.0 (History Enabled)</span>
      </header>

      <main className="flex-1 min-h-0 grid grid-cols-12 gap-1 p-2">
        {activeTab === 'live' ? (
          <>
            {/* Stats - Left Col */}
            <div className="col-span-3 lg:col-span-2 flex flex-col gap-2 h-full">
              <StatsPanel stats={stats} sysStats={sysStats} />
            </div>

            {/* Center - Current Doc & Log */}
            <div className="col-span-6 lg:col-span-7 flex flex-col gap-2 min-h-0">
              <div className="h-[45%] min-h-[200px]">
                <CurrentDocPanel doc={currentDoc} />
              </div>
              <div className="flex-1 min-h-0">
                <LogPanel logs={logs} />
              </div>
            </div>

            {/* Right - Model Responses & List */}
            <div className="col-span-3 lg:col-span-3 flex flex-col gap-2 min-h-0">
              <div className="h-1/3 min-h-[150px]">
                <LLMResponsesPanel responses={llmResponses} />
              </div>
              <div className="flex-1 min-h-0">
                <DocumentList documents={documents} />
              </div>
            </div>
          </>
        ) : (
          /* History View */
          <div className="col-span-12 h-full flex flex-col gap-2">
            <div className="flex-1 min-h-0">
              <HistoryPanel history={history} />
            </div>
            {/* Show stats summary at bottom of history too? Maybe unnecessary if we want max space */}
          </div>
        )}

        <div className="col-span-12 mt-1">
          <div className="w-full bg-secondary h-2.5 rounded-full overflow-hidden">
            <div
              className="bg-green-500 h-full transition-all duration-300 relative"
              style={{ width: `${stats.total > 0 ? (stats.processed / stats.total) * 100 : 0}%` }}
            >
              <div className="absolute inset-0 bg-white/20 animate-pulse"></div>
            </div>
          </div>
        </div>
      </main>

      <Controls
        maxDocs={100}
        setMaxDocs={() => { }}
        onLoad={() => { }}
        onStart={startProcessing}
        onPause={togglePause}
        onQuit={stopProcessing}
        processing={processing}
        paused={paused}
        loading={loading}
      />
    </div>
  )
}

export default App
