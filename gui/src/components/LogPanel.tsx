import { useEffect, useRef } from 'react'

export function LogPanel({ logs }: { logs: string[] }) {
    const endRef = useRef<HTMLDivElement>(null)

    useEffect(() => {
        endRef.current?.scrollIntoView({ behavior: 'smooth' })
    }, [logs])

    return (
        <div className="border border-accent rounded-md flex flex-col bg-black text-green-400 font-mono text-xs p-2 overflow-hidden h-full shadow-inner">
            <div className="overflow-y-auto flex-1 space-y-1">
                {logs.map((log, i) => (
                    <div key={i} className="whitespace-pre-wrap break-words border-b border-gray-900 pb-0.5 mb-0.5 last:border-0">
                        <span className="text-gray-500 mr-2">[{new Date().toLocaleTimeString()}]</span>
                        <span dangerouslySetInnerHTML={{ __html: log }} />
                    </div>
                ))}
                <div ref={endRef} />
            </div>
        </div>
    )
}
