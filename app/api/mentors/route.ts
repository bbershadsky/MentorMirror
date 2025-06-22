import { NextResponse } from 'next/server'

// Voice mappings for specific mentors
const VOICE_MAPPINGS: { [key: string]: string } = {
  'eminem': 'Xlpccr56K0lJCUlWyRFz',
  'winston_churchill': 'm5qbXI0CgAFzPG5UoMRP',
  'andrew_tate': 'dWpPffaVSc5yhGXUqsnc',
  'john_f_kennedy': '0s2PKBiONhElJhZwfnGL',
}

// In a real application, this would be stored in a database
// For the demo, we'll use in-memory storage with mentors from the desktop version
let mentorsDatabase: { [key: string]: any } = {
  'paul_graham': {
    id: 'paul_graham',
    name: 'paul_graham',
    displayName: 'Paul Graham',
    status: 'active',
    hasVoice: false,
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
    id: 'winston_churchill',
    name: 'winston_churchill',
    displayName: 'Winston Churchill',
    status: 'active',
    hasVoice: true,
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
    id: 'abraham_lincoln',
    name: 'abraham_lincoln',
    displayName: 'Abraham Lincoln',
    status: 'active',
    hasVoice: false,
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
    id: 'charlie_munger',
    name: 'charlie_munger',
    displayName: 'Charlie Munger',
    status: 'active',
    hasVoice: false,
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
    id: 'morgan_freeman',
    name: 'morgan_freeman',
    displayName: 'Morgan Freeman',
    status: 'active',
    hasVoice: false,
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
    id: 'eminem',
    name: 'eminem',
    displayName: 'Eminem',
    status: 'active',
    hasVoice: true,
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
    id: 'andrew_tate',
    name: 'andrew_tate',
    displayName: 'Andrew Tate',
    status: 'active',
    hasVoice: true,
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
    id: 'john_f_kennedy',
    name: 'john_f_kennedy',
    displayName: 'John F. Kennedy',
    status: 'active',
    hasVoice: true,
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
    id: 'dr_seuss',
    name: 'dr_seuss',
    displayName: 'Dr. Seuss',
    status: 'active',
    hasVoice: false,
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

function checkVoiceAvailability(mentorId: string): boolean {
  // Check if mentor has voice mapping
  const mentorVariations = [
    mentorId.toLowerCase(),
    mentorId.toLowerCase().replace(' ', '_'),
    mentorId.toLowerCase().replace('_', ' ')
  ]
  
  return mentorVariations.some(variation => variation in VOICE_MAPPINGS)
}

export async function GET() {
  try {
    // Convert database to array format expected by frontend
    const mentorsArray = Object.values(mentorsDatabase).map(mentor => ({
      id: mentor.id,
      name: mentor.name,
      displayName: mentor.displayName,
      status: mentor.status,
      hasVoice: checkVoiceAvailability(mentor.id)
    }))

    return NextResponse.json(mentorsArray)
  } catch (error) {
    console.error('Error fetching mentors:', error)
    return NextResponse.json(
      { error: 'Failed to fetch mentors' },
      { status: 500 }
    )
  }
}

export async function POST(req: Request) {
  try {
    const { authorName, styleAnalysis, mentorId } = await req.json()

    if (!authorName || !styleAnalysis || !mentorId) {
      return NextResponse.json(
        { error: 'Missing required fields' },
        { status: 400 }
      )
    }

    // Add new mentor to database
    mentorsDatabase[mentorId] = {
      id: mentorId,
      name: mentorId,
      displayName: authorName,
      status: 'active',
      hasVoice: checkVoiceAvailability(mentorId),
      styleAnalysis,
      createdAt: new Date().toISOString()
    }

    return NextResponse.json({ 
      success: true, 
      mentor: mentorsDatabase[mentorId] 
    })
  } catch (error) {
    console.error('Error creating mentor:', error)
    return NextResponse.json(
      { error: 'Failed to create mentor' },
      { status: 500 }
    )
  }
} 