import type { Metadata } from 'next'
import { Inter } from 'next/font/google'
import './globals.css'
import { Toaster } from 'sonner'

const inter = Inter({ subsets: ['latin'] })

export const metadata: Metadata = {
  title: 'MentorMirror - AI-Powered Writing Style Emulation',
  description: 'Transform any piece of online content into a personalized writing mentor. Analyze writing styles and apply them to your own text.',
  keywords: ['AI', 'writing', 'style emulation', 'mentorship', 'content analysis'],
  authors: [{ name: 'MentorMirror Team' }],
  openGraph: {
    title: 'MentorMirror - AI-Powered Writing Style Emulation',
    description: 'Transform any piece of online content into a personalized writing mentor.',
    type: 'website',
  },
  twitter: {
    card: 'summary_large_image',
    title: 'MentorMirror - AI-Powered Writing Style Emulation',
    description: 'Transform any piece of online content into a personalized writing mentor.',
  },
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body className={inter.className}>
        {children}
        <Toaster position="bottom-right" />
      </body>
    </html>
  )
} 