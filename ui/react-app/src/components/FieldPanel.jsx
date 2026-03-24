
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
        if (status === "VERIFIED") return "bg-gradient-to-br from-slate-800 to-slate-800/80 border-slate-700/60 shadow-[inset_3px_0_0_0_rgba(16,185,129,0.8)] hover:border-slate-600";
        if (level === "RED") return "bg-gradient-to-br from-slate-800 to-slate-800/80 border-slate-700/60 shadow-[inset_3px_0_0_0_rgba(244,63,94,0.8)] hover:border-slate-600";
        if (level === "YELLOW") return "bg-gradient-to-br from-slate-800 to-slate-800/80 border-slate-700/60 shadow-[inset_3px_0_0_0_rgba(245,158,11,0.8)] hover:border-slate-600";
        return "bg-gradient-to-br from-slate-800 to-slate-800/80 border-slate-700/60 shadow-[inset_3px_0_0_0_rgba(100,116,139,0.8)] hover:border-slate-600";
    };

    return (
        <div className={cn("p-4 rounded-xl border mb-3 transition-all duration-300 hover:shadow-lg relative overflow-hidden group", getStatusColor(field.confidence_level, status))}>
            <div className="absolute inset-0 bg-white/5 opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none"></div>
            <div className="flex justify-between items-center mb-2 z-10 relative">
                <label className="text-sm font-semibold truncate flex-1 mr-2" style={{ color: 'var(--text-primary)' }} title={field.name}>
                    {field.name}
                </label>
                <span className={cn(
                    "text-[10px] uppercase tracking-wider px-2.5 py-1 rounded-md font-bold transition-colors",
                    status === "VERIFIED" ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20" : "bg-slate-700/50 text-slate-300 border border-slate-600/50"
                )}>
                    {status}
                </span>
            </div>

            <div className="flex gap-2.5 z-10 relative">
                <input
                    type="text"
                    value={value}
                    onChange={(e) => setValue(e.target.value)}
                    className="flex-1 p-2 text-sm border border-slate-700/50 rounded-lg focus:ring-2 focus:ring-blue-500/50 focus:border-blue-500 focus:bg-slate-900 outline-none transition-all bg-slate-900/60 text-slate-100 placeholder-slate-500 shadow-inner"
                />
                <button
                    onClick={handleVerify}
                    disabled={loading || status === "VERIFIED" && value === field.value}
                    className={cn(
                        "p-2 rounded-lg text-white transition-all duration-200 flex items-center justify-center",
                        status === "VERIFIED" ? "bg-emerald-500/20 text-emerald-400 hover:bg-emerald-500/30 border border-emerald-500/30" : "bg-blue-600 hover:bg-blue-500 hover:shadow-[0_0_15px_rgba(59,130,246,0.3)] border border-blue-500"
                    )}
                    title="Verify"
                >
                    {loading ? "..." : <Check size={16} />}
                </button>
            </div>

            <div className="flex justify-between items-center mt-3 text-xs z-10 relative" style={{ color: 'var(--text-muted)' }}>
                <span>Conf: {(field.confidence * 100).toFixed(0)}%</span>
                {field.confidence_level === "RED" && (
                    <span className="flex items-center text-rose-400 font-semibold">
                        <AlertTriangle size={12} className="mr-1" /> Low Confidence
                    </span>
                )}
            </div>
        </div>
    );
};

export default function FieldPanel({ fields, onFieldUpdate }) {
    if (!fields) return <div className="p-4" style={{ color: 'var(--text-muted)' }}>No fields loaded.</div>;

    return (
        <div className="h-full overflow-y-auto p-4" style={{ backgroundColor: 'var(--bg-panel)' }}>
            <h2 className="text-sm uppercase tracking-widest font-bold mb-4 sticky top-0 pb-3 pt-1 z-10 backdrop-blur-md" style={{ color: 'var(--text-muted)', backgroundColor: 'var(--bg-panel)', borderBottom: '1px solid var(--border-soft)' }}>
                Extracted Data <span className="text-slate-500 ml-1">({fields.length})</span>
            </h2>
            <div className="space-y-2">
                {fields.map((field) => (
                    <FieldRow key={field.id} field={field} onUpdate={onFieldUpdate} />
                ))}
            </div>
        </div>
    );
}
