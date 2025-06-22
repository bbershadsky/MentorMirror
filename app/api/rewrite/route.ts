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
  'winston_churchill': {
    styleAnalysis: {
      tone_voice: 'Commanding, inspirational, and deeply authoritative with classical eloquence',
      sentence_structure: 'Powerful, rhythmic sentences with parallel structure and dramatic pauses',
      vocabulary_diction: 'Rich, formal language with historical references and classical allusions',
      rhetorical_patterns: 'Uses metaphor, repetition, and crescendo to build emotional impact',
      unique_elements: 'Masterful use of tricolon, alliteration, and biblical cadences',
      content_themes: 'Leadership, democracy, freedom, history, and moral courage',
      audience_engagement: 'Direct appeals to shared values, dramatic imagery, and calls to action'
    }
  },
  'abraham_lincoln': {
    styleAnalysis: {
      tone_voice: 'Humble yet profound, with measured dignity and moral clarity',
      sentence_structure: 'Carefully balanced sentences with biblical rhythm and legal precision',
      vocabulary_diction: 'Simple, accessible language elevated by metaphor and biblical references',
      rhetorical_patterns: 'Uses parallelism, antithesis, and careful logical progression',
      unique_elements: 'Folksy wisdom combined with constitutional gravitas',
      content_themes: 'Unity, justice, democracy, moral obligation, and national purpose',
      audience_engagement: 'Appeals to shared humanity and common moral ground'
    }
  },
  'charlie_munger': {
    styleAnalysis: {
      tone_voice: 'Direct, pragmatic, and often bluntly honest with dry wit',
      sentence_structure: 'Short, punchy statements mixed with longer explanatory passages',
      vocabulary_diction: 'Business terminology combined with folksy wisdom and mental models',
      rhetorical_patterns: 'Uses analogies, historical examples, and inversion thinking',
      unique_elements: 'Frequent references to psychology, incentives, and human folly',
      content_themes: 'Investing, psychology, business principles, and rational thinking',
      audience_engagement: 'Challenges conventional wisdom with contrarian insights'
    }
  },
  'morgan_freeman': {
    styleAnalysis: {
      tone_voice: 'Warm, authoritative, and deeply resonant with natural gravitas',
      sentence_structure: 'Flowing, measured sentences with natural pauses and emphasis',
      vocabulary_diction: 'Clear, accessible language with occasional poetic flourishes',
      rhetorical_patterns: 'Uses storytelling, gentle wisdom, and universal truths',
      unique_elements: 'Narrator-like quality with philosophical undertones',
      content_themes: 'Human nature, wisdom, life lessons, and universal experiences',
      audience_engagement: 'Creates intimate connection through shared understanding'
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
  },
  'andrew_tate': {
    styleAnalysis: {
      tone_voice: 'Aggressive, confident, and provocative with alpha male energy',
      sentence_structure: 'Short, declarative statements with emphasis and repetition',
      vocabulary_diction: 'Direct, often crude language mixed with business terminology',
      rhetorical_patterns: 'Uses personal anecdotes, challenges, and controversial statements',
      unique_elements: 'Frequent use of superlatives and absolute statements',
      content_themes: 'Success, masculinity, wealth, and self-improvement',
      audience_engagement: 'Confrontational style designed to provoke and motivate'
    }
  },
  'john_f_kennedy': {
    styleAnalysis: {
      tone_voice: 'Inspirational, optimistic, and charismatic with youthful energy',
      sentence_structure: 'Rhythmic, balanced sentences with memorable parallel structure',
      vocabulary_diction: 'Elevated but accessible language with classical references',
      rhetorical_patterns: 'Uses antithesis, alliteration, and calls to action',
      unique_elements: 'Boston accent influence and memorable phraseology',
      content_themes: 'Progress, service, democracy, and American idealism',
      audience_engagement: 'Inspirational appeals to shared values and collective action'
    }
  },
  'dr_seuss': {
    styleAnalysis: {
      tone_voice: 'Playful, whimsical, and imaginative with childlike wonder',
      sentence_structure: 'Rhythmic, rhyming patterns with simple sentence structures',
      vocabulary_diction: 'Simple words, made-up terms, and creative wordplay',
      rhetorical_patterns: 'Uses repetition, rhyme, and fantastical imagery',
      unique_elements: 'Nonsense words, anapestic tetrameter, and moral lessons',
      content_themes: 'Imagination, acceptance, perseverance, and life lessons',
      audience_engagement: 'Appeals to inner child and universal human experiences'
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