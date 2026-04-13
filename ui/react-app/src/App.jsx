
import React, { useState, useEffect } from 'react'
import DocumentList from './components/DocumentList'
import ImageViewer from './components/ImageViewer'
import FieldPanel from './components/FieldPanel'
import { getPageFields, getImageUrl } from './lib/api'

function App() {
  const [selectedPage, setSelectedPage] = useState(null)
  const [fields, setFields] = useState([])
  const [imageUrl, setImageUrl] = useState(null)
  const [sidebarWidth, setSidebarWidth] = useState(450)
  const [isResizing, setIsResizing] = useState(false)

  // Load fields when a page is selected
  useEffect(() => {
    if (selectedPage) {
      setImageUrl(getImageUrl(selectedPage.id))
      getPageFields(selectedPage.id)
        .then(setFields)
        .catch(console.error)
    } else {
      setFields([])
      setImageUrl(null)
    }
  }, [selectedPage])

  const handleMouseDown = (e) => {
    e.preventDefault()
    setIsResizing(true)
  }

  useEffect(() => {
    const handleMouseMove = (e) => {
      if (!isResizing) return
      const newWidth = window.innerWidth - e.clientX
      if (newWidth > 300 && newWidth < 800) {
        setSidebarWidth(newWidth)
      }
    }

    const handleMouseUp = () => {
      setIsResizing(false)
    }

    if (isResizing) {
      window.addEventListener('mousemove', handleMouseMove)
      window.addEventListener('mouseup', handleMouseUp)
    }

    return () => {
      window.removeEventListener('mousemove', handleMouseMove)
      window.removeEventListener('mouseup', handleMouseUp)
    }
  }, [isResizing])

  const handleFieldUpdate = (updatedField) => {
    setFields(prev =>
      prev.map(f => f.id === updatedField.id ? updatedField : f)
    )
  }

  return (
    <div className={`flex h-screen w-screen overflow-hidden font-sans ${isResizing ? 'cursor-col-resize select-none' : ''}`}>
      {/* Sidebar: Document List */}
      <DocumentList
        onSelectPage={setSelectedPage}
        selectedPageId={selectedPage?.id}
      />

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col h-full overflow-hidden relative z-0">
        {/* Header (Optional) */}
        <div className="px-6 py-3.5 flex justify-between items-center z-20 glass-panel shadow-sm border-b border-white/5">
          <h2 className="font-semibold text-lg tracking-wide bg-clip-text text-transparent bg-gradient-to-r from-blue-300 to-indigo-300 drop-shadow-sm">
            {selectedPage
              ? `Reviewing: Page ${selectedPage.page_number}`
              : "Select a document to begin"}
          </h2>
          <div className="text-sm font-medium px-3 py-1 rounded-full bg-slate-800/60 border border-white/10 shadow-inner" style={{ color: 'var(--text-muted)' }}>
            <span className="text-emerald-400 mr-1">{selectedPage ? fields.filter(f => f.status === "VERIFIED").length : 0}</span> 
            / {selectedPage ? fields.length : 0} Verified
          </div>
        </div>

        {/* Workspace: Image + Form */}
        <div className="flex-1 flex overflow-hidden relative">
          {/* Left: Image Viewer */}
          <div className="flex-1 relative" style={{ backgroundColor: 'var(--bg-viewer)' }}>
            <ImageViewer imageUrl={imageUrl} />
          </div>

          {/* Draggable Handle */}
          <div
            onMouseDown={handleMouseDown}
            className={`w-1.5 h-full cursor-col-resize z-30 transition-all duration-300 flex justify-center items-center group ${isResizing ? 'bg-blue-500 shadow-[0_0_15px_rgba(59,130,246,0.6)]' : 'bg-transparent hover:bg-blue-500/50 hover:shadow-[0_0_10px_rgba(59,130,246,0.3)]'}`}
            title="Drag to resize"
          >
             <div className="h-12 w-[2px] bg-white/20 rounded-full group-hover:bg-white/60 transition-colors" />
          </div>

          {/* Right: Field Panel */}
          <div
            style={{ width: `${sidebarWidth}px` }}
            className="flex flex-col z-20 glass-panel border-l border-white/5 shadow-[-10px_0_30px_rgba(0,0,0,0.5)] bg-slate-900/40"
          >
            <FieldPanel
              fields={fields}
              onFieldUpdate={handleFieldUpdate}
            />
          </div>
        </div>
      </div>
    </div>
  )
}

export default App
