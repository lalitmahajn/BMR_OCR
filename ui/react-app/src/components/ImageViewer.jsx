
import React, { useState } from "react";
import { ZoomIn, ZoomOut, RotateCw } from "lucide-react";

export default function ImageViewer({ imageUrl }) {
    const [scale, setScale] = useState(1);
    const [rotation, setRotation] = useState(0);

    if (!imageUrl) return <div className="flex items-center justify-center h-full text-white/40 tracking-widest uppercase font-semibold text-sm">No Image Selected</div>;

    return (
        <div className="flex flex-col h-full relative overflow-hidden bg-gradient-to-br from-black/80 to-black">
            {/* Toolbar */}
            <div className="absolute xl:top-6 xl:right-6 top-4 right-4 flex gap-1 z-10 p-2 rounded-2xl glass-panel shadow-[0_8px_32px_rgba(0,0,0,0.5)] border border-white/10">
                <button onClick={() => setScale(s => Math.max(0.5, s - 0.1))} className="p-2 hover:bg-white/10 rounded-xl transition-all duration-200 hover:scale-110 active:scale-95 text-white/70 hover:text-white">
                    <ZoomOut size={20} />
                </button>
                <div className="px-3 text-sm flex items-center font-bold font-mono text-sky-200 bg-black/20 rounded-lg shadow-inner border border-black/50 mx-1">{Math.round(scale * 100)}%</div>
                <button onClick={() => setScale(s => Math.min(3, s + 0.1))} className="p-2 hover:bg-white/10 rounded-xl transition-all duration-200 hover:scale-110 active:scale-95 text-white/70 hover:text-white">
                    <ZoomIn size={20} />
                </button>
                <div className="w-px mx-1 bg-white/10 my-1"></div>
                <button onClick={() => setRotation(r => (r + 90) % 360)} className="p-2 hover:bg-white/10 rounded-xl transition-all duration-200 hover:scale-110 active:scale-95 text-white/70 hover:text-white">
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
