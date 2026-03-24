
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
    <div className={`flex h-screen w-screen overflow-hidden font-sans ${isResizing ? 'cursor-col-resize select-none' : ''}`} style={{ backgroundColor: 'var(--bg-warm)', color: 'var(--text-primary)' }}>
      {/* Sidebar: Document List */}
      <DocumentList
        onSelectPage={setSelectedPage}
        selectedPageId={selectedPage?.id}
      />

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col h-full overflow-hidden">
        {/* Header (Optional) */}
        <div className="px-4 py-2.5 flex justify-between items-center z-10" style={{ backgroundColor: 'var(--bg-surface)', borderBottom: '1px solid var(--border-soft)' }}>
          <h2 className="font-semibold text-lg" style={{ color: 'var(--text-primary)' }}>
            {selectedPage
              ? `Reviewing: Page ${selectedPage.page_number}`
              : "Select a document to begin"}
          </h2>
          <div className="text-sm" style={{ color: 'var(--text-muted)' }}>
            {selectedPage && `${fields.filter(f => f.status === "VERIFIED").length} / ${fields.length} Verified`}
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
            className={`w-1.5 h-full cursor-col-resize hover:bg-blue-500 transition-colors z-30 ${isResizing ? 'bg-blue-600' : 'bg-transparent'}`}
            title="Drag to resize"
          />

          {/* Right: Field Panel */}
          <div
            style={{ width: `${sidebarWidth}px`, backgroundColor: 'var(--bg-surface)', borderLeft: '1px solid var(--border-soft)', boxShadow: '-2px 0 12px rgba(0,0,0,0.04)' }}
            className="flex flex-col z-20"
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
