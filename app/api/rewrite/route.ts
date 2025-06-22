import { NextRequest, NextResponse } from 'next/server'
import { OpenAI } from 'openai'
import { GoogleGenerativeAI } from '@google/generative-ai'

interface RewriteRequest {
  text: string
  mentorId: string
  service: 'openai' | 'google'
  model: string
  preserveTone?: boolean
}

// Initialize AI clients
const openai = process.env.OPENAI_API_KEY ? new OpenAI({
  apiKey: process.env.OPENAI_API_KEY,
}) : null

const genai = process.env.GOOGLE_API_KEY ? new GoogleGenerativeAI(process.env.GOOGLE_API_KEY) : null

// Mock mentor database - in real app this would be from a database
const mentorsDatabase: { [key: string]: any } = {
  'paul_graham': {
    styleAnalysis: {
      tone_voice: 'Analytical, thoughtful, and direct with a conversational yet authoritative tone',
      sentence_structure: 'Mix of short, punchy sentences and longer, complex explanations',
      vocabulary_diction: 'Technical startup terminology combined with accessible language',
      rhetorical_patterns: 'Uses concrete examples, analogies, and logical progression',
      unique_elements: 'Frequent use of parenthetical remarks and numbered lists',
      content_themes: 'Startups, technology, programming, venture capital, and entrepreneurship',
      audience_engagement: 'Direct address to readers, rhetorical questions, and practical advice'
    }
  },
  'eminem': {
    styleAnalysis: {
      tone_voice: 'Intense, raw, and emotionally charged with rapid-fire delivery',
      sentence_structure: 'Complex rhyme schemes, internal rhymes, and rhythmic patterns',
      vocabulary_diction: 'Street language mixed with sophisticated wordplay and metaphors',
      rhetorical_patterns: 'Storytelling through personal experiences and social commentary',
      unique_elements: 'Multi-syllabic rhymes, alliteration, and controversial content',
      content_themes: 'Personal struggles, social issues, hip-hop culture, and redemption',
      audience_engagement: 'Direct confrontation, emotional vulnerability, and provocative statements'
    }
  }
}

async function rewriteText(
  userText: string, 
  styleAnalysis: any, 
  service: string, 
  model: string,
  preserveTone: boolean = false
): Promise<string> {
  const styleDescription = JSON.stringify(styleAnalysis, null, 2)

  const prompt = preserveTone 
    ? `You are an expert writing style editor. Your task is to preserve the user's original text exactly as written, but present it as if spoken by someone with this specific style and voice:

**STYLE ANALYSIS:**
---
${styleDescription}
---

**USER TEXT (preserve exactly, but present in the mentor's voice):**
---
${userText}
---

**INSTRUCTIONS:**
- Keep the exact same words and meaning
- Present it as if the mentor is saying these exact words
- Add the mentor's characteristic tone and delivery style
- Do not change the core message or content

**RESULT:**`
    : `You are an expert writing style editor. Your task is to rewrite the "USER TEXT" provided below so that it matches the style defined in the "STYLE ANALYSIS".

**Key Instructions:**
- **Preserve the Core Message:** The original meaning, message, and key information of the user's text MUST be maintained. Do not add new ideas or remove essential points.
- **Adopt the Style:** Infuse the rewritten text with the specified tone, voice, sentence structure, vocabulary, and rhetorical patterns from the style analysis.
- **Be Subtle:** The goal is a natural-sounding text, not a caricature. The style should be adopted seamlessly.

**STYLE ANALYSIS:**
---
${styleDescription}
---

**USER TEXT:**
---
${userText}
---

**REWRITTEN TEXT (in the mentor's style):**`

  try {
    if (service === 'openai' && openai) {
      const response = await openai.chat.completions.create({
        model,
        messages: [{ role: 'user', content: prompt }],
        max_tokens: 1000,
        temperature: 0.7,
      })
      
      return response.choices[0]?.message?.content?.trim() || 'Failed to rewrite text'
    } else if (service === 'google' && genai) {
      const genModel = genai.getGenerativeModel({ model })
      const result = await genModel.generateContent(prompt)
      const response = await result.response
      return response.text().trim()
    } else {
      throw new Error('AI service not configured')
    }
  } catch (error) {
    console.error('Rewrite error:', error)
    throw new Error(`Text rewriting failed: ${error instanceof Error ? error.message : 'Unknown error'}`)
  }
}

export async function POST(req: NextRequest) {
  try {
    const body: RewriteRequest = await req.json()
    const { text, mentorId, service, model, preserveTone = false } = body

    if (!text || !mentorId) {
      return NextResponse.json(
        { error: 'Text and mentor ID are required' },
        { status: 400 }
      )
    }

    // Get mentor style analysis
    const mentor = mentorsDatabase[mentorId]
    if (!mentor) {
      return NextResponse.json(
        { error: 'Mentor not found' },
        { status: 404 }
      )
    }

    const rewrittenText = await rewriteText(
      text,
      mentor.styleAnalysis,
      service,
      model,
      preserveTone
    )

    return NextResponse.json({
      rewrittenText,
      mentorId,
      originalText: text,
      preserveTone
    })

  } catch (error) {
    console.error('Rewrite API error:', error)
    return NextResponse.json(
      { error: error instanceof Error ? error.message : 'Unknown error occurred' },
      { status: 500 }
    )
  }
} 