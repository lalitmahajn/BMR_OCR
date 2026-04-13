
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
        <div className="mb-2">
            <button
                onClick={toggle}
                className="w-full flex items-center p-3 hover:bg-white/5 rounded-xl text-left text-sm transition-all duration-300 group relative overflow-hidden backdrop-blur-sm border border-transparent hover:border-white/5"
            >
                {expanded ? <ChevronDown size={16} className="text-white/60" /> : <ChevronRight size={16} className="text-white/40 group-hover:text-white/80 transition-colors" />}
                <FileText size={16} className="mx-2 text-sky-400 group-hover:text-sky-300 group-hover:drop-shadow-[0_0_8px_rgba(56,189,248,0.8)] transition-all" />
                <span className="truncate flex-1 font-medium tracking-wide text-white/90 group-hover:text-white">{doc.filename}</span>
                <span className="text-[10px] font-bold tracking-wider px-2 py-0.5 rounded-full bg-black/40 text-white/60 border border-white/5 shadow-inner">{doc.page_count} PAGES</span>
            </button>

            {/* Smooth height transition wrapper could technically be done with grid but keeping it simple */}
            <div className={cn("overflow-hidden transition-all duration-500 ease-in-out", expanded ? "max-h-[5000px] opacity-100 mt-2" : "max-h-0 opacity-0")}>
                <div className="pl-6 space-y-1 border-l border-white/10 ml-3 py-1">
                    {loading ? (
                        <div className="text-xs text-white/40 p-2 animate-pulse">Loading pages...</div>
                    ) : (
                        pages.map((page) => (
                            <button
                                key={page.id}
                                onClick={() => onSelectPage(page)}
                                className={cn(
                                    "w-full text-left text-xs p-2.5 rounded-xl transition-all duration-300 flex justify-between items-center group relative overflow-hidden",
                                    selectedPageId === page.id 
                                        ? "bg-sky-500/10 text-sky-300 font-semibold shadow-[inset_2px_0_0_0_rgba(56,189,248,1)] border border-sky-500/20" 
                                        : "text-white/50 hover:text-white/90 hover:bg-white/5"
                                )}
                            >
                                {selectedPageId === page.id && <div className="absolute inset-0 bg-gradient-to-r from-sky-500/10 to-transparent pointer-events-none" />}
                                <span className="relative z-10 tracking-wide">Page {page.page_number}</span>
                                {selectedPageId === page.id && <div className="w-1.5 h-1.5 rounded-full bg-sky-400 shadow-[0_0_10px_rgba(56,189,248,1)] relative z-10 animate-pulse"></div>}
                            </button>
                        ))
                    )}
                </div>
            </div>
        </div>
    );
};

export default function DocumentList({ onSelectPage, selectedPageId }) {
    const [documents, setDocuments] = useState([]);

    useEffect(() => {
        getDocuments().then(setDocuments).catch(console.error);
    }, []);

    return (
        <div className="w-[320px] h-full flex flex-col relative glass-panel border-r border-white/5 z-10 shadow-xl bg-black/20">
            <div className="absolute inset-0 bg-[url('https://grainy-gradients.vercel.app/noise.svg')] opacity-[0.02] pointer-events-none mix-blend-overlay"></div>
            <div className="p-6 relative border-b border-white/5 backdrop-blur-md bg-black/10">
                <h1 className="font-extrabold flex items-center gap-3 text-xl tracking-tight">
                    <div className="relative">
                        <div className="absolute inset-0 bg-sky-400 blur-md opacity-50 rounded-full animate-pulse"></div>
                        <img src="/vite.svg" className="w-7 h-7 relative z-10 drop-shadow-md" alt="Logo" />
                    </div>
                    <span className="bg-gradient-to-br from-sky-300 via-sky-100 to-indigo-300 bg-clip-text text-transparent drop-shadow-[0_2px_10px_rgba(56,189,248,0.4)]">BMR Verifier</span>
                </h1>
            </div>
            <div className="flex-1 overflow-y-auto p-4 z-10 custom-scrollbar space-y-1">
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
