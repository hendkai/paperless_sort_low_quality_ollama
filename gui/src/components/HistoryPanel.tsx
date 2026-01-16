import { useState, useMemo, Fragment } from 'react'

export interface HistoryEntry {
    timestamp: string
    doc_id: number
    title: string
    action: string
    reason: string
    details: string
    old_title?: string
    new_title?: string
}

interface HistoryPanelProps {
    history: HistoryEntry[]
}

type FilterType = 'all' | 'renamed' | 'high_quality' | 'low_quality' | 'skipped' | 'error' | 'no_consensus'

export function HistoryPanel({ history }: HistoryPanelProps) {
    const [filter, setFilter] = useState<FilterType>('all')
    const [searchTerm, setSearchTerm] = useState('')
    const [expandedRows, setExpandedRows] = useState<Set<number>>(new Set())

    // Filter logic
    const filteredHistory = useMemo(() => {
        return history.filter(entry => {
            // Search filter
            if (searchTerm) {
                const search = searchTerm.toLowerCase()
                const matchesSearch =
                    entry.title.toLowerCase().includes(search) ||
                    entry.details.toLowerCase().includes(search) ||
                    entry.doc_id.toString().includes(search)
                if (!matchesSearch) return false
            }

            // Type filter
            switch (filter) {
                case 'renamed':
                    return !!(entry.old_title && entry.new_title)
                case 'high_quality':
                    return entry.reason === 'high_quality'
                case 'low_quality':
                    return entry.reason === 'low_quality'
                case 'skipped':
                    return entry.action === 'skipped'
                case 'error':
                    return entry.action === 'error'
                case 'no_consensus':
                    return entry.reason === 'no_consensus'
                default:
                    return true
            }
        })
    }, [history, filter, searchTerm])

    // Statistics for filter badges
    const stats = useMemo(() => ({
        all: history.length,
        renamed: history.filter(e => !!(e.old_title && e.new_title)).length,
        high_quality: history.filter(e => e.reason === 'high_quality').length,
        low_quality: history.filter(e => e.reason === 'low_quality').length,
        skipped: history.filter(e => e.action === 'skipped').length,
        error: history.filter(e => e.action === 'error').length,
        no_consensus: history.filter(e => e.reason === 'no_consensus').length,
    }), [history])

    const toggleRow = (index: number) => {
        setExpandedRows(prev => {
            const newSet = new Set(prev)
            if (newSet.has(index)) {
                newSet.delete(index)
            } else {
                newSet.add(index)
            }
            return newSet
        })
    }

    const filterButtons: { key: FilterType; label: string; icon: string; color: string }[] = [
        { key: 'all', label: 'All', icon: '📋', color: 'bg-gray-500/20 text-gray-300' },
        { key: 'renamed', label: 'Renamed', icon: '✏️', color: 'bg-blue-500/20 text-blue-400' },
        { key: 'high_quality', label: 'High Quality', icon: '✅', color: 'bg-green-500/20 text-green-400' },
        { key: 'low_quality', label: 'Low Quality', icon: '📉', color: 'bg-orange-500/20 text-orange-400' },
        { key: 'skipped', label: 'Skipped', icon: '⏭️', color: 'bg-yellow-500/20 text-yellow-400' },
        { key: 'no_consensus', label: 'No Consensus', icon: '🤷', color: 'bg-purple-500/20 text-purple-400' },
        { key: 'error', label: 'Error', icon: '❌', color: 'bg-red-500/20 text-red-400' },
    ]

    return (
        <div className="flex flex-col h-full bg-secondary/30 rounded-lg overflow-hidden border border-border">
            {/* Header with search and filters */}
            <div className="bg-secondary px-3 py-2 border-b border-border space-y-2">
                <div className="flex justify-between items-center">
                    <h3 className="font-semibold text-sm">📜 Processing History</h3>
                    <span className="text-xs text-muted-foreground">
                        {filteredHistory.length} of {history.length} entries
                    </span>
                </div>

                {/* Search bar */}
                <div className="relative">
                    <input
                        type="text"
                        placeholder="Search by title, ID or details..."
                        value={searchTerm}
                        onChange={(e) => setSearchTerm(e.target.value)}
                        className="w-full bg-black/20 border border-border rounded px-3 py-1.5 text-xs placeholder:text-muted-foreground focus:outline-none focus:ring-1 focus:ring-primary"
                    />
                    {searchTerm && (
                        <button
                            onClick={() => setSearchTerm('')}
                            className="absolute right-2 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
                        >
                            ✕
                        </button>
                    )}
                </div>

                {/* Filter buttons */}
                <div className="flex flex-wrap gap-1">
                    {filterButtons.map(btn => (
                        <button
                            key={btn.key}
                            onClick={() => setFilter(btn.key)}
                            className={`inline-flex items-center gap-1 px-2 py-1 rounded text-[10px] font-medium transition-all ${
                                filter === btn.key
                                    ? btn.color + ' ring-1 ring-white/30'
                                    : 'bg-black/20 text-muted-foreground hover:bg-black/30'
                            }`}
                        >
                            <span>{btn.icon}</span>
                            <span>{btn.label}</span>
                            <span className="bg-black/30 px-1 rounded">{stats[btn.key]}</span>
                        </button>
                    ))}
                </div>
            </div>

            {/* Table */}
            <div className="flex-1 overflow-auto p-0">
                <table className="w-full text-left text-xs">
                    <thead className="bg-secondary/50 sticky top-0 z-10">
                        <tr>
                            <th className="px-2 py-2 font-medium w-8"></th>
                            <th className="px-3 py-2 font-medium">Time</th>
                            <th className="px-3 py-2 font-medium">ID</th>
                            <th className="px-3 py-2 font-medium">Old Title</th>
                            <th className="px-3 py-2 font-medium">New Title</th>
                            <th className="px-3 py-2 font-medium">Status</th>
                            <th className="px-3 py-2 font-medium">Result</th>
                        </tr>
                    </thead>
                    <tbody className="divide-y divide-border/50">
                        {filteredHistory.length === 0 ? (
                            <tr>
                                <td colSpan={7} className="px-3 py-8 text-center text-muted-foreground">
                                    {searchTerm || filter !== 'all'
                                        ? 'No entries found with these filters.'
                                        : 'No entries yet.'}
                                </td>
                            </tr>
                        ) : (
                            filteredHistory.map((entry, i) => {
                                const isExpanded = expandedRows.has(i)
                                const hasDetails = (entry.details && entry.details.length > 0) || entry.old_title || entry.new_title
                                const wasRenamed = !!(entry.old_title && entry.new_title)

                                return (
                                    <Fragment key={`entry-${i}`}>
                                        <tr
                                            className={`hover:bg-white/5 transition-colors ${hasDetails ? 'cursor-pointer' : ''}`}
                                            onClick={() => hasDetails && toggleRow(i)}
                                        >
                                            <td className="px-2 py-2 text-center">
                                                {hasDetails && (
                                                    <span className="text-muted-foreground">
                                                        {isExpanded ? '▼' : '▶'}
                                                    </span>
                                                )}
                                            </td>
                                            <td className="px-3 py-2 whitespace-nowrap opacity-70">{entry.timestamp}</td>
                                            <td className="px-3 py-2 font-mono opacity-70">{entry.doc_id}</td>
                                            <td className="px-3 py-2">
                                                <span className={`truncate max-w-[180px] block ${wasRenamed ? 'text-red-400 line-through opacity-70' : 'text-muted-foreground'}`} title={entry.old_title || entry.title}>
                                                    {entry.old_title || entry.title || '-'}
                                                </span>
                                            </td>
                                            <td className="px-3 py-2">
                                                <span className={`truncate max-w-[180px] block ${wasRenamed ? 'text-green-400 font-medium' : 'text-muted-foreground'}`} title={entry.new_title || entry.title}>
                                                    {entry.new_title || (wasRenamed ? '-' : entry.title) || '-'}
                                                </span>
                                            </td>
                                            <td className="px-3 py-2">
                                                <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-medium ${
                                                    entry.action === 'skipped' ? 'bg-yellow-500/20 text-yellow-400' :
                                                    entry.action === 'error' ? 'bg-red-500/20 text-red-400' :
                                                    'bg-green-500/20 text-green-400'
                                                }`}>
                                                    {entry.action === 'skipped' ? '⏭️ Skipped' :
                                                     entry.action === 'error' ? '❌ Error' : '✅ Processed'}
                                                </span>
                                            </td>
                                            <td className="px-3 py-2">
                                                <span className={`font-medium ${
                                                    entry.reason === 'low_quality' ? 'text-orange-400' :
                                                    entry.reason === 'high_quality' ? 'text-green-400' :
                                                    entry.reason === 'no_consensus' ? 'text-purple-400' :
                                                    'text-muted-foreground'
                                                }`}>
                                                    {entry.reason === 'high_quality' ? '✅ High Quality' :
                                                     entry.reason === 'low_quality' ? '📉 Low Quality' :
                                                     entry.reason === 'no_consensus' ? '🤷 No Consensus' :
                                                     entry.reason}
                                                </span>
                                            </td>
                                        </tr>
                                        {isExpanded && hasDetails && (
                                            <tr key={`details-${i}`} className="bg-black/20">
                                                <td colSpan={7} className="px-6 py-3">
                                                    <div className="text-xs space-y-3">
                                                        {wasRenamed && (
                                                            <div className="p-3 bg-blue-500/10 border border-blue-500/20 rounded space-y-2">
                                                                <div className="text-blue-400 font-medium">✏️ Document was renamed</div>
                                                                <div className="grid grid-cols-[auto_1fr] gap-x-3 gap-y-1 text-[11px]">
                                                                    <span className="text-muted-foreground">Old Title:</span>
                                                                    <span className="font-mono text-red-400 line-through">{entry.old_title}</span>
                                                                    <span className="text-muted-foreground">New Title:</span>
                                                                    <span className="font-mono text-green-400">{entry.new_title}</span>
                                                                </div>
                                                            </div>
                                                        )}
                                                        {entry.details && (
                                                            <>
                                                                <div className="font-medium text-muted-foreground">Details:</div>
                                                                <div className="bg-black/30 rounded p-3 font-mono text-[11px] whitespace-pre-wrap">
                                                                    {entry.details.split(';').map((detail, j) => (
                                                                        <div key={j} className="flex items-start gap-2 py-0.5">
                                                                            <span className="text-primary">•</span>
                                                                            <span>{detail.trim()}</span>
                                                                        </div>
                                                                    ))}
                                                                </div>
                                                            </>
                                                        )}
                                                    </div>
                                                </td>
                                            </tr>
                                        )}
                                    </Fragment>
                                )
                            })
                        )}
                    </tbody>
                </table>
            </div>
        </div>
    )
}
