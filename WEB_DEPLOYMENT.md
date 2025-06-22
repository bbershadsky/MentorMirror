# MentorMirror Web Deployment Guide

This guide explains how to deploy the web version of MentorMirror to Vercel as a Next.js application.

## 🌐 Components Deployed to Vercel

The following components from the original PyQt desktop application have been converted for web deployment:

### ✅ **Converted Components**

1. **Frontend UI** → **Next.js React Application**
   - Modern, responsive web interface using shadcn/ui components
   - Real-time progress tracking with animated indicators
   - Console output display and interactive controls
   - Mobile-friendly responsive design

2. **Content Scraping** → **Serverless API Route** (`/api/analyze`)
   - URL content extraction using Cheerio
   - PDF processing capabilities (limited in serverless environment)
   - Author name inference using AI
   - Writing style analysis

3. **Text Rewriting** → **Serverless API Route** (`/api/rewrite`)
   - Style emulation using OpenAI/Google AI APIs
   - Preserve tone functionality
   - Real-time text transformation

4. **Text-to-Speech** → **Serverless API Route** (`/api/tts`)
   - ElevenLabs API integration
   - Voice mapping for specific mentors
   - Audio streaming to browser

5. **Mentor Management** → **Serverless API Route** (`/api/mentors`)
   - In-memory mentor database (can be upgraded to persistent storage)
   - Voice availability checking
   - Mentor CRUD operations

### ❌ **Components Not Deployed** (Desktop-Only)

1. **Local File Processing** - Limited in serverless environment
2. **PyQt6 GUI Components** - Replaced with React components
3. **Local Database Files** - Replaced with API-based storage
4. **Desktop Audio Playback** - Replaced with web audio APIs

## 🚀 Deployment Steps

### 1. **Environment Variables Setup**

Set these environment variables in your Vercel dashboard:

```bash
OPENAI_API_KEY=sk-your-openai-key
GOOGLE_API_KEY=your-google-ai-key
ELEVENLABS_API_KEY=your-elevenlabs-key
```

### 2. **Vercel Deployment**

#### Option A: Deploy via Vercel CLI
```bash
# Install Vercel CLI
npm i -g vercel

# Deploy to Vercel
vercel --prod
```

#### Option B: Deploy via GitHub Integration
1. Push your code to GitHub
2. Connect your repository to Vercel
3. Configure environment variables
4. Deploy automatically on push

### 3. **Domain Configuration**

Configure your custom domain in Vercel dashboard:
- Add your domain
- Configure DNS settings
- Enable HTTPS (automatic)

## 🛠 Technical Architecture

### **Frontend (Next.js App Router)**
```
app/
├── globals.css          # Global styles with shadcn/ui variables
├── layout.tsx          # Root layout component
├── page.tsx            # Main application page
└── api/                # Serverless API routes
    ├── analyze/        # Content analysis endpoint
    ├── mentors/        # Mentor management endpoint
    ├── rewrite/        # Text rewriting endpoint
    └── tts/            # Text-to-speech endpoint
```

### **API Routes (Serverless Functions)**

#### `/api/analyze` - Content Analysis
- **Input**: URL, AI service, model
- **Output**: Streaming analysis progress
- **Features**: Real-time progress updates, author detection, style analysis

#### `/api/rewrite` - Text Rewriting
- **Input**: Text, mentor ID, AI service, model
- **Output**: Rewritten text in mentor's style
- **Features**: Preserve tone option, style application

#### `/api/tts` - Text-to-Speech
- **Input**: Text, mentor ID
- **Output**: Audio stream (MP3)
- **Features**: ElevenLabs integration, voice mapping

#### `/api/mentors` - Mentor Management
- **Methods**: GET (list), POST (create)
- **Features**: Voice availability checking, mentor CRUD

### **Key Libraries & Dependencies**

```json
{
  "next": "^14.0.0",
  "react": "^18.2.0",
  "openai": "^4.20.0",
  "@google/generative-ai": "^0.2.1",
  "cheerio": "^1.1.0",
  "axios": "^1.10.0",
  "@radix-ui/react-*": "Various shadcn/ui components",
  "tailwindcss": "^3.3.6",
  "framer-motion": "^10.16.16"
}
```

## 🎨 UI Components (shadcn/ui)

The web version uses modern, accessible UI components:

- **Cards** - Organized content sections
- **Buttons** - Interactive elements with loading states
- **Progress Bars** - Real-time analysis tracking
- **Select Dropdowns** - AI service and mentor selection
- **Textareas** - Text input and output
- **Checkboxes** - Configuration options
- **Badges** - Status indicators
- **Toast Notifications** - User feedback

## 🔧 Configuration Files

### **next.config.js**
```javascript
module.exports = {
  experimental: {
    serverComponentsExternalPackages: ['playwright', 'cheerio']
  },
  env: {
    OPENAI_API_KEY: process.env.OPENAI_API_KEY,
    GOOGLE_API_KEY: process.env.GOOGLE_API_KEY,
    ELEVENLABS_API_KEY: process.env.ELEVENLABS_API_KEY,
  }
}
```

### **vercel.json**
```json
{
  "framework": "nextjs",
  "functions": {
    "app/api/**/*.ts": {
      "maxDuration": 60
    }
  }
}
```

## 📱 Features & Capabilities

### **Web-Specific Enhancements**
1. **Responsive Design** - Works on desktop, tablet, and mobile
2. **Real-time Updates** - Server-sent events for progress tracking
3. **Modern UI** - Clean, accessible interface with dark mode support
4. **Fast Loading** - Optimized with Next.js App Router
5. **SEO Optimized** - Meta tags and structured data

### **Maintained Features from Desktop**
1. **Content Analysis** - URL scraping and style analysis
2. **Text Rewriting** - AI-powered style emulation
3. **Voice Synthesis** - Text-to-speech with mentor voices
4. **Progress Tracking** - Real-time workflow monitoring
5. **Multiple AI Providers** - OpenAI and Google AI support

## 🔒 Security Considerations

1. **API Keys** - Stored securely in Vercel environment variables
2. **CORS** - Configured for secure cross-origin requests
3. **Rate Limiting** - Built-in Vercel function limits
4. **Input Validation** - Server-side validation for all inputs
5. **Error Handling** - Comprehensive error catching and logging

## 📈 Performance Optimizations

1. **Serverless Functions** - Auto-scaling and efficient resource usage
2. **Streaming Responses** - Real-time progress updates
3. **Optimized Bundle** - Tree-shaking and code splitting
4. **CDN Distribution** - Global edge network via Vercel
5. **Caching** - Intelligent caching strategies

## 🚨 Limitations & Considerations

### **Serverless Limitations**
1. **Execution Time** - 60-second maximum for API routes
2. **Memory Limits** - 1GB maximum memory per function
3. **Cold Starts** - Initial request latency
4. **File Storage** - No persistent file system

### **Web Browser Limitations**
1. **Local Files** - Cannot process local files directly
2. **Large Files** - Limited by browser memory
3. **Audio Playback** - Browser-dependent audio support

## 🔄 Migration from Desktop

To migrate from the desktop version:

1. **Export Mentors** - Extract mentor data from desktop app
2. **Update URLs** - Change from local file paths to web URLs
3. **Configure APIs** - Set up API keys in Vercel
4. **Test Functionality** - Verify all features work in web environment

## 📞 Support & Troubleshooting

### **Common Issues**

1. **API Key Errors** - Verify environment variables in Vercel
2. **Timeout Issues** - Check function execution limits
3. **Audio Playback** - Ensure browser supports audio formats
4. **CORS Errors** - Verify API route configurations

### **Debug Tools**

1. **Vercel Logs** - Check function execution logs
2. **Browser Console** - Monitor client-side errors
3. **Network Tab** - Inspect API requests/responses

## 🎯 Future Enhancements

1. **Database Integration** - Persistent mentor storage
2. **User Authentication** - Personal mentor collections
3. **Batch Processing** - Multiple URL analysis
4. **Advanced Analytics** - Usage tracking and insights
5. **Mobile App** - React Native version

---

## 🚀 Quick Start

1. Clone the repository
2. Install dependencies: `npm install`
3. Set environment variables
4. Run locally: `npm run dev`
5. Deploy to Vercel: `vercel --prod`

The web version provides all the core functionality of the desktop application in a modern, scalable, and accessible web interface! 