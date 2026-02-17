
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
                className="w-full flex items-center p-2 hover:bg-gray-100 rounded text-left text-sm"
            >
                {expanded ? <ChevronDown size={16} /> : <ChevronRight size={16} />}
                <FileText size={16} className="mx-2 text-blue-600" />
                <span className="truncate flex-1 font-medium">{doc.filename}</span>
                <span className="text-xs text-gray-500 bg-gray-200 px-1.5 rounded">{doc.page_count}p</span>
            </button>

            {expanded && (
                <div className="pl-6 space-y-0.5 mt-1 border-l-2 border-gray-100 ml-3">
                    {loading ? (
                        <div className="text-xs text-gray-400 p-2">Loading pages...</div>
                    ) : (
                        pages.map((page) => (
                            <button
                                key={page.id}
                                onClick={() => onSelectPage(page)}
                                className={cn(
                                    "w-full text-left text-xs p-2 rounded hover:bg-gray-50 transition-colors flex justify-between",
                                    selectedPageId === page.id ? "bg-blue-50 text-blue-700 font-medium" : "text-gray-600"
                                )}
                            >
                                <span>Page {page.page_number}</span>
                                {selectedPageId === page.id && <div className="w-1.5 h-1.5 rounded-full bg-blue-500 mt-1"></div>}
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
        <div className="w-64 bg-white border-r h-full flex flex-col">
            <div className="p-4 border-b">
                <h1 className="font-bold text-gray-800 flex items-center gap-2">
                    <img src="/vite.svg" className="w-6 h-6" alt="Logo" />
                    BMR Verifier
                </h1>
            </div>
            <div className="flex-1 overflow-y-auto p-2">
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
