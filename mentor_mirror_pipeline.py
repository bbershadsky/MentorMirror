#!/usr/bin/env python3
"""
MentorMirror Complete Pipeline
Integrates url2txts.py + style_emulation_system.py + mentor prompts
Based on IDEA.md workflow
"""

import asyncio
import json
import os
import datetime
from typing import Dict, List, Any, Optional
from pathlib import Path
import argparse

# Add new imports for model selection
import tiktoken
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv

# Import our custom modules
from style_emulation_system import StyleEmulator
from sam_altman_style_prompts import create_sam_altman_emulation_prompt, create_mentor_prompts_sam_style

load_dotenv()

# Define a token limit for switching models
TOKEN_LIMIT_GPT4O_MINI = 120000

class MentorMirror:
    def __init__(self, service: str = "openai", model_name: str = "gpt-4o-mini"):
        """Initializes the pipeline with a specific model."""
        if service.lower() == "google":
            self.llm = ChatGoogleGenerativeAI(model=model_name)
            self.style_emulator = StyleEmulator(service="google", model_name=model_name)
        else:  # default to openai
            self.llm = ChatOpenAI(model=model_name)
            self.style_emulator = StyleEmulator(service="openai", model_name=model_name)
        
        self.output_dir = None
        
    def setup_session(self, mentor_name: str) -> str:
        """Create a session directory for this mentor analysis."""
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        self.output_dir = f"mentor_session_{mentor_name.lower().replace(' ', '_')}_{timestamp}"
        os.makedirs(self.output_dir, exist_ok=True)
        return self.output_dir
    
    async def scrape_mentor_content(self, url: str) -> Optional[str]:
        """
        Scrape content from a mentor's URL using the url2txts system.
        This would integrate with the existing url2txts.py functionality.
        """
        # For now, we'll use existing scraped content
        # In production, this would call the url2txts scraping functions
        print(f"🔍 Scraping content from: {url}")
        print("   (Using existing scraped content for demo)")
        return None
    
    def load_mentor_content(self, file_path: str) -> str:
        """Load mentor content from a file."""
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    
    def analyze_mentor_style(self, content: str, mentor_name: str) -> Dict[str, Any]:
        """Analyze the mentor's writing style."""
        print(f"📊 Analyzing {mentor_name}'s writing style...")
        style_analysis = self.style_emulator.analyze_writing_style(content, mentor_name)
        
        if self.output_dir:
            analysis_path = os.path.join(self.output_dir, "style_analysis.json")
            with open(analysis_path, 'w', encoding='utf-8') as f:
                json.dump(style_analysis, f, indent=2, ensure_ascii=False)
            print(f"✅ Style analysis saved to: {analysis_path}")
        
        return style_analysis
    
    def generate_mentor_prompts(self, style_analysis: Dict[str, Any], mentor_name: str) -> Dict[str, str]:
        """Generate mentor-specific prompts based on style analysis."""
        print(f"🎯 Generating {mentor_name} mentor prompts...")
        
        if mentor_name.lower() == "sam altman":
            prompts = create_mentor_prompts_sam_style()
        else:
            prompts = self.style_emulator.create_mentor_style_prompts(style_analysis)
        
        if self.output_dir:
            prompts_path = os.path.join(self.output_dir, "mentor_prompts.json")
            with open(prompts_path, 'w', encoding='utf-8') as f:
                json.dump(prompts, f, indent=2, ensure_ascii=False)
            print(f"✅ Mentor prompts saved to: {prompts_path}")
        
        return prompts
    
    def generate_daily_mentorgram(self, style_analysis: Dict[str, Any], mentor_name: str, topic: str = None) -> Dict[str, str]:
        """Generate a daily 'Mentor-gram' as specified in IDEA.md."""
        print(f"📧 Generating daily Mentor-gram from {mentor_name}...")
        
        if not topic:
            topics = [
                "building good habits",
                "making hard decisions", 
                "personal growth",
                "overcoming challenges",
                "finding clarity"
            ]
            import random
            topic = random.choice(topics)
        
        # Generate the three components of a Mentor-gram
        quote_prompt = f"""
        Generate an inspirational quote that {mentor_name} would say about "{topic}".
        Use their exact writing style and voice. Make it personal and actionable.
        """
        
        action_prompt = f"""
        Based on {mentor_name}'s style and thinking, suggest one concrete action 
        someone could take today related to "{topic}". Write it in their voice.
        """
        
        reflection_prompt = f"""
        Create a self-reflection question that {mentor_name} would ask about "{topic}".
        Use their style of inquiry and make it thought-provoking.
        """
        
        # Generate each component
        quote = self.llm.invoke(quote_prompt).content
        action = self.llm.invoke(action_prompt).content  
        reflection = self.llm.invoke(reflection_prompt).content
        
        mentorgram = {
            "date": datetime.datetime.now().strftime("%Y-%m-%d"),
            "mentor": mentor_name,
            "topic": topic,
            "quote": quote.strip(),
            "action": action.strip(),
            "reflection": reflection.strip()
        }
        
        # Save Mentor-gram
        if self.output_dir:
            mentorgram_path = os.path.join(self.output_dir, f"mentorgram_{mentorgram['date']}.json")
            with open(mentorgram_path, 'w', encoding='utf-8') as f:
                json.dump(mentorgram, f, indent=2, ensure_ascii=False)
        
        return mentorgram
    
    def generate_styled_content(self, style_analysis: Dict[str, Any], topic: str, mentor_name: str) -> str:
        """Generate new content in the mentor's style."""
        print(f"✨ Generating content in {mentor_name}'s style about '{topic}'...")
        
        if mentor_name.lower() == "sam altman":
            prompt = create_sam_altman_emulation_prompt(topic)
            content = self.llm.invoke(prompt).content
        else:
            content = self.style_emulator.generate_styled_content(style_analysis, topic)
        
        if self.output_dir:
            safe_topic = topic.lower().replace(' ', '_').replace('/', '_')[:30]
            content_path = os.path.join(self.output_dir, f"generated_content_{safe_topic}.txt")
            with open(content_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"✅ Generated content saved to: {content_path}")
        
        return content
    
    def create_session_summary(self, mentor_name: str, style_analysis: Dict[str, Any], mentorgram: Dict[str, str]) -> Dict[str, Any]:
        """Create a summary of the session."""
        summary = {
            "session_info": {
                "mentor": mentor_name,
                "date": datetime.datetime.now().isoformat(),
                "output_directory": self.output_dir
            },
            "style_highlights": {
                "tone": style_analysis.get("Tone & Voice", "Not analyzed"),
                "key_themes": style_analysis.get("Content Themes", []),
                "signature_elements": style_analysis.get("Unique Stylistic Elements", {})
            },
            "daily_mentorgram": mentorgram,
            "files_generated": [
                "style_analysis.json",
                "mentor_prompts.json", 
                f"mentorgram_{mentorgram['date']}.json"
            ]
        }
        
        if self.output_dir:
            summary_path = os.path.join(self.output_dir, "session_summary.json")
            with open(summary_path, 'w', encoding='utf-8') as f:
                json.dump(summary, f, indent=2, ensure_ascii=False)
            print(f"📄 Session summary saved to: {summary_path}")
        
        return summary

def print_mentorgram(mentorgram: Dict[str, str]):
    """Pretty print a Mentor-gram."""
    print(f"\n📧 Daily Mentor-gram from {mentorgram['mentor']}")
    print("=" * 60)
    print(f"📅 Date: {mentorgram['date']}")
    print(f"🎯 Topic: {mentorgram['topic']}")
    print(f"\n💭 Quote:")
    print(f"   \"{mentorgram['quote']}\"")
    print(f"\n🎯 Action:")
    print(f"   {mentorgram['action']}")
    print(f"\n🤔 Reflection:")
    print(f"   {mentorgram['reflection']}")
    print("=" * 60)

async def main():
    """
    Example workflow using Sam Altman's DALL•E 2 content
    """
    parser = argparse.ArgumentParser(description="MentorMirror Pipeline")
    parser.add_argument("--service", type=str, default="openai", choices=["openai", "google"], help="AI service to use")
    parser.add_argument("--model", type=str, default="gpt-4o-mini", help="Model name to use")
    args = parser.parse_args()

    print(f"🧠 MentorMirror Pipeline - Using {args.service} with model {args.model}")
    print("=" * 60)
    
    mentor_mirror = MentorMirror(service=args.service, model_name=args.model)
    
    mentor_name = "Sam Altman"
    session_dir = mentor_mirror.setup_session(mentor_name)
    print(f"📁 Session directory: {session_dir}")
    
    content_file = "blog-samaltman_2025-06-21_19-21-05/dall-star-e-2.txt"
    if not os.path.exists(content_file):
        print(f"⚠️  Content file not found: {content_file}")
        return
        
    mentor_content = mentor_mirror.load_mentor_content(content_file)
    print(f"📖 Loaded content from: {content_file}")
    
    # This will trigger the LLM selection
    style_analysis = mentor_mirror.analyze_mentor_style(mentor_content, mentor_name)
    
    mentor_prompts = mentor_mirror.generate_mentor_prompts(style_analysis, mentor_name)
    
    mentorgram = mentor_mirror.generate_daily_mentorgram(style_analysis, mentor_name)
    print_mentorgram(mentorgram)
    
    new_content = mentor_mirror.generate_styled_content(
        style_analysis,
        "The future of AI in education", 
        mentor_name
    )
    print(f"\n✨ Generated content preview:")
    print(new_content[:300] + "..." if len(new_content) > 300 else new_content)
    
    summary = mentor_mirror.create_session_summary(mentor_name, style_analysis, mentorgram)
    
    print(f"\n🎉 MentorMirror session complete!")
    print(f"📊 Files created in: {session_dir}")
    for file in summary["files_generated"]:
        print(f"   - {file}")

if __name__ == "__main__":
    asyncio.run(main()) 