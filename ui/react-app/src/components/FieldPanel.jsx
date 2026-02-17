
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
        if (status === "VERIFIED") return "bg-green-100 border-green-500";
        if (level === "RED") return "bg-red-50 border-red-500";
        if (level === "YELLOW") return "bg-yellow-50 border-yellow-500";
        return "bg-gray-50 border-gray-300";
    };

    return (
        <div className={cn("p-3 rounded border mb-2", getStatusColor(field.confidence_level, status))}>
            <div className="flex justify-between items-center mb-1">
                <label className="text-sm font-medium text-gray-700 truncate w-2/3" title={field.name}>
                    {field.name}
                </label>
                <span className={cn(
                    "text-xs px-2 py-0.5 rounded-full",
                    status === "VERIFIED" ? "bg-green-200 text-green-800" : "bg-gray-200 text-gray-800"
                )}>
                    {status}
                </span>
            </div>

            <div className="flex gap-2">
                <input
                    type="text"
                    value={value}
                    onChange={(e) => setValue(e.target.value)}
                    className="flex-1 p-1 text-sm border rounded focus:ring-2 focus:ring-blue-500 outline-none"
                />
                <button
                    onClick={handleVerify}
                    disabled={loading || status === "VERIFIED" && value === field.value}
                    className={cn(
                        "p-1.5 rounded text-white transition-colors",
                        status === "VERIFIED" ? "bg-green-600 hover:bg-green-700" : "bg-blue-600 hover:bg-blue-700"
                    )}
                    title="Verify"
                >
                    {loading ? "..." : <Check size={16} />}
                </button>
            </div>

            <div className="flex justify-between items-center mt-1 text-xs text-gray-500">
                <span>Conf: {(field.confidence * 100).toFixed(0)}%</span>
                {field.confidence_level === "RED" && (
                    <span className="flex items-center text-red-600 font-bold">
                        <AlertTriangle size={12} className="mr-1" /> Low Confidence
                    </span>
                )}
            </div>
        </div>
    );
};

export default function FieldPanel({ fields, onFieldUpdate }) {
    if (!fields) return <div className="p-4 text-gray-500">No fields loaded.</div>;

    return (
        <div className="h-full overflow-y-auto p-4 bg-white border-l">
            <h2 className="text-lg font-bold mb-4 sticky top-0 bg-white pb-2 border-b">
                Extracted Data ({fields.length})
            </h2>
            <div className="space-y-2">
                {fields.map((field) => (
                    <FieldRow key={field.id} field={field} onUpdate={onFieldUpdate} />
                ))}
            </div>
        </div>
    );
}
