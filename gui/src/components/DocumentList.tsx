import clsx from 'clsx'

export interface DocumentInfo {
    id: number
    title: string
    content: string
    status: 'pending' | 'processing' | 'high_quality' | 'low_quality' | 'no_consensus' | 'error' | 'skipped'
    new_title?: string
}

export function DocumentList({ documents }: { documents: DocumentInfo[] }) {
    return (
        <div className="border border-border rounded-md h-full overflow-hidden flex flex-col bg-card">
            <div className="bg-muted p-2 font-bold text-xs uppercase tracking-wider border-b border-border">Documents ({documents.length})</div>
            <div className="overflow-y-auto flex-1">
                <table className="w-full text-left text-sm">
                    <thead className="bg-secondary text-secondary-foreground sticky top-0 z-10">
                        <tr>
                            <th className="p-2 w-16">ID</th>
                            <th className="p-2">Title</th>
                            <th className="p-2 w-32">Status</th>
                        </tr>
                    </thead>
                    <tbody>
                        {documents.length === 0 && (
                            <tr>
                                <td colSpan={3} className="p-4 text-center text-muted-foreground">No documents loaded.</td>
                            </tr>
                        )}
                        {documents.map(doc => (
                            <tr key={doc.id} className="border-b border-border/50 hover:bg-muted/50 transition-colors">
                                <td className="p-2 font-mono text-xs text-muted-foreground">{doc.id}</td>
                                <td className="p-2">
                                    <div className="font-medium truncate max-w-[300px]" title={doc.title}>{doc.title}</div>
                                    {doc.new_title && <div className="text-green-500 text-xs truncate max-w-[300px]">➜ {doc.new_title}</div>}
                                </td>
                                <td className={clsx("p-2 text-xs font-bold uppercase", {
                                    'text-yellow-500': doc.status === 'processing',
                                    'text-green-500': doc.status === 'high_quality',
                                    'text-red-500': doc.status === 'low_quality',
                                    'text-purple-500': doc.status === 'error',
                                    'text-orange-400': doc.status === 'no_consensus',
                                    'text-muted-foreground': doc.status === 'pending' || doc.status === 'skipped'
                                })}>{doc.status.replace('_', ' ')}</td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>
        </div>
    )
}
