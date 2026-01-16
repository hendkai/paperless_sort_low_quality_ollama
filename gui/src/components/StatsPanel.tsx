

export interface ProcessingStats {
    total: number
    processed: number
    high_quality: number
    low_quality: number
    no_consensus: number
    errors: number
    skipped: number
}

export interface SystemStats {
    cpu: number
    ram: number
    ram_txt: string
    gpu: number
    vram: number
    vram_txt: string
}

export function StatsPanel({ stats, sysStats }: { stats: ProcessingStats, sysStats?: SystemStats }) {
    const percent = stats.total > 0 ? ((stats.processed / stats.total) * 100).toFixed(1) : '0.0'
    return (
        <div className="flex flex-col gap-2 h-full">
            <div className="border border-primary p-4 bg-card rounded-md shadow-sm h-1/2 overflow-y-auto">
                <h2 className="text-lg font-bold text-primary mb-2 border-b border-border pb-1">Statistics</h2>
                <div className="space-y-1 text-xs">
                    <div className="flex justify-between"><span>Total:</span> <span className="font-mono">{stats.total}</span></div>
                    <div className="flex justify-between"><span>Processed:</span> <span className="font-mono">{stats.processed} ({percent}%)</span></div>
                    <div className="flex justify-between text-green-500"><span>High Quality:</span> <span className="font-mono">{stats.high_quality}</span></div>
                    <div className="flex justify-between text-red-500"><span>Low Quality:</span> <span className="font-mono">{stats.low_quality}</span></div>
                    <div className="flex justify-between text-yellow-500"><span>No Consensus:</span> <span className="font-mono">{stats.no_consensus}</span></div>
                    <div className="flex justify-between text-purple-500"><span>Errors:</span> <span className="font-mono">{stats.errors}</span></div>
                    <div className="flex justify-between text-gray-500"><span>Skipped:</span> <span className="font-mono">{stats.skipped}</span></div>
                </div>
            </div>

            {sysStats && (
                <div className="border border-secondary p-4 bg-card/50 rounded-md shadow-sm h-1/2">
                    <h2 className="text-lg font-bold text-secondary mb-2 border-b border-border pb-1">System</h2>
                    <div className="space-y-2 text-xs">
                        <div>
                            <div className="flex justify-between mb-1"><span>CPU</span> <span className="font-mono">{sysStats.cpu}%</span></div>
                            <div className="w-full bg-secondary/20 rounded-full h-1.5"><div className="bg-secondary h-1.5 rounded-full" style={{ width: `${sysStats.cpu}%` }}></div></div>
                        </div>
                        <div>
                            <div className="flex justify-between mb-1"><span>RAM</span> <span className="font-mono">{sysStats.ram}% ({sysStats.ram_txt})</span></div>
                            <div className="w-full bg-secondary/20 rounded-full h-1.5"><div className="bg-secondary h-1.5 rounded-full" style={{ width: `${sysStats.ram}%` }}></div></div>
                        </div>
                        <div>
                            <div className="flex justify-between mb-1"><span>GPU</span> <span className="font-mono">{sysStats.gpu}%</span></div>
                            <div className="w-full bg-primary/20 rounded-full h-1.5"><div className="bg-primary h-1.5 rounded-full" style={{ width: `${sysStats.gpu}%` }}></div></div>
                        </div>
                        <div>
                            <div className="flex justify-between mb-1"><span>VRAM</span> <span className="font-mono">{sysStats.vram}% ({sysStats.vram_txt})</span></div>
                            <div className="w-full bg-primary/20 rounded-full h-1.5"><div className="bg-primary h-1.5 rounded-full" style={{ width: `${sysStats.vram}%` }}></div></div>
                        </div>
                    </div>
                </div>
            )}
        </div>
    )
}
