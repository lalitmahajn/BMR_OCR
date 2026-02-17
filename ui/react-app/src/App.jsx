
import React, { useState, useEffect } from 'react'
import DocumentList from './components/DocumentList'
import ImageViewer from './components/ImageViewer'
import FieldPanel from './components/FieldPanel'
import { getPageFields, getImageUrl } from './lib/api'

function App() {
  const [selectedPage, setSelectedPage] = useState(null)
  const [fields, setFields] = useState([])
  const [imageUrl, setImageUrl] = useState(null)

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

  const handleFieldUpdate = (updatedField) => {
    setFields(prev =>
      prev.map(f => f.id === updatedField.id ? updatedField : f)
    )
  }

  return (
    <div className="flex h-screen w-screen bg-gray-50 overflow-hidden text-gray-900 font-sans">
      {/* Sidebar: Document List */}
      <DocumentList
        onSelectPage={setSelectedPage}
        selectedPageId={selectedPage?.id}
      />

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col h-full overflow-hidden">
        {/* Header (Optional) */}
        <div className="bg-white border-b px-4 py-2 flex justify-between items-center shadow-sm z-10">
          <h2 className="font-semibold text-lg">
            {selectedPage
              ? `Reviewing: Page ${selectedPage.page_number}`
              : "Select a document to begin"}
          </h2>
          <div className="text-sm text-gray-500">
            {selectedPage && `${fields.filter(f => f.status === "VERIFIED").length} / ${fields.length} Verified`}
          </div>
        </div>

        {/* Workspace: Image + Form */}
        <div className="flex-1 flex overflow-hidden">
          {/* Left: Image Viewer (60%) */}
          <div className="flex-1 bg-gray-200 relative">
            <ImageViewer imageUrl={imageUrl} />
          </div>

          {/* Right: Field Panel (40%) */}
          <div className="w-[400px] border-l bg-white flex flex-col shadow-xl z-20">
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
