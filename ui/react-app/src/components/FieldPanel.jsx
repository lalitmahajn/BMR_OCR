
import React, { useState, useEffect } from "react";
import { updateField } from "../lib/api";
import { Check, X, AlertTriangle } from "lucide-react";
import { cn } from "../lib/utils";

const FieldRow = ({ field, onUpdate }) => {
    const [value, setValue] = useState(field.value || "");
    const [status, setStatus] = useState(field.status);
    const [loading, setLoading] = useState(false);

    useEffect(() => {
        setValue(field.value || "");
        setStatus(field.status);
    }, [field]);

    const handleVerify = async () => {
        setLoading(true);
        try {
            const updated = await updateField(field.id, value);
            setStatus(updated.status);
            onUpdate(updated);
        } catch (e) {
            console.error("Failed to update field", e);
        } finally {
            setLoading(false);
        }
    };

    const getStatusColor = (level, status) => {
        if (status === "VERIFIED") return "bg-emerald-900/20 border-emerald-500/30 shadow-[inset_0_0_15px_rgba(16,185,129,0.1)] hover:border-emerald-500/50 hover:shadow-[0_0_20px_rgba(16,185,129,0.15)]";
        if (level === "RED") return "bg-rose-900/20 border-rose-500/30 shadow-[inset_0_0_15px_rgba(244,63,94,0.1)] hover:border-rose-500/50 hover:shadow-[0_0_20px_rgba(244,63,94,0.15)]";
        if (level === "YELLOW") return "bg-amber-900/20 border-amber-500/30 shadow-[inset_0_0_15px_rgba(245,158,11,0.1)] hover:border-amber-500/50 hover:shadow-[0_0_20px_rgba(245,158,11,0.15)]";
        return "bg-black/20 border-white/10 hover:border-white/20 hover:shadow-[0_0_20px_rgba(255,255,255,0.05)]";
    };

    return (
        <div className={cn("p-5 rounded-2xl border mb-4 transition-all duration-300 relative overflow-hidden group backdrop-blur-sm", getStatusColor(field.confidence_level, status))}>
            <div className="absolute inset-0 bg-gradient-to-br from-white/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-500 pointer-events-none"></div>
            <div className="flex justify-between items-center mb-3 z-10 relative">
                <label className="text-sm font-semibold truncate flex-1 mr-2 tracking-wide text-white/90 drop-shadow-sm" title={field.name}>
                    {field.label || field.name}
                </label>
                <span className={cn(
                    "text-[10px] uppercase tracking-wider px-2.5 py-1 rounded-full font-extrabold transition-all",
                    status === "VERIFIED" ? "bg-emerald-500/20 text-emerald-300 border border-emerald-500/30 shadow-[0_0_10px_rgba(16,185,129,0.2)]" : "bg-black/40 text-white/50 border border-white/5 shadow-inner"
                )}>
                    {status}
                </span>
            </div>

            <div className="flex gap-2.5 z-10 relative mt-1">
                <input
                    type="text"
                    value={value}
                    onChange={(e) => setValue(e.target.value)}
                    className="flex-1 p-3 text-sm rounded-xl outline-none transition-all duration-300 font-medium tracking-wide
                    bg-black/30 border border-white/5 text-white/90 placeholder-white/30 
                    focus:ring-2 focus:ring-sky-500/40 focus:border-sky-400/50 focus:bg-sky-950/20 focus:shadow-[0_0_15px_rgba(56,189,248,0.2)]"
                />
                <button
                    onClick={handleVerify}
                    disabled={loading || (status === "VERIFIED" && value === field.value)}
                    className={cn(
                        "w-11 h-11 flex-shrink-0 rounded-xl text-white transition-all duration-300 flex items-center justify-center",
                        (status === "VERIFIED" && value === field.value) 
                            ? "bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 opacity-50 cursor-not-allowed" 
                            : "bg-gradient-to-br from-sky-500 to-blue-600 hover:scale-105 hover:shadow-[0_0_20px_rgba(56,189,248,0.4)] border border-sky-400/50"
                    )}
                    title="Verify"
                >
                    {loading ? <span className="animate-pulse">...</span> : <Check size={18} strokeWidth={2.5} />}
                </button>
            </div>

            <div className="flex justify-between items-center mt-4 text-[11px] font-bold tracking-wide z-10 relative text-white/40">
                <span className="bg-black/30 px-2 py-0.5 rounded-md border border-white/5">CONFIDENCE: {(field.confidence * 100).toFixed(0)}%</span>
                {field.confidence_level === "RED" && (
                    <span className="flex items-center text-rose-400 drop-shadow-[0_0_5px_rgba(244,63,94,0.5)]">
                        <AlertTriangle size={12} className="mr-1.5" /> LOW CONFIDENCE
                    </span>
                )}
            </div>
        </div>
    );
};

export default function FieldPanel({ fields, onFieldUpdate }) {
    if (!fields) return <div className="p-6 text-white/40 font-semibold uppercase tracking-widest text-sm text-center">No fields loaded.</div>;

    return (
        <div className="h-full flex flex-col pt-2 relative">
            <h2 className="text-xs uppercase tracking-[0.2em] font-extrabold mb-5 px-6 pt-4 pb-4 sticky top-0 z-20 backdrop-blur-xl border-b border-white/5 flex items-center justify-between">
                <span className="bg-clip-text text-transparent bg-gradient-to-r from-white to-white/50">Extracted Data</span>
                <span className="bg-black/40 text-sky-400 px-2.5 py-0.5 rounded-full border border-sky-500/30 shadow-[0_0_10px_rgba(56,189,248,0.1)]">{fields.length}</span>
            </h2>
            <div className="flex-1 overflow-y-auto px-6 pb-6 custom-scrollbar">
                <div className="space-y-1">
                    {fields.map((field) => (
                        <FieldRow key={field.id} field={field} onUpdate={onFieldUpdate} />
                    ))}
                </div>
            </div>
        </div>
    );
}
