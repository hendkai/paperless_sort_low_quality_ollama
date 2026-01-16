import { Loader2, Play, Pause, Power, RotateCw } from 'lucide-react'

export function Controls({
    maxDocs,
    setMaxDocs,
    onLoad,
    onStart,
    onPause,
    onQuit,
    processing,
    paused,
    loading
}: any) {
    return (
        <div className="flex items-center justify-center gap-4 p-4 border-t border-border bg-muted/20 backdrop-blur">
            {/* Limit control hidden for streaming mode
            <div className="flex items-center gap-2 border border-primary/50 bg-card rounded p-1 mr-4 shadow-sm">
                ... (hidden)
            </div>
            */}

            {/* Load button hidden for one-click start
            <button
                onClick={onLoad}
                disabled={processing || loading}
                className="px-6 py-2 bg-blue-600 hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed text-white rounded shadow-md flex items-center gap-2 font-bold transition-all active:scale-95"
            >
                {loading ? <Loader2 className="animate-spin w-4 h-4" /> : <RotateCw className="w-4 h-4" />}
                Laden
            </button>
            */}

            <button
                onClick={onStart}
                disabled={processing || loading}
                className="px-6 py-2 bg-green-600 hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed text-white rounded shadow-md flex items-center gap-2 font-bold transition-all active:scale-95"
            >
                <Play className="w-4 h-4" />
                Start
            </button>

            <button
                onClick={onPause}
                disabled={!processing}
                className="px-6 py-2 bg-yellow-600 hover:bg-yellow-700 disabled:opacity-50 disabled:cursor-not-allowed text-white rounded shadow-md flex items-center gap-2 min-w-[140px] justify-center font-bold transition-all active:scale-95"
            >
                {paused ? <Play className="w-4 h-4" /> : <Pause className="w-4 h-4" />}
                {paused ? "Resume" : "Pause"}
            </button>

            <button
                onClick={onQuit}
                className="px-6 py-2 bg-destructive hover:bg-destructive/90 text-destructive-foreground rounded shadow-md flex items-center gap-2 font-bold transition-all active:scale-95 ml-4"
            >
                <Power className="w-4 h-4" />
                Stop
            </button>
        </div>
    )
}
