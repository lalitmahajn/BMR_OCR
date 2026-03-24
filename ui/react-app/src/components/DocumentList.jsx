
import React, { useState, useEffect } from "react";
import { getDocuments, getPages } from "../lib/api";
import { FileText, ChevronRight, ChevronDown } from "lucide-react";
import { cn } from "../lib/utils";

const DocumentItem = ({ doc, onSelectPage, selectedPageId }) => {
    const [expanded, setExpanded] = useState(false);
    const [pages, setPages] = useState([]);
    const [loading, setLoading] = useState(false);

    const toggle = async () => {
        if (!expanded && pages.length === 0) {
            setLoading(true);
            try {
                const data = await getPages(doc.id);
                setPages(data);
            } catch (err) {
                console.error("Failed to load pages", err);
            } finally {
                setLoading(false);
            }
        }
        setExpanded(!expanded);
    };

    return (
        <div className="mb-1">
            <button
                onClick={toggle}
                className="w-full flex items-center p-2.5 hover:bg-slate-700/60 rounded-xl text-left text-sm transition-all duration-200 group relative overflow-hidden"
            >
                {expanded ? <ChevronDown size={16} /> : <ChevronRight size={16} />}
                <FileText size={16} className="mx-2 text-blue-400 group-hover:text-blue-300 transition-colors" />
                <span className="truncate flex-1 font-medium">{doc.filename}</span>
                <span className="text-[10px] font-semibold tracking-wide px-2 py-0.5 rounded-full" style={{ backgroundColor: 'var(--border-soft)', color: 'var(--text-primary)' }}>{doc.page_count} PAGES</span>
            </button>

            {expanded && (
                <div className="pl-6 space-y-1 mt-2 border-l-2 ml-3" style={{ borderColor: 'var(--border-soft)' }}>
                    {loading ? (
                        <div className="text-xs text-slate-400 p-2">Loading pages...</div>
                    ) : (
                        pages.map((page) => (
                            <button
                                key={page.id}
                                onClick={() => onSelectPage(page)}
                                className={cn(
                                    "w-full text-left text-xs p-2.5 rounded-xl hover:bg-slate-700/60 transition-all duration-200 flex justify-between items-center group",
                                    selectedPageId === page.id ? "bg-gradient-to-r from-blue-900/40 to-slate-800/0 text-blue-300 font-semibold shadow-[inset_2px_0_0_0_rgba(96,165,250,1)] bg-slate-800/50" : "text-slate-400"
                                )}
                            >
                                <span>Page {page.page_number}</span>
                                {selectedPageId === page.id && <div className="w-1.5 h-1.5 rounded-full bg-blue-400 shadow-[0_0_8px_rgba(96,165,250,0.8)]"></div>}
                            </button>
                        ))
                    )}
                </div>
            )}
        </div>
    );
};

export default function DocumentList({ onSelectPage, selectedPageId }) {
    const [documents, setDocuments] = useState([]);

    useEffect(() => {
        getDocuments().then(setDocuments).catch(console.error);
    }, []);

    return (
        <div className="w-72 h-full flex flex-col relative" style={{ background: 'linear-gradient(180deg, var(--bg-sidebar) 0%, var(--bg-warm) 100%)', borderRight: '1px solid var(--border-soft)' }}>
            <div className="absolute inset-0 bg-[url('https://grainy-gradients.vercel.app/noise.svg')] opacity-[0.03] pointer-events-none mix-blend-overlay"></div>
            <div className="p-4" style={{ borderBottom: '1px solid var(--border-soft)' }}>
                <h1 className="font-bold flex items-center gap-2.5 text-lg" style={{ color: 'var(--text-primary)' }}>
                    <img src="/vite.svg" className="w-6 h-6" alt="Logo" />
                    <span className="bg-gradient-to-r from-blue-400 to-indigo-400 bg-clip-text text-transparent drop-shadow-sm font-extrabold tracking-tight">BMR Verifier</span>
                </h1>
            </div>
            <div className="flex-1 overflow-y-auto p-3 z-10 custom-scrollbar">
                {documents.map((doc) => (
                    <DocumentItem
                        key={doc.id}
                        doc={doc}
                        onSelectPage={onSelectPage}
                        selectedPageId={selectedPageId}
                    />
                ))}
            </div>
        </div>
    );
}
