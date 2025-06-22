import { NextRequest, NextResponse } from 'next/server'

interface TTSRequest {
  text: string
  mentorId: string
}

// Voice mappings for specific mentors
const VOICE_MAPPINGS: { [key: string]: string } = {
  'eminem': 'Xlpccr56K0lJCUlWyRFz',
  'winston_churchill': 'm5qbXI0CgAFzPG5UoMRP',
  'andrew_tate': 'dWpPffaVSc5yhGXUqsnc',
  'john_f_kennedy': '0s2PKBiONhElJhZwfnGL',
}

function getVoiceId(mentorId: string): string | null {
  // Try multiple variations to find voice mapping
  const mentorVariations = [
    mentorId.toLowerCase(),
    mentorId.toLowerCase().replace(' ', '_'),
    mentorId.toLowerCase().replace('_', ' ')
  ]
  
  for (const variation of mentorVariations) {
    if (variation in VOICE_MAPPINGS) {
      return VOICE_MAPPINGS[variation]
    }
  }
  
  return null
}

async function generateSpeech(text: string, voiceId: string): Promise<ArrayBuffer> {
  const apiKey = process.env.ELEVENLABS_API_KEY
  if (!apiKey) {
    throw new Error('ElevenLabs API key not configured')
  }

  const url = `https://api.elevenlabs.io/v1/text-to-speech/${voiceId}`
  
  const response = await fetch(url, {
    method: 'POST',
    headers: {
      'Accept': 'audio/mpeg',
      'Content-Type': 'application/json',
      'xi-api-key': apiKey
    },
    body: JSON.stringify({
      text,
      model_id: 'eleven_monolingual_v1',
      voice_settings: {
        stability: 0.5,
        similarity_boost: 0.5
      }
    })
  })

  if (!response.ok) {
    const errorText = await response.text()
    throw new Error(`ElevenLabs API error: ${response.status} - ${errorText}`)
  }

  return response.arrayBuffer()
}

export async function POST(req: NextRequest) {
  try {
    const body: TTSRequest = await req.json()
    const { text, mentorId } = body

    if (!text || !mentorId) {
      return NextResponse.json(
        { error: 'Text and mentor ID are required' },
        { status: 400 }
      )
    }

    // Get voice ID for the mentor
    const voiceId = getVoiceId(mentorId)
    if (!voiceId) {
      return NextResponse.json(
        { error: 'Voice not available for this mentor' },
        { status: 404 }
      )
    }

    // Generate speech
    const audioBuffer = await generateSpeech(text, voiceId)

    // Return audio as response
    return new Response(audioBuffer, {
      headers: {
        'Content-Type': 'audio/mpeg',
        'Content-Length': audioBuffer.byteLength.toString(),
      },
    })

  } catch (error) {
    console.error('TTS API error:', error)
    return NextResponse.json(
      { error: error instanceof Error ? error.message : 'Unknown error occurred' },
      { status: 500 }
    )
  }
} 