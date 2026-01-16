import { DocumentInfo } from './DocumentList'

export function CurrentDocPanel({ doc }: { doc: DocumentInfo | null }) {
    if (!doc) {
        return (
            <div className="border border-secondary p-4 h-full bg-card rounded-md flex items-center justify-center text-muted-foreground">
                Waiting to start...
            </div>
        )
    }

    const statusColors = {
        pending: "text-muted-foreground",
        processing: "text-yellow-500",
        high_quality: "text-green-500",
        low_quality: "text-red-500",
        no_consensus: "text-orange-500",
        error: "text-purple-500",
        skipped: "text-muted-foreground",
    }

    const color = statusColors[doc.status] || "text-foreground"

    return (
        <div className="border border-secondary p-4 h-full bg-card rounded-md flex flex-col shadow-sm">
            <h2 className="text-lg font-bold text-primary mb-4 border-b border-border pb-2">Current Document</h2>

            <div className="space-y-4 flex-1 overflow-hidden flex flex-col">
                <div>
                    <span className="text-xs uppercase text-muted-foreground font-bold">ID</span>
                    <div className="font-mono">{doc.id}</div>
                </div>

                <div>
                    <span className="text-xs uppercase text-muted-foreground font-bold">Title</span>
                    <div className="font-medium text-lg leading-tight">{doc.title}</div>
                    {doc.new_title && <div className="text-green-500 pt-1">➜ {doc.new_title}</div>}
                </div>

                <div>
                    <span className="text-xs uppercase text-muted-foreground font-bold">Status</span>
                    <div className={`font-bold uppercase ${color}`}>{doc.status.replace('_', ' ')}</div>
                </div>

                <div className="flex-1 min-h-0 flex flex-col">
                    <span className="text-xs uppercase text-muted-foreground font-bold mb-1">Preview</span>
                    <div className="bg-muted/30 p-2 rounded text-sm text-muted-foreground overflow-y-auto flex-1 border border-border/50 font-serif">
                        {doc.content}
                    </div>
                </div>
            </div>
        </div>
    )
}
