
import React, { useState } from "react";
import { ZoomIn, ZoomOut, RotateCw } from "lucide-react";

export default function ImageViewer({ imageUrl }) {
    const [scale, setScale] = useState(1);
    const [rotation, setRotation] = useState(0);

    if (!imageUrl) return <div className="flex items-center justify-center h-full" style={{ backgroundColor: 'var(--bg-viewer)', color: 'var(--text-muted)' }}>No Image Selected</div>;

    return (
        <div className="flex flex-col h-full relative overflow-hidden" style={{ backgroundColor: 'var(--bg-viewer)' }}>
            {/* Toolbar */}
            <div className="absolute top-4 right-4 flex gap-2 z-10 p-1.5 rounded-lg shadow-lg backdrop-blur-md" style={{ backgroundColor: 'var(--bg-surface)', border: '1px solid var(--border-soft)', color: 'var(--text-primary)' }}>
                <button onClick={() => setScale(s => Math.max(0.5, s - 0.1))} className="p-1.5 hover:bg-slate-700/50 rounded-md transition-colors">
                    <ZoomOut size={20} />
                </button>
                <span className="px-2 text-sm flex items-center font-medium" style={{ color: 'var(--text-primary)' }}>{Math.round(scale * 100)}%</span>
                <button onClick={() => setScale(s => Math.min(3, s + 0.1))} className="p-1.5 hover:bg-slate-700/50 rounded-md transition-colors">
                    <ZoomIn size={20} />
                </button>
                <div className="w-px mx-0.5" style={{ backgroundColor: 'var(--border-soft)' }}></div>
                <button onClick={() => setRotation(r => (r + 90) % 360)} className="p-1.5 hover:bg-slate-700/50 rounded-md transition-colors">
                    <RotateCw size={20} />
                </button>
            </div>

            {/* Image Container with Scrolling */}
            <div className="flex-1 overflow-auto flex items-center justify-center p-8">
                <div
                    style={{
                        transform: `scale(${scale}) rotate(${rotation}deg)`,
                        transition: 'transform 0.2s',
                        transformOrigin: 'center center'
                    }}
                    className="shadow-2xl"
                >
                    <img
                        src={imageUrl}
                        alt="Document Page"
                        className="max-w-full max-h-[85vh] object-contain"
                    />
                </div>
            </div>
        </div>
    );
}
