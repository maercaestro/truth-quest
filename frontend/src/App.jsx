import { useState } from 'react'
import './App.css'

function App() {
  const [youtubeUrl, setYoutubeUrl] = useState('')
  const [analyzing, setAnalyzing] = useState(false)
  const [progress, setProgress] = useState(0)
  const [progressMessage, setProgressMessage] = useState('')
  const [result, setResult] = useState(null)
  const [error, setError] = useState(null)

  const handleAnalyze = async (e) => {
    e.preventDefault()
    setAnalyzing(true)
    setProgress(0)
    setProgressMessage('Starting analysis...')
    setError(null)
    setResult(null)

    try {
      // Simulate progress updates
      setProgress(10)
      setProgressMessage('Fetching transcript...')
      
      // Start the actual API call
      const startTime = Date.now()
      const progressInterval = setInterval(() => {
        const elapsed = Date.now() - startTime
        // Gradually increase progress up to 90% over 60 seconds
        const estimatedProgress = Math.min(90, 10 + (elapsed / 60000) * 80)
        setProgress(Math.floor(estimatedProgress))
        
        if (estimatedProgress < 30) {
          setProgressMessage('Fetching transcript...')
        } else if (estimatedProgress < 60) {
          setProgressMessage('Extracting facts...')
        } else {
          setProgressMessage('Verifying facts...')
        }
      }, 500)

      const response = await fetch('http://localhost:3001/api/analyze', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ youtubeUrl }),
      })

      clearInterval(progressInterval)
      setProgress(100)
      setProgressMessage('Analysis complete!')

      const data = await response.json()

      if (!response.ok) {
        throw new Error(data.error || 'Failed to analyze video')
      }

      setResult(data)
    } catch (err) {
      setError(err.message)
    } finally {
      setAnalyzing(false)
      setProgress(0)
    }
  }

  const getGradeColorClass = (color) => {
    const colors = {
      green: 'from-[#28A745] to-[#20803a]',
      blue: 'from-[#00ADB5] to-[#008891]',
      orange: 'from-[#FFC107] to-[#e6ad06]',
      red: 'from-[#DC3545] to-[#c82333]',
      gray: 'from-gray-500 to-slate-600'
    }
    return colors[color] || colors.gray
  }

  const getVerdictColor = (verdict) => {
    const colors = {
      supported: 'text-[#28A745] bg-green-50 border-green-200',
      refuted: 'text-[#DC3545] bg-red-50 border-red-200',
      partially_true: 'text-[#FFC107] bg-yellow-50 border-yellow-200',
      error: 'text-gray-600 bg-gray-50 border-gray-200'
    }
    return colors[verdict] || colors.error
  }

  return (
    <div className="min-h-screen bg-gray-100">
      {/* Header */}
      <div className="bg-[#2C3E50] text-white py-6 px-4 shadow-lg">
        <div className="max-w-7xl mx-auto">
          <div className="flex items-center justify-center gap-4">
            <img src="/logotruth.png" alt="Truth Quest Logo" className="h-16 w-16" />
            <div>
              <h1 className="text-4xl font-bold">Truth Quest</h1>
              <p className="text-[#00ADB5] text-lg">AI-Powered YouTube Fact Checker</p>
            </div>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="max-w-7xl mx-auto px-4 py-8">
        <div className="bg-white rounded-lg shadow-xl p-8 mb-6">
          <form onSubmit={handleAnalyze} className="space-y-4">
            <div>
              <label htmlFor="youtube-url" className="block text-sm font-medium text-[#4B5563] mb-2">
                YouTube URL
              </label>
              <input
                id="youtube-url"
                type="text"
                value={youtubeUrl}
                onChange={(e) => setYoutubeUrl(e.target.value)}
                placeholder="https://www.youtube.com/watch?v=..."
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-[#00ADB5] focus:border-[#00ADB5] text-lg"
                required
              />
            </div>
            <button
              type="submit"
              disabled={analyzing}
              className="w-full bg-[#2C3E50] hover:bg-[#1a252f] disabled:bg-gray-400 text-white font-semibold py-3 px-6 rounded-lg transition-colors text-lg"
            >
              {analyzing ? 'Analyzing Video...' : 'Analyze Video'}
            </button>
          </form>
        </div>

        {error && (
          <div className="bg-red-50 border border-[#DC3545] text-[#DC3545] px-6 py-4 rounded-lg mb-6">
            <p className="font-medium text-lg">Error</p>
            <p>{error}</p>
          </div>
        )}

        {analyzing && (
          <div className="bg-white rounded-lg shadow-xl p-8">
            <div className="mb-4">
              <div className="flex justify-between items-center mb-2">
                <p className="text-[#4B5563] text-lg font-medium">{progressMessage}</p>
                <span className="text-[#00ADB5] font-bold text-xl">{progress}%</span>
              </div>
              <p className="text-sm text-gray-500">This may take 30-60 seconds</p>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-4 overflow-hidden">
              <div 
                className="bg-[#00ADB5] h-4 rounded-full transition-all duration-500 ease-out" 
                style={{width: `${progress}%`}}
              ></div>
            </div>
          </div>
        )}

        {result && (
          <div className="space-y-6">
            <div className={`bg-linear-to-r ${getGradeColorClass(result.gradeColor)} rounded-lg shadow-2xl p-12 text-white`}>
              <div className="text-center">
                <div className="text-9xl font-bold mb-4">{result.grade}</div>
                <div className="text-3xl font-semibold mb-2">{result.gradeDescription}</div>
                <div className="text-xl opacity-90">Score: {result.score}%</div>
                <div className="mt-4 text-base opacity-80">
                  Based on {result.sampledFacts} verified facts (sampled from {result.totalFacts} total)
                </div>
              </div>
            </div>

            <div className="bg-white rounded-lg shadow-xl p-8">
              <h3 className="text-2xl font-bold text-[#2C3E50] mb-6">Verification Summary</h3>
              <div className="grid grid-cols-3 gap-6">
                <div className="text-center p-6 bg-green-50 rounded-lg border-2 border-green-200">
                  <div className="text-4xl font-bold text-[#28A745]">{result.summary.supported}</div>
                  <div className="text-sm text-[#4B5563] mt-2 font-medium">Supported</div>
                </div>
                <div className="text-center p-6 bg-yellow-50 rounded-lg border-2 border-yellow-200">
                  <div className="text-4xl font-bold text-[#FFC107]">{result.summary.partiallyTrue}</div>
                  <div className="text-sm text-[#4B5563] mt-2 font-medium">Partially True</div>
                </div>
                <div className="text-center p-6 bg-red-50 rounded-lg border-2 border-red-200">
                  <div className="text-4xl font-bold text-[#DC3545]">{result.summary.refuted}</div>
                  <div className="text-sm text-[#4B5563] mt-2 font-medium">Refuted</div>
                </div>
              </div>
            </div>

            <div className="bg-white rounded-lg shadow-xl p-8">
              <h3 className="text-2xl font-bold text-[#2C3E50] mb-6">
                Verified Facts ({result.verifiedFacts.length})
              </h3>
              <div className="space-y-4">
                {result.verifiedFacts.map((fact, index) => (
                  <div key={index} className={`border-2 rounded-lg p-6 ${getVerdictColor(fact.verification.verdict)}`}>
                    <div className="flex justify-between items-start mb-3">
                      <div className="flex-1">
                        <p className="font-semibold text-lg mb-2">{fact.claim}</p>
                        <span className="inline-block px-4 py-1 rounded-full text-sm font-bold">
                          {fact.verification.verdict.replace('_', ' ').toUpperCase()}
                        </span>
                      </div>
                    </div>
                    {fact.verification.reasoning && (
                      <p className="text-sm mt-4 mb-3 text-[#4B5563]">
                        <strong className="text-[#2C3E50]">Analysis:</strong> {fact.verification.reasoning}
                      </p>
                    )}
                    {fact.verification.sources && fact.verification.sources.length > 0 && (
                      <div className="mt-4 pt-4 border-t border-gray-200">
                        <p className="text-sm font-semibold mb-2 text-[#2C3E50]">Sources:</p>
                        <ul className="space-y-2">
                          {fact.verification.sources.map((source, idx) => (
                            <li key={idx} className="text-sm">
                              <a href={source.url} target="_blank" rel="noopener noreferrer" className="text-[#00ADB5] hover:text-[#008891] hover:underline font-medium">
                                {source.title}
                              </a>
                            </li>
                          ))}
                        </ul>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

export default App
