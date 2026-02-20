
import React, { useState } from "react";
import { ZoomIn, ZoomOut, RotateCw } from "lucide-react";

export default function ImageViewer({ imageUrl }) {
    const [scale, setScale] = useState(1);
    const [rotation, setRotation] = useState(0);

    if (!imageUrl) return <div className="flex items-center justify-center h-full bg-gray-100 text-gray-400">No Image Selected</div>;

    return (
        <div className="flex flex-col h-full bg-gray-100 relative overflow-hidden">
            {/* Toolbar */}
            <div className="absolute top-4 right-4 flex gap-2 z-10 bg-white/80 p-1 rounded shadow backdrop-blur">
                <button onClick={() => setScale(s => Math.max(0.5, s - 0.1))} className="p-1 hover:bg-gray-200 rounded">
                    <ZoomOut size={20} />
                </button>
                <span className="px-2 text-sm flex items-center">{Math.round(scale * 100)}%</span>
                <button onClick={() => setScale(s => Math.min(3, s + 0.1))} className="p-1 hover:bg-gray-200 rounded">
                    <ZoomIn size={20} />
                </button>
                <div className="w-px bg-gray-300 mx-1"></div>
                <button onClick={() => setRotation(r => (r + 90) % 360)} className="p-1 hover:bg-gray-200 rounded">
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
