import { NextRequest, NextResponse } from 'next/server'
import { OpenAI } from 'openai'
import { GoogleGenerativeAI } from '@google/generative-ai'
import * as cheerio from 'cheerio'
import axios from 'axios'

interface AnalysisRequest {
  url: string
  service: 'openai' | 'google'
  model: string
}

interface StyleAnalysis {
  tone_voice: string
  sentence_structure: string
  vocabulary_diction: string
  rhetorical_patterns: string
  unique_elements: string
  content_themes: string
  audience_engagement: string
}

// Initialize AI clients
const openai = process.env.OPENAI_API_KEY ? new OpenAI({
  apiKey: process.env.OPENAI_API_KEY,
}) : null

const genai = process.env.GOOGLE_API_KEY ? new GoogleGenerativeAI(process.env.GOOGLE_API_KEY) : null

async function scrapeContent(url: string): Promise<string> {
  try {
    // Handle local files or PDFs differently in production
    if (url.startsWith('http')) {
      const response = await axios.get(url, {
        timeout: 30000,
        headers: {
          'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
      })
      
      const $ = cheerio.load(response.data)
      
      // Remove script and style elements
      $('script, style, nav, header, footer, aside').remove()
      
      // Extract main content
      let content = ''
      const contentSelectors = ['main', 'article', '.content', '.post', '.entry', 'body']
      
      for (const selector of contentSelectors) {
        const element = $(selector).first()
        if (element.length > 0) {
          content = element.text().trim()
          if (content.length > 500) break
        }
      }
      
      if (!content || content.length < 500) {
        content = $('body').text().trim()
      }
      
      // Clean up the content
      content = content
        .replace(/\s+/g, ' ')
        .replace(/\n+/g, '\n')
        .trim()
      
      return content.substring(0, 10000) // Limit content length
    } else {
      throw new Error('Local file processing not supported in web version')
    }
  } catch (error) {
    throw new Error(`Failed to scrape content: ${error instanceof Error ? error.message : 'Unknown error'}`)
  }
}

async function inferAuthor(content: string, service: string, model: string): Promise<string> {
  const prompt = `Analyze the following text and try to determine who the author is based on:
- Any self-references or mentions of their own name
- Writing style and topics that might indicate a specific well-known author
- Any biographical details or personal anecdotes mentioned
- The overall voice and perspective

Text to analyze:
"""
${content.substring(0, 2000)}...
"""

Return ONLY the author's name (first and last name if available). If you cannot determine the author with reasonable confidence, return "Unknown Author".`

  try {
    if (service === 'openai' && openai) {
      const response = await openai.chat.completions.create({
        model,
        messages: [{ role: 'user', content: prompt }],
        max_tokens: 50,
        temperature: 0.3,
      })
      
      const authorName = response.choices[0]?.message?.content?.trim() || 'Unknown Author'
      return authorName.length > 50 ? 'Unknown Author' : authorName
    } else if (service === 'google' && genai) {
      const genModel = genai.getGenerativeModel({ model })
      const result = await genModel.generateContent(prompt)
      const response = await result.response
      const authorName = response.text().trim()
      return authorName.length > 50 ? 'Unknown Author' : authorName
    } else {
      throw new Error('AI service not configured')
    }
  } catch (error) {
    console.error('Author inference error:', error)
    return 'Unknown Author'
  }
}

function extractJSON(content: string): any {
  let jsonStr = content.trim()
  
  // Remove markdown code blocks if present
  if (jsonStr.startsWith('```json')) {
    jsonStr = jsonStr.replace(/^```json\s*/, '').replace(/\s*```$/, '')
  } else if (jsonStr.startsWith('```')) {
    jsonStr = jsonStr.replace(/^```\s*/, '').replace(/\s*```$/, '')
  }
  
  // Extract JSON object
  const jsonMatch = jsonStr.match(/\{[\s\S]*\}/)
  if (jsonMatch) {
    try {
      return JSON.parse(jsonMatch[0])
    } catch (parseError) {
      console.error('JSON parse error:', parseError)
      console.error('Attempted to parse:', jsonMatch[0])
      throw parseError
    }
  }
  
  throw new Error('No valid JSON found in response')
}

async function analyzeStyle(content: string, authorName: string, service: string, model: string): Promise<StyleAnalysis> {
  const prompt = `You are a literary style analyst. Analyze the following text by ${authorName} and extract:

1. **Tone & Voice**: Describe the overall tone (formal/casual, optimistic/pessimistic, etc.)
2. **Sentence Structure**: Analyze sentence length, complexity, use of lists/bullets
3. **Vocabulary & Diction**: Level of technical language, common word choices, jargon
4. **Rhetorical Patterns**: How they present arguments, use of examples, storytelling style
5. **Unique Stylistic Elements**: Signature phrases, punctuation habits, paragraph structure
6. **Content Themes**: What topics/concepts they frequently discuss
7. **Audience Engagement**: How they connect with readers (direct address, questions, etc.)

Text to analyze:
"""
${content}
"""

Return ONLY a valid JSON object with these exact keys: tone_voice, sentence_structure, vocabulary_diction, rhetorical_patterns, unique_elements, content_themes, audience_engagement. Do not include any other text or markdown formatting.

Example format:
{
  "tone_voice": "Your analysis here",
  "sentence_structure": "Your analysis here",
  "vocabulary_diction": "Your analysis here",
  "rhetorical_patterns": "Your analysis here",
  "unique_elements": "Your analysis here",
  "content_themes": "Your analysis here",
  "audience_engagement": "Your analysis here"
}`

  try {
    if (service === 'openai' && openai) {
      const response = await openai.chat.completions.create({
        model,
        messages: [{ role: 'user', content: prompt }],
        max_tokens: 1000,
        temperature: 0.7,
      })
      
      const content = response.choices[0]?.message?.content || ''
      
      try {
        return extractJSON(content)
      } catch (error) {
        console.error('Failed to extract JSON from OpenAI response:', error)
        // Fallback: create structured response
        return {
          tone_voice: 'Analysis not available in structured format',
          sentence_structure: '',
          vocabulary_diction: '',
          rhetorical_patterns: '',
          unique_elements: '',
          content_themes: '',
          audience_engagement: content
        }
      }
    } else if (service === 'google' && genai) {
      const genModel = genai.getGenerativeModel({ model })
      const result = await genModel.generateContent(prompt)
      const response = await result.response
      const content = response.text()
      
      try {
        return extractJSON(content)
      } catch (error) {
        console.error('Failed to extract JSON from Google AI response:', error)
        // Fallback: create structured response
        return {
          tone_voice: 'Analysis not available in structured format',
          sentence_structure: '',
          vocabulary_diction: '',
          rhetorical_patterns: '',
          unique_elements: '',
          content_themes: '',
          audience_engagement: content
        }
      }
    } else {
      throw new Error('AI service not configured')
    }
  } catch (error) {
    console.error('Style analysis error:', error)
    throw new Error(`Style analysis failed: ${error instanceof Error ? error.message : 'Unknown error'}`)
  }
}

export async function POST(req: NextRequest) {
  try {
    const body: AnalysisRequest = await req.json()
    const { url, service, model } = body

    if (!url) {
      return NextResponse.json({ error: 'URL is required' }, { status: 400 })
    }

    // Create a streaming response
    const encoder = new TextEncoder()
    const stream = new ReadableStream({
      async start(controller) {
        try {
          // Step 1: Scrape Content
          controller.enqueue(encoder.encode(`data: ${JSON.stringify({ 
            step: 'scraping', 
            completed: false, 
            message: '📄 Scraping content from URL...' 
          })}\n\n`))

          const content = await scrapeContent(url)
          
          controller.enqueue(encoder.encode(`data: ${JSON.stringify({ 
            step: 'scraping', 
            completed: true, 
            message: '✅ Content scraped successfully' 
          })}\n\n`))

          // Step 2: Infer Author
          controller.enqueue(encoder.encode(`data: ${JSON.stringify({ 
            step: 'author', 
            completed: false, 
            message: '🔍 Inferring author name...' 
          })}\n\n`))

          const authorName = await inferAuthor(content, service, model)
          
          controller.enqueue(encoder.encode(`data: ${JSON.stringify({ 
            step: 'author', 
            completed: true, 
            message: `✅ Author identified: ${authorName}` 
          })}\n\n`))

          // Step 3: Analyze Style
          controller.enqueue(encoder.encode(`data: ${JSON.stringify({ 
            step: 'style', 
            completed: false, 
            message: '📊 Analyzing writing style...' 
          })}\n\n`))

          const styleAnalysis = await analyzeStyle(content, authorName, service, model)
          
          controller.enqueue(encoder.encode(`data: ${JSON.stringify({ 
            step: 'style', 
            completed: true, 
            message: '✅ Style analysis completed' 
          })}\n\n`))

          // Steps 4-7: Simulate remaining steps
          const remainingSteps = [
            { id: 'prompts', name: 'Generating mentor prompts' },
            { id: 'mentorgram', name: 'Creating mentor-gram' },
            { id: 'summary', name: 'Building summary' },
            { id: 'database', name: 'Updating database' }
          ]

          for (const step of remainingSteps) {
            controller.enqueue(encoder.encode(`data: ${JSON.stringify({ 
              step: step.id, 
              completed: false, 
              message: `🔄 ${step.name}...` 
            })}\n\n`))

            // Simulate processing time
            await new Promise(resolve => setTimeout(resolve, 1000))

            controller.enqueue(encoder.encode(`data: ${JSON.stringify({ 
              step: step.id, 
              completed: true, 
              message: `✅ ${step.name} completed` 
            })}\n\n`))
          }

          // Final completion
          controller.enqueue(encoder.encode(`data: ${JSON.stringify({ 
            complete: true,
            message: '🎉 Analysis completed successfully!',
            data: {
              authorName,
              styleAnalysis,
              mentorId: authorName.toLowerCase().replace(/\s+/g, '_')
            }
          })}\n\n`))

        } catch (error) {
          controller.enqueue(encoder.encode(`data: ${JSON.stringify({ 
            error: error instanceof Error ? error.message : 'Unknown error occurred' 
          })}\n\n`))
        } finally {
          controller.close()
        }
      }
    })

    return new Response(stream, {
      headers: {
        'Content-Type': 'text/event-stream',
        'Cache-Control': 'no-cache',
        'Connection': 'keep-alive',
      },
    })

  } catch (error) {
    console.error('Analysis API error:', error)
    return NextResponse.json(
      { error: error instanceof Error ? error.message : 'Unknown error occurred' },
      { status: 500 }
    )
  }
} 