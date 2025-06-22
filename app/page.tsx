'use client'

import { useState, useEffect } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Textarea } from '@/components/ui/textarea'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Label } from '@/components/ui/label'
import { Progress } from '@/components/ui/progress'
import { Checkbox } from '@/components/ui/checkbox'
import { Separator } from '@/components/ui/separator'
import { Badge } from '@/components/ui/badge'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { AlertCircle, Play, Pause, Square, Loader2, Brain, Mic, FileText, Sparkles } from 'lucide-react'
import { toast } from 'sonner'
import { Alert, AlertDescription } from '@/components/ui/alert'

interface Mentor {
  id: string
  name: string
  displayName: string
  status: string
  hasVoice: boolean
}

interface AnalysisStep {
  id: string
  name: string
  completed: boolean
  active: boolean
}

const AI_MODELS = {
  OpenAI: {
    'GPT-4o Mini': 'gpt-4o-mini',
    'GPT-4o': 'gpt-4o',
    'GPT-4 Turbo': 'gpt-4-turbo'
  },
  Google: {
    'Gemini 2.5 Pro': 'gemini-2.5-pro',
    'Gemini 2.5 Flash': 'gemini-2.5-flash',
    'Gemini 2.0 Flash': 'gemini-2.0-flash',
    'Gemini 2.0 Flash-Lite': 'gemini-2.0-flash-lite'
  }
}

const ANALYSIS_STEPS: AnalysisStep[] = [
  { id: 'scraping', name: 'Scraping Content', completed: false, active: false },
  { id: 'author', name: 'Inferring Author', completed: false, active: false },
  { id: 'style', name: 'Analyzing Style', completed: false, active: false },
  { id: 'prompts', name: 'Generating Prompts', completed: false, active: false },
  { id: 'mentorgram', name: 'Creating Mentor-gram', completed: false, active: false },
  { id: 'summary', name: 'Building Summary', completed: false, active: false },
  { id: 'database', name: 'Updating Database', completed: false, active: false }
]

export default function Home() {
  const [selectedService, setSelectedService] = useState<string>('OpenAI')
  const [selectedModel, setSelectedModel] = useState<string>('gpt-4o-mini')
  const [contentUrl, setContentUrl] = useState<string>('')
  const [selectedMentor, setSelectedMentor] = useState<string>('')
  const [userText, setUserText] = useState<string>('')
  const [preserveTone, setPreserveTone] = useState<boolean>(false)
  const [mentors, setMentors] = useState<Mentor[]>([])
  const [analysisSteps, setAnalysisSteps] = useState<AnalysisStep[]>(ANALYSIS_STEPS)
  const [isAnalyzing, setIsAnalyzing] = useState<boolean>(false)
  const [isRewriting, setIsRewriting] = useState<boolean>(false)
  const [progress, setProgress] = useState<number>(0)
  const [consoleOutput, setConsoleOutput] = useState<string>('')
  const [rewrittenText, setRewrittenText] = useState<string>('')
  const [audioPlaying, setAudioPlaying] = useState<boolean>(false)
  const [audioLoading, setAudioLoading] = useState<boolean>(false)

  useEffect(() => {
    fetchMentors()
  }, [])

  useEffect(() => {
    const models = AI_MODELS[selectedService as keyof typeof AI_MODELS]
    if (models) {
      const firstModel = Object.values(models)[0]
      setSelectedModel(firstModel)
    }
  }, [selectedService])

  const fetchMentors = async () => {
    try {
      const response = await fetch('/api/mentors')
      if (response.ok) {
        const data = await response.json()
        setMentors(data)
      }
    } catch (error) {
      console.error('Failed to fetch mentors:', error)
    }
  }

  const addToConsole = (message: string) => {
    setConsoleOutput(prev => prev + message + '\n')
  }

  const resetAnalysisSteps = () => {
    setAnalysisSteps(ANALYSIS_STEPS.map(step => ({ ...step, completed: false, active: false })))
    setProgress(0)
  }

  const updateAnalysisStep = (stepId: string, completed: boolean = true, active: boolean = false) => {
    setAnalysisSteps(prev => prev.map(step => 
      step.id === stepId 
        ? { ...step, completed, active }
        : { ...step, active: false }
    ))
    
    if (completed) {
      const completedCount = analysisSteps.filter(s => s.completed).length + 1
      setProgress((completedCount / ANALYSIS_STEPS.length) * 100)
    }
  }

  const handleCompleteAnalysis = async () => {
    if (!contentUrl.trim()) {
      toast.error('Please enter a content URL')
      return
    }

    setIsAnalyzing(true)
    resetAnalysisSteps()
    setConsoleOutput('')
    addToConsole('🚀 Starting complete analysis workflow...')

    try {
      updateAnalysisStep('scraping', false, true)
      addToConsole('📄 Scraping content from URL...')

      const response = await fetch('/api/analyze', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          url: contentUrl,
          service: selectedService.toLowerCase(),
          model: selectedModel,
        }),
      })

      if (!response.ok) {
        throw new Error(`Analysis failed: ${response.statusText}`)
      }

      const reader = response.body?.getReader()
      if (!reader) throw new Error('No response stream')

      const decoder = new TextDecoder()
      let buffer = ''

      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        buffer += decoder.decode(value, { stream: true })
        const lines = buffer.split('\n')
        buffer = lines.pop() || ''

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const data = JSON.parse(line.slice(6))
              
              if (data.step) {
                updateAnalysisStep(data.step, data.completed, !data.completed)
              }
              
              if (data.message) {
                addToConsole(data.message)
              }
              
              if (data.error) {
                throw new Error(data.error)
              }
              
              if (data.complete) {
                addToConsole('🎉 Analysis completed successfully!')
                toast.success('Mentor analysis completed!')
                fetchMentors()
              }
            } catch (e) {
              console.error('Error parsing SSE data:', e)
            }
          }
        }
      }
    } catch (error) {
      console.error('Analysis error:', error)
      addToConsole(`❌ Error: ${error instanceof Error ? error.message : 'Unknown error'}`)
      toast.error('Analysis failed. Please try again.')
    } finally {
      setIsAnalyzing(false)
    }
  }

  const handleRewriteText = async () => {
    if (!userText.trim()) {
      toast.error('Please enter text to rewrite')
      return
    }

    if (!selectedMentor) {
      toast.error('Please select a mentor')
      return
    }

    setIsRewriting(true)
    setRewrittenText('')
    addToConsole('✍️ Rewriting text in mentor\'s style...')

    try {
      const response = await fetch('/api/rewrite', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          text: userText,
          mentorId: selectedMentor,
          service: selectedService.toLowerCase(),
          model: selectedModel,
          preserveTone,
        }),
      })

      if (!response.ok) {
        throw new Error(`Rewrite failed: ${response.statusText}`)
      }

      const data = await response.json()
      setRewrittenText(data.rewrittenText)
      addToConsole('✅ Text rewritten successfully!')
      toast.success('Text rewritten in mentor\'s style!')
    } catch (error) {
      console.error('Rewrite error:', error)
      addToConsole(`❌ Error: ${error instanceof Error ? error.message : 'Unknown error'}`)
      toast.error('Rewrite failed. Please try again.')
    } finally {
      setIsRewriting(false)
    }
  }

  const handlePlayAudio = async () => {
    const textToPlay = preserveTone ? userText : rewrittenText
    if (!textToPlay.trim()) {
      toast.error('No text available for audio playback')
      return
    }

    const mentor = mentors.find(m => m.id === selectedMentor)
    if (!mentor?.hasVoice) {
      toast.error('Voice not available for this mentor')
      return
    }

    setAudioLoading(true)
    addToConsole('🎤 Generating audio...')

    try {
      const response = await fetch('/api/tts', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          text: textToPlay,
          mentorId: selectedMentor,
        }),
      })

      if (!response.ok) {
        throw new Error(`TTS failed: ${response.statusText}`)
      }

      const audioBlob = await response.blob()
      const audioUrl = URL.createObjectURL(audioBlob)
      const audio = new Audio(audioUrl)
      
      audio.onplay = () => setAudioPlaying(true)
      audio.onended = () => setAudioPlaying(false)
      audio.onerror = () => {
        setAudioPlaying(false)
        toast.error('Audio playback failed')
      }
      
      await audio.play()
      addToConsole('🔊 Audio playback started')
    } catch (error) {
      console.error('TTS error:', error)
      addToConsole(`❌ TTS Error: ${error instanceof Error ? error.message : 'Unknown error'}`)
      toast.error('Audio generation failed')
    } finally {
      setAudioLoading(false)
    }
  }

  const selectedMentorData = mentors.find(m => m.id === selectedMentor)
  const canPlayAudio = selectedMentorData?.hasVoice && (preserveTone ? userText.trim() : rewrittenText.trim())

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 p-4">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold text-gray-900 mb-2 flex items-center justify-center gap-2">
            <Brain className="h-8 w-8 text-blue-600" />
            MentorMirror
          </h1>
          <p className="text-lg text-gray-600">AI-Powered Writing Style Emulation</p>
        </div>

        {/* Main Content */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
          {/* Add New Mentor */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <FileText className="h-5 w-5" />
                1. Add New Mentor
              </CardTitle>
              <CardDescription>
                Automatically detect author and analyze their writing style from any URL
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              {/* AI Service Selection */}
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label htmlFor="service">AI Service</Label>
                  <Select value={selectedService} onValueChange={setSelectedService}>
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      {Object.keys(AI_MODELS).map(service => (
                        <SelectItem key={service} value={service}>
                          {service}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                <div>
                  <Label htmlFor="model">Model</Label>
                  <Select value={selectedModel} onValueChange={setSelectedModel}>
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      {Object.entries(AI_MODELS[selectedService as keyof typeof AI_MODELS] || {}).map(([name, value]) => (
                        <SelectItem key={value} value={value}>
                          {name}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
              </div>

              {/* URL Input */}
              <div>
                <Label htmlFor="url">Content URL (Blog Post or PDF)</Label>
                <Input
                  id="url"
                  placeholder="https://example.com/blog-post or path/to/document.pdf"
                  value={contentUrl}
                  onChange={(e) => setContentUrl(e.target.value)}
                />
              </div>

              {/* Start Analysis Button */}
              <Button 
                onClick={handleCompleteAnalysis} 
                disabled={isAnalyzing || !contentUrl.trim()}
                className="w-full"
              >
                {isAnalyzing ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    Analyzing...
                  </>
                ) : (
                  <>
                    <Sparkles className="mr-2 h-4 w-4" />
                    Start Complete Analysis
                  </>
                )}
              </Button>

              {/* Progress Tracking */}
              {isAnalyzing && (
                <div className="space-y-3">
                  <Progress value={progress} className="w-full" />
                  <div className="grid grid-cols-2 gap-2">
                    {analysisSteps.map((step) => (
                      <div key={step.id} className="flex items-center space-x-2">
                        <Checkbox checked={step.completed} disabled />
                        <span className={`text-sm ${step.active ? 'text-blue-600 font-medium' : step.completed ? 'text-green-600' : 'text-gray-500'}`}>
                          {step.name}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </CardContent>
          </Card>

          {/* Apply Style */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Sparkles className="h-5 w-5" />
                2. Apply Mentor Style
              </CardTitle>
              <CardDescription>
                Rewrite your text in your chosen mentor's voice
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              {/* Mentor Selection */}
              <div className="flex gap-2">
                <div className="flex-1">
                  <Label htmlFor="mentor">Select Mentor</Label>
                  <Select value={selectedMentor} onValueChange={setSelectedMentor}>
                    <SelectTrigger>
                      <SelectValue placeholder="Choose a mentor..." />
                    </SelectTrigger>
                    <SelectContent>
                      {mentors.map((mentor) => (
                        <SelectItem key={mentor.id} value={mentor.id}>
                          <div className="flex items-center gap-2">
                            {mentor.displayName}
                            {mentor.hasVoice && <Mic className="h-3 w-3 text-green-500" />}
                          </div>
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                <Button variant="outline" onClick={fetchMentors} className="mt-6">
                  Refresh
                </Button>
              </div>

              {/* User Text Input */}
              <div>
                <Label htmlFor="userText">Your Text to Rewrite</Label>
                <Textarea
                  id="userText"
                  placeholder="Enter your text here to rewrite in the mentor's style..."
                  value={userText}
                  onChange={(e) => setUserText(e.target.value)}
                  rows={4}
                />
              </div>

              {/* Preserve Tone Option */}
              <div className="flex items-center space-x-2">
                <Checkbox 
                  id="preserveTone" 
                  checked={preserveTone}
                  onCheckedChange={(checked: boolean) => setPreserveTone(checked)}
                />
                <Label htmlFor="preserveTone" className="text-sm">
                  Preserve text without tone (use mentor's voice for original text)
                </Label>
              </div>

              {/* Rewrite Button */}
              <Button 
                onClick={handleRewriteText}
                disabled={isRewriting || !userText.trim() || !selectedMentor}
                className="w-full"
              >
                {isRewriting ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    Rewriting...
                  </>
                ) : (
                  'Rewrite in Mentor\'s Style'
                )}
              </Button>

              {/* Audio Controls */}
              {canPlayAudio && (
                <div className="flex items-center gap-2 p-3 bg-green-50 rounded-lg">
                  <Mic className="h-4 w-4 text-green-600" />
                  <span className="text-sm text-green-700 flex-1">Voice available</span>
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={handlePlayAudio}
                    disabled={audioLoading}
                  >
                    {audioLoading ? (
                      <Loader2 className="h-4 w-4 animate-spin" />
                    ) : audioPlaying ? (
                      <Pause className="h-4 w-4" />
                    ) : (
                      <Play className="h-4 w-4" />
                    )}
                  </Button>
                </div>
              )}
            </CardContent>
          </Card>
        </div>

        {/* Results Section */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Console Output */}
          <Card>
            <CardHeader>
              <CardTitle>Console Output</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="bg-gray-900 text-green-400 p-4 rounded-lg h-64 overflow-y-auto scrollbar-thin font-mono text-sm">
                <pre className="whitespace-pre-wrap">{consoleOutput || 'Ready to start...'}</pre>
              </div>
            </CardContent>
          </Card>

          {/* Rewritten Text */}
          <Card>
            <CardHeader>
              <CardTitle>Rewritten Text</CardTitle>
            </CardHeader>
            <CardContent>
              {rewrittenText ? (
                <div className="bg-blue-50 p-4 rounded-lg h-64 overflow-y-auto scrollbar-thin">
                  <p className="text-gray-800 whitespace-pre-wrap">{rewrittenText}</p>
                </div>
              ) : (
                <div className="bg-gray-50 p-4 rounded-lg h-64 flex items-center justify-center">
                  <p className="text-gray-500 text-center">
                    Rewritten text will appear here after you rewrite your text in a mentor's style
                  </p>
                </div>
              )}
            </CardContent>
          </Card>
        </div>

        {/* Info Section */}
        <Card className="mt-6">
          <CardHeader>
            <CardTitle>How MentorMirror Works</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="text-center">
                <div className="bg-blue-100 rounded-full p-3 w-12 h-12 mx-auto mb-2 flex items-center justify-center">
                  <FileText className="h-6 w-6 text-blue-600" />
                </div>
                <h3 className="font-semibold mb-1">1. Content Analysis</h3>
                <p className="text-sm text-gray-600">
                  Paste any URL and our AI automatically detects the author and analyzes their unique writing style
                </p>
              </div>
              <div className="text-center">
                <div className="bg-green-100 rounded-full p-3 w-12 h-12 mx-auto mb-2 flex items-center justify-center">
                  <Sparkles className="h-6 w-6 text-green-600" />
                </div>
                <h3 className="font-semibold mb-1">2. Style Application</h3>
                <p className="text-sm text-gray-600">
                  Enter your own text and watch it transform into your chosen mentor's voice while preserving your message
                </p>
              </div>
              <div className="text-center">
                <div className="bg-purple-100 rounded-full p-3 w-12 h-12 mx-auto mb-2 flex items-center justify-center">
                  <Mic className="h-6 w-6 text-purple-600" />
                </div>
                <h3 className="font-semibold mb-1">3. Voice Synthesis</h3>
                <p className="text-sm text-gray-600">
                  For supported mentors, hear your text spoken in their authentic voice using advanced AI technology
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
} 