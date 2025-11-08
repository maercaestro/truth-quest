import { useState, useMemo, useEffect } from 'react'
import { Search, Shield, CheckCircle, AlertTriangle, XCircle, Loader2, Youtube, Sparkles, LogOut, User, Smile, Heart, Star, Zap, Crown, Flame, Lock, Coffee } from 'lucide-react'
import { useAuth } from './contexts/AuthContext'
import AuthModal from './components/AuthModal'
import { API_URL } from './config'
import './App.css'

// CONFIGURATION - Easy to change for testing/production
const USAGE_LIMITS = {
  DAILY_LIMIT: 10,    // Change this for daily limit
  MONTHLY_LIMIT: 150  // Change this for monthly limit (kept for backend compatibility)
}

function App() {
  const [youtubeUrl, setYoutubeUrl] = useState('')
  const [analyzing, setAnalyzing] = useState(false)
  const [progress, setProgress] = useState(0)
  const [progressMessage, setProgressMessage] = useState('')
  const [result, setResult] = useState(null)
  const [error, setError] = useState(null)
  const [checkMode, setCheckMode] = useState('sample') // 'sample' or 'full'
  const [showAuthModal, setShowAuthModal] = useState(false)
  const [usageCount, setUsageCount] = useState(0)
  const [usageLimitReached, setUsageLimitReached] = useState(false)
  
  const { currentUser, logout, idToken } = useAuth()

  // Load usage count from localStorage
  useEffect(() => {
    if (currentUser) {
      const today = new Date().toDateString()
      const storageKey = `usage_${currentUser.uid}_${today}`
      const stored = localStorage.getItem(storageKey)
      const count = stored ? parseInt(stored, 10) : 0
      setUsageCount(count)
      setUsageLimitReached(count >= USAGE_LIMITS.DAILY_LIMIT)
    } else {
      setUsageCount(0)
      setUsageLimitReached(false)
    }
  }, [currentUser])

  // Generate a random icon based on user ID for consistency
  const userIcon = useMemo(() => {
    if (!currentUser) return User;
    
    const icons = [User, Smile, Heart, Star, Zap, Crown, Flame];
    const colors = ['#00ADB5', '#28A745', '#FFC107', '#DC3545', '#9B59B6', '#3498DB', '#E74C3C'];
    
    // Use user email/uid to generate consistent random index
    const seed = currentUser.email || currentUser.uid || '';
    const hash = seed.split('').reduce((acc, char) => acc + char.charCodeAt(0), 0);
    
    const iconIndex = hash % icons.length;
    const colorIndex = hash % colors.length;
    
    return { Icon: icons[iconIndex], color: colors[colorIndex] };
  }, [currentUser]);

  // Debug auth state
  console.log('🔍 Auth Debug:', { 
    currentUser: currentUser ? 'Logged in' : 'Not logged in',
    userEmail: currentUser?.email,
    photoURL: currentUser?.photoURL,
    displayName: currentUser?.displayName,
    hasToken: !!idToken,
    showAuthModal 
  })

  const handleSignInClick = () => {
    console.log('🔘 Sign In button clicked')
    console.log('📊 Current showAuthModal state:', showAuthModal)
    setShowAuthModal(true)
    console.log('✅ setShowAuthModal(true) called')
  }

  const handleAnalyze = async (e, mode = checkMode) => {
    e.preventDefault()
    
    // Check if user is logged in
    if (!currentUser) {
      setShowAuthModal(true)
      return
    }

    // Check usage limit
    if (usageLimitReached) {
      setError(`Daily limit of ${USAGE_LIMITS.DAILY_LIMIT} analyses reached. Please try again tomorrow.`)
      return
    }
    
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

      const response = await fetch(`${API_URL}/api/analyze`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${idToken}`
        },
        body: JSON.stringify({ 
          youtubeUrl,
          checkMode: mode
        }),
      })

      clearInterval(progressInterval)
      setProgress(100)
      setProgressMessage('Analysis complete!')

      const data = await response.json()

      if (!response.ok) {
        // Handle rate limit specifically
        if (response.status === 429) {
          throw new Error(data.error || 'Usage limit exceeded. Please try again later.')
        }
        throw new Error(data.error || 'Failed to analyze video')
      }

      setResult(data)
      
      // Increment usage count in localStorage
      const today = new Date().toDateString()
      const storageKey = `usage_${currentUser.uid}_${today}`
      const newCount = usageCount + 1
      localStorage.setItem(storageKey, newCount.toString())
      setUsageCount(newCount)
      setUsageLimitReached(newCount >= USAGE_LIMITS.DAILY_LIMIT)
      
    } catch (err) {
      setError(err.message)
    } finally {
      setAnalyzing(false)
      setProgress(0)
    }
  }

  const getGradeColorClass = (color) => {
    const colors = {
      green: '!bg-linear-to-r from-[#28A745] to-[#20803a]',
      blue: '!bg-linear-to-r from-[#00ADB5] to-[#008891]',
      orange: '!bg-linear-to-r from-[#FFC107] to-[#e6ad06]',
      red: '!bg-linear-to-r from-[#DC3545] to-[#c82333]',
      gray: '!bg-linear-to-r from-gray-500 to-slate-600'
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
    <div className="min-h-screen bg-linear-to-br from-slate-50 via-blue-50 to-indigo-50">
      {/* Header */}
      <div className="relative overflow-hidden">
        <div className="absolute inset-0 bg-linear-to-r from-[#2C3E50] via-[#34495E] to-[#2C3E50] opacity-95"></div>
        <div className="absolute inset-0 opacity-10">
          <div className="absolute inset-0 bg-[radial-gradient(circle_at_1px_1px,rgba(255,255,255,0.3)_1px,transparent_0)] bg-size-[20px_20px]"></div>
        </div>
        <div className="relative backdrop-blur-sm bg-white/10 border-b border-white/20">
          <div className="w-full px-4 py-8">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-6">
                <div className="relative">
                  <img src="/logotruth.png" alt="Truth Quest Logo" className="h-16 w-16 rounded-full border-2 border-white/30 shadow-lg" />
                </div>
                <div>
                  <h1 className="text-4xl font-semibold text-white tracking-tight font-sans">Truth Quest</h1>
                  <p className="text-gray-300 text-sm font-normal mt-1">AI-Powered YouTube Fact Checker</p>
                </div>
              </div>
              
              {/* User Profile Section */}
              {currentUser ? (
                <div className="flex items-center gap-4">
                  {/* Buy Me a Coffee Button */}
                  <a 
                    href="https://www.buymeacoffee.com/maercaestro"
                    target="_blank"
                    rel="noopener noreferrer"
                    className="flex items-center gap-2 bg-[#FFDD00] hover:bg-[#FFED4E] text-black px-5 py-2.5 rounded-full transition-all duration-300 font-semibold shadow-lg hover:shadow-xl hover:scale-105 border-2 border-black/10"
                  >
                    <Coffee className="h-5 w-5" />
                    Buy me a coffee
                  </a>
                  
                  <div className="flex items-center gap-3 bg-white/10 backdrop-blur-md rounded-full px-4 py-2 border border-white/20">
                    <div className="relative">
                      <div 
                        className="h-10 w-10 rounded-full flex items-center justify-center border-2 border-white" 
                        style={{ backgroundColor: userIcon.color }}
                      >
                        <userIcon.Icon className="h-5 w-5 text-white" />
                      </div>
                    </div>
                    <div className="text-left">
                      <p className="text-white font-medium text-sm">{currentUser.displayName || currentUser.email}</p>
                      <p className="text-[#00ADB5] text-xs">Signed In</p>
                    </div>
                  </div>
                  <button
                    onClick={logout}
                    className="flex items-center gap-2 !bg-red-500/90 hover:!bg-red-600 !text-white px-4 py-2 rounded-full transition-all duration-300 font-medium shadow-lg hover:shadow-xl"
                  >
                    <LogOut className="h-4 w-4" />
                    Sign Out
                  </button>
                </div>
              ) : (
                <div className="flex items-center gap-4">
                  {/* Buy Me a Coffee Button */}
                  <a 
                    href="https://www.buymeacoffee.com/maercaestro"
                    target="_blank"
                    rel="noopener noreferrer"
                    className="flex items-center gap-2 bg-[#FFDD00] hover:bg-[#FFED4E] text-black px-5 py-2.5 rounded-full transition-all duration-300 font-semibold shadow-lg hover:shadow-xl hover:scale-105 border-2 border-black/10"
                  >
                    <Coffee className="h-5 w-5" />
                    Buy me a coffee
                  </a>
                  
                  <button
                    onClick={handleSignInClick}
                    className="flex items-center gap-2 !bg-[#00ADB5] hover:!bg-[#00D4FF] !text-white px-6 py-3 rounded-full transition-all duration-300 font-semibold shadow-lg hover:shadow-xl"
                  >
                    <User className="h-5 w-5" />
                    Sign In
                  </button>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="w-full px-4 py-12 max-w-none">
        {/* Show form only when no results */}
        {!result && (
          <div className="relative backdrop-blur-xl bg-white/80 rounded-3xl shadow-2xl border border-white/20 p-10 mb-8 hover:shadow-3xl transition-all duration-500 max-w-4xl mx-auto">
            <div className="text-center mb-8">
              <h2 className="text-3xl font-bold text-[#2C3E50] mb-3 flex items-center justify-center gap-3">
                <Youtube className="h-8 w-8 text-red-500" />
                Analyze YouTube Video
              </h2>
              <p className="text-gray-600 text-lg">Enter a YouTube URL to verify its factual accuracy</p>
              
              {/* Usage Counter */}
              {currentUser && (
                <div className="mt-4 inline-flex items-center gap-2 bg-blue-50 border border-blue-200 px-4 py-2 rounded-full">
                  <Shield className="h-4 w-4 text-[#00ADB5]" />
                  <span className="text-sm font-medium text-gray-700">
                    Usage today: <span className="font-bold text-[#00ADB5]">{usageCount}/{USAGE_LIMITS.DAILY_LIMIT}</span>
                  </span>
                </div>
              )}
            </div>
            
            {/* Lock overlay when not logged in */}
            {!currentUser && (
              <div className="absolute inset-0 backdrop-blur-sm bg-white/60 rounded-3xl flex flex-col items-center justify-center z-10">
                <Lock className="h-16 w-16 text-gray-400 mb-4" />
                <h3 className="text-2xl font-bold text-gray-700 mb-2">Sign In Required</h3>
                <p className="text-gray-600 mb-6">Please sign in to start fact-checking videos</p>
                <button
                  onClick={handleSignInClick}
                  className="flex items-center gap-2 !bg-[#00ADB5] hover:!bg-[#00D4FF] !text-white px-8 py-3 rounded-full transition-all duration-300 font-semibold shadow-lg hover:shadow-xl"
                >
                  <User className="h-5 w-5" />
                  Sign In Now
                </button>
              </div>
            )}
            
            <form onSubmit={handleAnalyze} className="space-y-6">
              <div className="relative group">
                <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none">
                  <Search className="h-5 w-5 text-gray-400 group-focus-within:text-[#00ADB5] transition-colors" />
                </div>
                <input
                  id="youtube-url"
                  type="text"
                  value={youtubeUrl}
                  onChange={(e) => setYoutubeUrl(e.target.value)}
                  placeholder="Paste your YouTube URL here..."
                  className="w-full pl-12 pr-4 py-4 border-2 border-gray-200 rounded-2xl focus:ring-4 focus:ring-[#00ADB5]/20 focus:border-[#00ADB5] text-lg transition-all duration-300 bg-white/50 backdrop-blur-sm hover:border-gray-300"
                  required
                />
                <div className="absolute inset-0 rounded-2xl bg-linear-to-r from-[#00ADB5]/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300 pointer-events-none"></div>
              </div>

              {/* Check Mode Selection */}
              <div className="flex gap-4">
                <div className="flex-1 group relative">
                  <button
                    type="button"
                    onClick={() => setCheckMode('sample')}
                    className={`w-full py-3 px-6 rounded-xl font-semibold transition-all duration-300 ${
                      checkMode === 'sample'
                        ? '!bg-[#00ADB5] !text-white !shadow-lg scale-105'
                        : '!bg-gray-100 !text-gray-600 hover:!bg-gray-200'
                    }`}
                  >
                    ⚡ Sample Check (Fast)
                  </button>
                  <div className="absolute bottom-full left-1/2 transform -translate-x-1/2 mb-2 px-4 py-2 bg-gray-900 text-white text-sm rounded-lg opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none whitespace-nowrap z-10">
                    Checks 5-7 random facts • Takes 30-60 seconds • Good for quick verification
                  </div>
                </div>
                
                <div className="flex-1 group relative">
                  <button
                    type="button"
                    onClick={() => setCheckMode('full')}
                    className={`w-full py-3 px-6 rounded-xl font-semibold transition-all duration-300 ${
                      checkMode === 'full'
                        ? '!bg-[#00ADB5] !text-white shadow-lg scale-105'
                        : '!bg-gray-100 !text-gray-600 hover:!bg-gray-200'
                    }`}
                  >
                    🔍 Full Check (Thorough)
                  </button>
                  <div className="absolute bottom-full left-1/2 transform -translate-x-1/2 mb-2 px-4 py-2 bg-gray-900 text-white text-sm rounded-lg opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none whitespace-nowrap z-10">
                    Checks ALL facts • Takes 2-5 minutes • Most accurate verification
                  </div>
                </div>
              </div>
              
              <button
                type="submit"
                disabled={analyzing || usageLimitReached}
                className="w-full bg-linear-to-r from-[#2C3E50] to-[#34495E] hover:from-[#1a252f] hover:to-[#2c3e50] disabled:from-gray-400 disabled:to-gray-500 text-white font-bold py-4 px-8 rounded-2xl transition-all duration-300 text-xl shadow-lg hover:shadow-xl hover:scale-[1.02] disabled:hover:scale-100 disabled:cursor-not-allowed flex items-center justify-center gap-3 group"
              >
                {analyzing ? (
                  <>
                    <Loader2 className="h-6 w-6 animate-spin" />
                    Analyzing Video...
                  </>
                ) : usageLimitReached ? (
                  <>
                    <Lock className="h-6 w-6" />
                    Daily Limit Reached
                  </>
                ) : (
                  <>
                    <Shield className="h-6 w-6 group-hover:animate-pulse" />
                    Start Fact Check
                  </>
                )}
              </button>
            </form>
          </div>
        )}

        {/* Show "Check Next Video" button when results exist */}
        {result && (
          <div className="max-w-4xl mx-auto mb-8">
            <button
              onClick={() => {
                setResult(null);
                setYoutubeUrl('');
                setError(null);
              }}
              className="w-full bg-linear-to-r from-[#00ADB5] to-[#00D4FF] hover:from-[#008891] hover:to-[#00ADB5] text-white font-bold py-4 px-8 rounded-2xl transition-all duration-300 text-xl shadow-lg hover:shadow-xl hover:scale-[1.02] flex items-center justify-center gap-3 group"
            >
              <Youtube className="h-6 w-6 group-hover:animate-pulse" />
              Check Next Video
            </button>
          </div>
        )}

        {error && (
          <div className="backdrop-blur-xl bg-red-50/80 border-2 border-red-200/50 rounded-2xl p-6 mb-8 animate-in slide-in-from-top-2 duration-500">
            <div className="flex items-start gap-4">
              <div className="shrink-0">
                <XCircle className="h-8 w-8 text-[#DC3545]" />
              </div>
              <div>
                <h3 className="text-xl font-bold text-[#DC3545] mb-2">Analysis Error</h3>
                <p className="text-gray-700 text-lg">{error}</p>
              </div>
            </div>
          </div>
        )}

        {analyzing && (
          <div className="backdrop-blur-xl bg-white/80 rounded-3xl shadow-2xl border border-white/20 p-8 animate-in fade-in-0 duration-500">
            <div className="text-center mb-6">
              <Loader2 className="h-12 w-12 text-[#00ADB5] animate-spin mx-auto mb-4" />
              <h3 className="text-2xl font-bold text-[#2C3E50] mb-2">Analyzing Video</h3>
              <p className="text-gray-600 text-lg">{progressMessage}</p>
              <p className="text-sm text-gray-500 mt-2">This process typically takes 30-60 seconds</p>
            </div>
            
            <div className="relative mb-6">
              <div className="w-full bg-gray-200 rounded-full h-6 overflow-hidden shadow-inner">
                <div 
                  className="bg-linear-to-r from-[#00ADB5] via-[#00C4CC] to-[#00ADB5] h-6 rounded-full transition-all duration-1000 ease-out shadow-lg relative overflow-hidden"
                  style={{width: `${progress}%`}}
                >
                  <div className="absolute inset-0 bg-linear-to-r from-transparent via-white/30 to-transparent animate-pulse"></div>
                </div>
              </div>
              <div className="flex justify-between items-center mt-3">
                <span className="text-sm text-gray-500">Progress</span>
                <span className="text-xl font-bold text-[#00ADB5]">{progress}%</span>
              </div>
            </div>
          </div>
        )}

        {result && (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 animate-in fade-in-0 slide-in-from-bottom-4 duration-700">
            {/* Left Side - Video Section */}
            <div className="space-y-6">
              {/* Video Embed */}
              <div className="backdrop-blur-xl bg-white/80 rounded-3xl shadow-2xl border border-white/20 p-6 sticky top-4">
                <div className="aspect-video bg-black rounded-xl overflow-hidden mb-4">
                  <iframe
                    src={`https://www.youtube.com/embed/${youtubeUrl.match(/(?:youtube\.com\/(?:[^\/]+\/.+\/|(?:v|e(?:mbed)?)\/|.*[?&]v=)|youtu\.be\/)([^"&?\/\s]{11})/)?.[1]}`}
                    title="YouTube video player"
                    className="w-full h-full"
                    frameBorder="0"
                    allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
                    allowFullScreen
                  ></iframe>
                </div>
                
                {/* Video Info */}
                <div className="space-y-3">
                  <h4 className="text-xl font-bold text-[#2C3E50] leading-tight">{result.videoTitle}</h4>
                  <div className="flex flex-wrap items-center gap-3 text-sm text-gray-600">
                    <span className="flex items-center gap-2">
                      <Shield className="h-4 w-4" />
                      {result.videoUploader}
                    </span>
                    {result.videoDuration > 0 && (
                      <span className="flex items-center gap-2">
                        <span>⏱️</span>
                        {Math.floor(result.videoDuration / 60)}:{(result.videoDuration % 60).toString().padStart(2, '0')}
                      </span>
                    )}
                    {result.videoViewCount > 0 && (
                      <span className="flex items-center gap-2">
                        <span>👁️</span>
                        {result.videoViewCount.toLocaleString()} views
                      </span>
                    )}
                  </div>
                </div>

                {/* Grade Display */}
                <div className={`mt-6 rounded-2xl p-6 text-white relative overflow-hidden ${getGradeColorClass(result.gradeColor)}`}>
                  <div className="absolute inset-0 bg-linear-to-br from-white/10 via-transparent to-black/20"></div>
                  <div className="relative text-center">
                    <div className="inline-flex items-center justify-center w-20 h-20 bg-white/20 rounded-full mb-3 backdrop-blur-sm border border-white/30">
                      <div className="text-5xl font-black">{result.grade}</div>
                    </div>
                    <div className="text-2xl font-bold mb-2">{result.gradeDescription}</div>
                    <div className="text-lg opacity-90 mb-3">Accuracy: {result.score}%</div>
                    <div className="text-sm bg-white/20 px-4 py-2 rounded-full backdrop-blur-sm border border-white/30 inline-flex items-center gap-2">
                      <Shield className="h-4 w-4" />
                      {result.checkMode === 'full' 
                        ? `All ${result.sampledFacts} facts verified` 
                        : `${result.sampledFacts}/${result.totalFacts} facts verified`}
                    </div>
                  </div>
                </div>
              </div>
            </div>

            {/* Right Side - Analysis Section (Scrollable) */}
            <div className="space-y-6 max-h-[calc(100vh-12rem)] overflow-y-auto pr-2 scrollbar-thin scrollbar-thumb-gray-300 scrollbar-track-gray-100">

            {/* Central Thesis */}
            {result.centralThesis && (
              <div className={`backdrop-blur-xl rounded-3xl shadow-2xl border-2 p-8 hover:shadow-3xl transition-all duration-500 ${getVerdictColor(result.centralThesis.verification.verdict)}`}>
                <h3 className="text-3xl font-bold text-[#2C3E50] mb-6 text-center flex items-center justify-center gap-3">
                  <Sparkles className="h-8 w-8" />
                  Central Thesis
                </h3>
                <div className="space-y-4">
                  <div className="flex items-start gap-3 mb-4">
                    {result.centralThesis.verification.verdict === 'supported' && <CheckCircle className="h-8 w-8 text-[#28A745] shrink-0 mt-1" />}
                    {result.centralThesis.verification.verdict === 'partially_true' && <AlertTriangle className="h-8 w-8 text-[#FFC107] shrink-0 mt-1" />}
                    {result.centralThesis.verification.verdict === 'refuted' && <XCircle className="h-8 w-8 text-[#DC3545] shrink-0 mt-1" />}
                    <div className="flex-1">
                      <p className="text-2xl font-bold text-[#2C3E50] mb-3 leading-relaxed">{result.centralThesis.claim}</p>
                      <span className="inline-flex items-center px-5 py-2 rounded-full text-base font-bold bg-white/80 backdrop-blur-sm border-2 border-current">
                        {result.centralThesis.verification.verdict.replace('_', ' ').toUpperCase()}
                      </span>
                    </div>
                  </div>
                  
                  {result.centralThesis.verification.reasoning && (
                    <div className="p-5 bg-white/50 rounded-xl border border-white/50">
                      <p className="text-lg text-[#4B5563] leading-relaxed">
                        <strong className="text-[#2C3E50] font-semibold">Analysis:</strong> {result.centralThesis.verification.reasoning}
                      </p>
                    </div>
                  )}
                  
                  {result.centralThesis.verification.sources && result.centralThesis.verification.sources.length > 0 && (
                    <div className="pt-5 border-t border-gray-200/50">
                      <p className="text-lg font-semibold mb-3 text-[#2C3E50] flex items-center gap-2">
                        <Shield className="h-5 w-5" />
                        Sources:
                      </p>
                      <div className="space-y-3">
                        {result.centralThesis.verification.sources.map((source, idx) => (
                          <div key={idx} className="flex items-center gap-3 p-3 bg-white/40 rounded-lg border border-white/30 hover:bg-white/60 transition-colors">
                            <div className="w-2 h-2 bg-[#00ADB5] rounded-full shrink-0"></div>
                            <a 
                              href={source.url} 
                              target="_blank" 
                              rel="noopener noreferrer" 
                              className="text-[#00ADB5] hover:text-[#008891] font-medium hover:underline transition-colors flex-1"
                            >
                              {source.title}
                            </a>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* Summary Cards */}
            <div className="backdrop-blur-xl bg-white/80 rounded-3xl shadow-2xl border border-white/20 p-8 hover:shadow-3xl transition-all duration-500">
              <h3 className="text-3xl font-bold text-[#2C3E50] mb-8 text-center flex items-center justify-center gap-3">
                <CheckCircle className="h-8 w-8 text-[#28A745]" />
                Verification Summary
              </h3>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <div className="group bg-linear-to-br from-green-50 to-green-100 rounded-2xl p-8 border-2 border-green-200 hover:shadow-lg hover:scale-105 transition-all duration-300">
                  <div className="text-center">
                    <div className="inline-flex items-center justify-center w-16 h-16 bg-green-500 rounded-full mb-4 group-hover:animate-bounce">
                      <CheckCircle className="h-8 w-8 text-white" />
                    </div>
                    <div className="text-5xl font-black text-[#28A745] mb-3">{result.summary.supported}</div>
                    <div className="text-xl font-bold text-[#4B5563]">Supported</div>
                    <div className="text-sm text-green-600 mt-2">Well-verified claims</div>
                  </div>
                </div>
                
                <div className="group bg-linear-to-br from-yellow-50 to-yellow-100 rounded-2xl p-8 border-2 border-yellow-200 hover:shadow-lg hover:scale-105 transition-all duration-300">
                  <div className="text-center">
                    <div className="inline-flex items-center justify-center w-16 h-16 bg-yellow-500 rounded-full mb-4 group-hover:animate-bounce">
                      <AlertTriangle className="h-8 w-8 text-white" />
                    </div>
                    <div className="text-5xl font-black text-[#FFC107] mb-3">{result.summary.partiallyTrue}</div>
                    <div className="text-xl font-bold text-[#4B5563]">Partially True</div>
                    <div className="text-sm text-yellow-600 mt-2">Needs verification</div>
                  </div>
                </div>
                
                <div className="group bg-linear-to-br from-red-50 to-red-100 rounded-2xl p-8 border-2 border-red-200 hover:shadow-lg hover:scale-105 transition-all duration-300">
                  <div className="text-center">
                    <div className="inline-flex items-center justify-center w-16 h-16 bg-red-500 rounded-full mb-4 group-hover:animate-bounce">
                      <XCircle className="h-8 w-8 text-white" />
                    </div>
                    <div className="text-5xl font-black text-[#DC3545] mb-3">{result.summary.refuted}</div>
                    <div className="text-xl font-bold text-[#4B5563]">Refuted</div>
                    <div className="text-sm text-red-600 mt-2">Inaccurate claims</div>
                  </div>
                </div>
              </div>
            </div>

            {/* Verified Facts */}
            <div className="backdrop-blur-xl bg-white/80 rounded-3xl shadow-2xl border border-white/20 p-8 hover:shadow-3xl transition-all duration-500">
              <h3 className="text-3xl font-bold text-[#2C3E50] mb-8 text-center flex items-center justify-center gap-3">
                <Search className="h-8 w-8 text-[#00ADB5]" />
                Verified Facts ({result.verifiedFacts.length})
              </h3>
              <div className="space-y-6">
                {result.verifiedFacts.map((fact, index) => (
                  <div key={index} className={`group backdrop-blur-sm bg-white/60 border-2 rounded-2xl p-8 hover:shadow-lg hover:scale-[1.01] transition-all duration-300 ${getVerdictColor(fact.verification.verdict)}`}>
                    <div className="flex justify-between items-start mb-4">
                      <div className="flex-1">
                        <div className="flex items-center gap-3 mb-3">
                          {fact.verification.verdict === 'supported' && <CheckCircle className="h-6 w-6 text-[#28A745] shrink-0" />}
                          {fact.verification.verdict === 'partially_true' && <AlertTriangle className="h-6 w-6 text-[#FFC107] shrink-0" />}
                          {fact.verification.verdict === 'refuted' && <XCircle className="h-6 w-6 text-[#DC3545] shrink-0" />}
                          <span className="inline-flex items-center px-4 py-2 rounded-full text-sm font-bold bg-white/80 backdrop-blur-sm border border-current">
                            {fact.verification.verdict.replace('_', ' ').toUpperCase()}
                          </span>
                        </div>
                        <p className="font-bold text-xl mb-4 text-[#2C3E50] leading-relaxed">{fact.claim}</p>
                      </div>
                    </div>
                    
                    {fact.verification.reasoning && (
                      <div className="mb-6 p-4 bg-white/50 rounded-xl border border-white/50">
                        <p className="text-base text-[#4B5563] leading-relaxed">
                          <strong className="text-[#2C3E50] font-semibold">Analysis:</strong> {fact.verification.reasoning}
                        </p>
                      </div>
                    )}
                    
                    {fact.verification.sources && fact.verification.sources.length > 0 && (
                      <div className="pt-6 border-t border-gray-200/50">
                        <p className="text-lg font-semibold mb-4 text-[#2C3E50] flex items-center gap-2">
                          <Shield className="h-5 w-5" />
                          Sources:
                        </p>
                        <div className="space-y-3">
                          {fact.verification.sources.map((source, idx) => (
                            <div key={idx} className="flex items-center gap-3 p-3 bg-white/40 rounded-lg border border-white/30 hover:bg-white/60 transition-colors">
                              <div className="w-2 h-2 bg-[#00ADB5] rounded-full shrink-0"></div>
                              <a 
                                href={source.url} 
                                target="_blank" 
                                rel="noopener noreferrer" 
                                className="text-[#00ADB5] hover:text-[#008891] font-medium hover:underline transition-colors flex-1"
                              >
                                {source.title}
                              </a>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
            </div>
            {/* End of Right Side - Analysis Section */}
          </div>
        )}
      </div>
      
      {/* Auth Modal */}
      {console.log('🎭 Rendering AuthModal:', showAuthModal)}
      {showAuthModal && (
        <AuthModal 
          isOpen={showAuthModal}
          onClose={() => {
            console.log('❌ Closing AuthModal')
            setShowAuthModal(false)
          }} 
        />
      )}
    </div>
  )
}

export default App
