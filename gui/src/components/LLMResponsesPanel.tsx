export function LLMResponsesPanel({ responses }: { responses: Record<string, string> }) {
    if (Object.keys(responses).length === 0) {
        return (
            <div className="border border-green-600 p-4 h-full bg-card rounded-md flex items-center justify-center text-muted-foreground text-sm shadow-sm">
                Waiting for evaluation...
            </div>
        )
    }

    return (
        <div className="border border-green-600 p-4 h-full bg-card rounded-md shadow-sm overflow-hidden flex flex-col">
            <h2 className="text-lg font-bold text-green-600 mb-4 border-b border-border pb-2">LLM Responses</h2>
            <div className="space-y-3 overflow-y-auto flex-1">
                {Object.entries(responses).map(([model, response]) => {
                    const isHigh = response.toLowerCase().includes('high quality')
                    const isLow = response.toLowerCase().includes('low quality')
                    const color = isHigh ? 'text-green-500' : isLow ? 'text-red-500' : 'text-yellow-500'
                    const icon = isHigh ? '+' : isLow ? '-' : '?'

                    return (
                        <div key={model} className="flex flex-col border-b border-border/30 last:border-0 pb-2">
                            <div className="flex items-center gap-2">
                                <span className={`font-bold ${color} w-5 text-center`}>{icon}</span>
                                <span className="font-bold text-sm truncate" title={model}>{model}</span>
                            </div>
                            <div className={`pl-7 text-xs ${color} opacity-90`}>{response || "No response"}</div>
                        </div>
                    )
                })}
            </div>
        </div>
    )
}
