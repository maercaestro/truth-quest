import { useState } from 'react'
import './App.css'

function App() {
  const [youtubeUrl, setYoutubeUrl] = useState('')
  const [loading, setLoading] = useState(false)
  const [transcription, setTranscription] = useState(null)
  const [facts, setFacts] = useState(null)
  const [verifiedFacts, setVerifiedFacts] = useState(null)
  const [extractingFacts, setExtractingFacts] = useState(false)
  const [verifyingFacts, setVerifyingFacts] = useState(false)
  const [error, setError] = useState(null)

  const handleSubmit = async (e) => {
    e.preventDefault()
    setLoading(true)
    setError(null)
    setTranscription(null)
    setFacts(null)
    setVerifiedFacts(null)

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

  const handleVerifyFacts = async () => {
    if (!facts?.facts) return
    
    setVerifyingFacts(true)
    setError(null)
    
    try {
      const response = await fetch('http://localhost:3001/api/verify-facts', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ facts: facts.facts }),
      })

      const data = await response.json()

      if (!response.ok) {
        throw new Error(data.error || 'Failed to verify facts')
      }

      setVerifiedFacts(data)
    } catch (err) {
      setError(err.message)
    } finally {
      setVerifyingFacts(false)
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
                <div className="flex justify-between items-center mb-4">
                  <h2 className="text-2xl font-bold text-gray-900 dark:text-white">
                    Extracted Facts ({facts.factCount})
                  </h2>
                  {facts.factCount > 0 && !verifiedFacts && (
                    <button
                      onClick={handleVerifyFacts}
                      disabled={verifyingFacts}
                      className="bg-purple-600 hover:bg-purple-700 disabled:bg-gray-400 text-white font-medium py-2 px-4 rounded-lg transition-colors"
                    >
                      {verifyingFacts ? 'Verifying with Brave Search...' : 'Verify Facts'}
                    </button>
                  )}
                </div>
                
                {facts.factCount === 0 ? (
                  <p className="text-gray-600 dark:text-gray-400">No verifiable facts found in this transcript.</p>
                ) : (
                  <>
                    {!verifiedFacts ? (
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
                    ) : null}

                    <div className="mt-4 text-xs text-gray-500 dark:text-gray-400">
                      API Usage: {facts.usage.totalTokens} tokens ({facts.usage.promptTokens} prompt + {facts.usage.completionTokens} completion)
                    </div>
                  </>
                )}
              </div>
            )}

            {verifiedFacts && (
              <div className="bg-white dark:bg-gray-800 rounded-lg shadow-xl p-6">
                <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-4">
                  Verification Results
                </h2>

                {/* Overall Score */}
                <div className="mb-6 p-6 bg-gradient-to-r from-blue-50 to-indigo-50 dark:from-gray-700 dark:to-gray-600 rounded-lg">
                  <div className="text-center">
                    <div className="text-5xl font-bold text-gray-900 dark:text-white mb-2">
                      {verifiedFacts.summary.score}/100
                    </div>
                    <div className="text-lg text-gray-600 dark:text-gray-300">Truth Score</div>
                  </div>
                  <div className="grid grid-cols-3 gap-4 mt-4 text-center">
                    <div>
                      <div className="text-2xl font-bold text-green-600">{verifiedFacts.summary.supported}</div>
                      <div className="text-sm text-gray-600 dark:text-gray-400">Supported</div>
                    </div>
                    <div>
                      <div className="text-2xl font-bold text-yellow-600">{verifiedFacts.summary.partiallyTrue}</div>
                      <div className="text-sm text-gray-600 dark:text-gray-400">Partial</div>
                    </div>
                    <div>
                      <div className="text-2xl font-bold text-red-600">{verifiedFacts.summary.refuted}</div>
                      <div className="text-sm text-gray-600 dark:text-gray-400">Refuted</div>
                    </div>
                  </div>
                </div>

                {/* Verified Facts */}
                <div className="space-y-4">
                  {verifiedFacts.verifiedFacts.map((fact, index) => {
                    const verdict = fact.verification?.verdict || 'inconclusive';
                    const verdictColors = {
                      supported: 'bg-green-100 dark:bg-green-900 text-green-800 dark:text-green-200 border-green-300',
                      refuted: 'bg-red-100 dark:bg-red-900 text-red-800 dark:text-red-200 border-red-300',
                      partially_true: 'bg-yellow-100 dark:bg-yellow-900 text-yellow-800 dark:text-yellow-200 border-yellow-300',
                      inconclusive: 'bg-gray-100 dark:bg-gray-700 text-gray-800 dark:text-gray-200 border-gray-300',
                      unverified: 'bg-gray-100 dark:bg-gray-700 text-gray-800 dark:text-gray-200 border-gray-300',
                      error: 'bg-red-100 dark:bg-red-900 text-red-800 dark:text-red-200 border-red-300'
                    };

                    return (
                      <div key={index} className={`border-2 rounded-lg p-4 ${verdictColors[verdict]}`}>
                        <div className="flex items-start justify-between mb-2">
                          <span className="inline-block bg-blue-100 dark:bg-blue-900 text-blue-800 dark:text-blue-200 text-xs font-semibold px-2 py-1 rounded">
                            {fact.category}
                          </span>
                          <div className="flex gap-2 items-center">
                            <span className="text-xs font-semibold uppercase">
                              {verdict.replace('_', ' ')}
                            </span>
                            <span className="text-xs bg-white dark:bg-gray-800 px-2 py-1 rounded">
                              {fact.verification?.confidence}% confident
                            </span>
                          </div>
                        </div>

                        <p className="text-gray-900 dark:text-white font-medium mb-3">
                          {fact.claim}
                        </p>

                        <div className="bg-white dark:bg-gray-800 rounded p-3 mb-3">
                          <p className="text-sm text-gray-700 dark:text-gray-300">
                            <strong>Analysis:</strong> {fact.verification?.reasoning}
                          </p>
                        </div>

                        {fact.verification?.sources && fact.verification.sources.length > 0 && (
                          <div className="mt-3">
                            <p className="text-sm font-semibold mb-2">Sources:</p>
                            <div className="space-y-2">
                              {fact.verification.sources.map((source, i) => (
                                <a
                                  key={i}
                                  href={source.url}
                                  target="_blank"
                                  rel="noopener noreferrer"
                                  className="block bg-white dark:bg-gray-800 p-2 rounded text-sm hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
                                >
                                  <div className="font-medium text-blue-600 dark:text-blue-400">{source.title}</div>
                                  <div className="text-xs text-gray-600 dark:text-gray-400 truncate">{source.url}</div>
                                </a>
                              ))}
                            </div>
                          </div>
                        )}
                      </div>
                    );
                  })}
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
