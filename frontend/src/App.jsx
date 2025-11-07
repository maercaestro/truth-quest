import { useState } from 'react'
import './App.css'

function App() {
  const [youtubeUrl, setYoutubeUrl] = useState('')
  const [loading, setLoading] = useState(false)
  const [transcription, setTranscription] = useState(null)
  const [facts, setFacts] = useState(null)
  const [extractingFacts, setExtractingFacts] = useState(false)
  const [error, setError] = useState(null)

  const handleSubmit = async (e) => {
    e.preventDefault()
    setLoading(true)
    setError(null)
    setTranscription(null)
    setFacts(null)

    try {
      const response = await fetch('http://localhost:3001/api/transcription', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ youtubeUrl }),
      })

      const data = await response.json()

      if (!response.ok) {
        throw new Error(data.error || 'Failed to fetch transcription')
      }

      setTranscription(data.transcript)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  const handleExtractFacts = async () => {
    if (!transcription?.full) return
    
    setExtractingFacts(true)
    setError(null)
    
    try {
      const response = await fetch('http://localhost:3001/api/extract-facts', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ transcript: transcription.full }),
      })

      const data = await response.json()

      if (!response.ok) {
        throw new Error(data.error || 'Failed to extract facts')
      }

      setFacts(data)
    } catch (err) {
      setError(err.message)
    } finally {
      setExtractingFacts(false)
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 dark:from-gray-900 dark:to-gray-800 py-12 px-4">
      <div className="max-w-4xl mx-auto">
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold text-gray-900 dark:text-white mb-2">
            Truth Quest
          </h1>
          <p className="text-lg text-gray-600 dark:text-gray-300">
            YouTube Transcription Fact Checker
          </p>
        </div>

        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-xl p-6 mb-6">
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label 
                htmlFor="youtube-url" 
                className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2"
              >
                YouTube URL
              </label>
              <input
                id="youtube-url"
                type="text"
                value={youtubeUrl}
                onChange={(e) => setYoutubeUrl(e.target.value)}
                placeholder="https://www.youtube.com/watch?v=..."
                className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent dark:bg-gray-700 dark:text-white"
                required
              />
            </div>
            <button
              type="submit"
              disabled={loading}
              className="w-full bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 text-white font-medium py-2 px-4 rounded-lg transition-colors"
            >
              {loading ? 'Fetching Transcription...' : 'Get Transcription'}
            </button>
          </form>
        </div>

        {error && (
          <div className="bg-red-50 dark:bg-red-900/30 border border-red-200 dark:border-red-800 rounded-lg p-4 mb-6">
            <p className="text-red-800 dark:text-red-200">
              <strong>Error:</strong> {error}
            </p>
          </div>
        )}

        {transcription && (
          <div className="space-y-6">
            <div className="bg-white dark:bg-gray-800 rounded-lg shadow-xl p-6">
              <div className="flex justify-between items-center mb-4">
                <h2 className="text-2xl font-bold text-gray-900 dark:text-white">
                  Transcription
                </h2>
                <button
                  onClick={handleExtractFacts}
                  disabled={extractingFacts}
                  className="bg-green-600 hover:bg-green-700 disabled:bg-gray-400 text-white font-medium py-2 px-4 rounded-lg transition-colors"
                >
                  {extractingFacts ? 'Extracting Facts...' : 'Extract Facts with AI'}
                </button>
              </div>
              <div className="bg-gray-50 dark:bg-gray-700 rounded-lg p-4 max-h-96 overflow-y-auto">
                <p className="text-gray-800 dark:text-gray-200 whitespace-pre-wrap">
                  {transcription.full}
                </p>
              </div>
              <div className="mt-4 text-sm text-gray-600 dark:text-gray-400">
                Total segments: {transcription.segments.length}
              </div>
            </div>

            {facts && (
              <div className="bg-white dark:bg-gray-800 rounded-lg shadow-xl p-6">
                <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-4">
                  Extracted Facts ({facts.factCount})
                </h2>
                
                {facts.factCount === 0 ? (
                  <p className="text-gray-600 dark:text-gray-400">No verifiable facts found in this transcript.</p>
                ) : (
                  <div className="space-y-4">
                    {facts.facts.map((fact, index) => (
                      <div key={index} className="border border-gray-200 dark:border-gray-700 rounded-lg p-4">
                        <div className="flex items-start justify-between mb-2">
                          <span className="inline-block bg-blue-100 dark:bg-blue-900 text-blue-800 dark:text-blue-200 text-xs font-semibold px-2 py-1 rounded">
                            {fact.category}
                          </span>
                          {fact.verifiable && (
                            <span className="inline-block bg-green-100 dark:bg-green-900 text-green-800 dark:text-green-200 text-xs font-semibold px-2 py-1 rounded">
                              Verifiable
                            </span>
                          )}
                        </div>
                        <p className="text-gray-900 dark:text-white font-medium mb-2">
                          {fact.claim}
                        </p>
                        {fact.context && (
                          <p className="text-sm text-gray-600 dark:text-gray-400 mb-2 italic">
                            Context: "{fact.context}"
                          </p>
                        )}
                        {fact.entities && fact.entities.length > 0 && (
                          <div className="flex flex-wrap gap-1 mt-2">
                            {fact.entities.map((entity, i) => (
                              <span key={i} className="bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 text-xs px-2 py-1 rounded">
                                {entity}
                              </span>
                            ))}
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                )}

                <div className="mt-4 text-xs text-gray-500 dark:text-gray-400">
                  API Usage: {facts.usage.totalTokens} tokens ({facts.usage.promptTokens} prompt + {facts.usage.completionTokens} completion)
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  )
}

export default App
