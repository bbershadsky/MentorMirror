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
import re
import argparse
from typing import Dict, List, Any, Optional
from pathlib import Path

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv

# Import our custom modules
from style_emulation_system import StyleEmulator

load_dotenv()

# Updated paths to use mentors folder
MENTORS_BASE_PATH = "mentors"
STYLE_DB_PATH = os.path.join(MENTORS_BASE_PATH, "styles")
SESSIONS_PATH = os.path.join(MENTORS_BASE_PATH, "sessions") 
MENTORS_DB_FILE = os.path.join(MENTORS_BASE_PATH, "mentors.json")

def safe_filename(name: str) -> str:
    """Create a safe, lowercase filename from a string."""
    name = name.lower().replace(" ", "_")
    return re.sub(r'[^a-z0-9_\-]', '', name)

def ensure_mentors_structure():
    """Ensure the mentors folder structure exists."""
    os.makedirs(MENTORS_BASE_PATH, exist_ok=True)
    os.makedirs(STYLE_DB_PATH, exist_ok=True)
    os.makedirs(SESSIONS_PATH, exist_ok=True)

def load_mentors_db() -> Dict[str, Any]:
    """Load the mentors database."""
    if os.path.exists(MENTORS_DB_FILE):
        try:
            with open(MENTORS_DB_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return {}
    return {}

def save_mentors_db(mentors_db: Dict[str, Any]) -> bool:
    """Save the mentors database."""
    try:
        with open(MENTORS_DB_FILE, 'w', encoding='utf-8') as f:
            json.dump(mentors_db, f, indent=2, ensure_ascii=False)
        return True
    except IOError:
        return False

def get_unique_author_name(base_name: str, mentors_db: Dict[str, Any]) -> str:
    """Generate a unique author name, handling duplicates with numerical suffixes."""
    if base_name.lower() != "unknown author":
        return base_name
    
    # For "Unknown Author", find the next available number
    counter = 1
    while True:
        candidate_name = f"Unknown Author {counter}"
        safe_candidate = safe_filename(candidate_name)
        
        # Check if this name already exists in the database
        if safe_candidate not in mentors_db:
            return candidate_name
        counter += 1

def validate_json_file(file_path: str, min_size: int = 50) -> bool:
    """Validate that a JSON file exists, is not empty, and contains valid JSON."""
    if not os.path.exists(file_path):
        return False
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            if len(content) < min_size:
                return False
            data = json.loads(content)
            return isinstance(data, (dict, list)) and len(str(data)) > min_size
    except (json.JSONDecodeError, IOError):
        return False

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
        ensure_mentors_structure()
        
    def setup_session(self, mentor_name: str) -> str:
        """Create a session directory for this mentor analysis."""
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        self.output_dir = os.path.join(SESSIONS_PATH, f"session_{safe_filename(mentor_name)}_{timestamp}")
        os.makedirs(self.output_dir, exist_ok=True)
        return self.output_dir
    
    def load_mentor_content(self, file_path: str) -> str:
        """Load mentor content from a file."""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Content file not found: {file_path}")
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()

    def infer_author_from_content(self, content: str) -> str:
        """Infer the author name from the scraped content."""
        print("🔍 Step 1/5: Inferring author name from content...")
        try:
            author_name = self.style_emulator.infer_author_name(content)
            
            # Handle duplicate unknown authors
            if author_name.lower() == "unknown author":
                mentors_db = load_mentors_db()
                author_name = get_unique_author_name(author_name, mentors_db)
            
            print(f"✅ Inferred author: {author_name}")
            return author_name
        except Exception as e:
            print(f"❌ Error inferring author name: {e}")
            # Generate unique unknown author name
            mentors_db = load_mentors_db()
            return get_unique_author_name("Unknown Author", mentors_db)
    
    def analyze_mentor_style(self, content: str, mentor_name: str) -> Optional[Dict[str, Any]]:
        """Analyze the mentor's writing style and save to the central store."""
        print("📊 Step 2/5: Analyzing writing style...")
        try:
            style_analysis = self.style_emulator.analyze_writing_style(content, mentor_name)
            
            # Save to both session directory and central store
            safe_name = safe_filename(mentor_name)
            
            # Session directory
            if self.output_dir:
                session_analysis_path = os.path.join(self.output_dir, "style_analysis.json")
                with open(session_analysis_path, 'w', encoding='utf-8') as f:
                    json.dump(style_analysis, f, indent=2, ensure_ascii=False)
            
            # Central store
            central_analysis_path = os.path.join(STYLE_DB_PATH, f"{safe_name}.json")
            with open(central_analysis_path, 'w', encoding='utf-8') as f:
                json.dump(style_analysis, f, indent=2, ensure_ascii=False)
            
            # Validate the file was created properly
            if validate_json_file(central_analysis_path):
                print(f"✅ Style analysis completed and saved")
                return style_analysis
            else:
                print(f"❌ Style analysis file validation failed")
                return None
                
        except Exception as e:
            print(f"❌ Error analyzing style: {e}")
            return None

    def generate_mentor_prompts(self, style_analysis: Dict[str, Any], mentor_name: str) -> Optional[Dict[str, str]]:
        """Generate mentor-specific prompts."""
        print("🎯 Step 3/5: Generating mentor prompts...")
        try:
            prompts = self.style_emulator.create_mentor_style_prompts(style_analysis)
            
            if self.output_dir:
                prompts_path = os.path.join(self.output_dir, "mentor_prompts.json")
                with open(prompts_path, 'w', encoding='utf-8') as f:
                    json.dump(prompts, f, indent=2, ensure_ascii=False)
                
                if validate_json_file(prompts_path):
                    print(f"✅ Mentor prompts generated and saved")
                    return prompts
                else:
                    print(f"❌ Mentor prompts file validation failed")
                    return None
            
        except Exception as e:
            print(f"❌ Error generating mentor prompts: {e}")
            return None

    def generate_daily_mentorgram(self, style_analysis: Dict[str, Any], mentor_name: str, topic: str = None) -> Optional[Dict[str, str]]:
        """Generate a daily 'Mentor-gram'."""
        print("📧 Step 4/5: Generating daily Mentor-gram...")
        
        try:
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
            
            quote_prompt = f"Generate an inspirational quote that {mentor_name} would say about '{topic}'. Use their exact writing style and voice. Make it personal and actionable."
            action_prompt = f"Based on {mentor_name}'s style and thinking, suggest one concrete action someone could take today related to '{topic}'. Write it in their voice."
            reflection_prompt = f"Create a self-reflection question that {mentor_name} would ask about '{topic}'. Use their style of inquiry and make it thought-provoking."
            
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
            
            if self.output_dir:
                mentorgram_path = os.path.join(self.output_dir, f"mentorgram_{mentorgram['date']}.json")
                with open(mentorgram_path, 'w', encoding='utf-8') as f:
                    json.dump(mentorgram, f, indent=2, ensure_ascii=False)
                
                if validate_json_file(mentorgram_path):
                    print(f"✅ Mentor-gram generated and saved")
                    return mentorgram
                else:
                    print(f"❌ Mentor-gram file validation failed")
                    return None
            
        except Exception as e:
            print(f"❌ Error generating mentor-gram: {e}")
            return None

    def create_session_summary(self, mentor_name: str, style_analysis: Dict[str, Any], mentorgram: Dict[str, str], prompts: Dict[str, str]) -> Optional[Dict[str, Any]]:
        """Create a comprehensive session summary."""
        print("📄 Step 5/5: Creating session summary...")
        
        try:
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
                    f"mentorgram_{mentorgram['date']}.json",
                    "session_summary.json"
                ],
                "validation_status": {
                    "style_analysis": "✅ Valid",
                    "mentor_prompts": "✅ Valid", 
                    "mentorgram": "✅ Valid",
                    "session_summary": "✅ Valid"
                }
            }
            
            if self.output_dir:
                summary_path = os.path.join(self.output_dir, "session_summary.json")
                with open(summary_path, 'w', encoding='utf-8') as f:
                    json.dump(summary, f, indent=2, ensure_ascii=False)
                
                if validate_json_file(summary_path):
                    print(f"✅ Session summary created and saved")
                    return summary
                else:
                    print(f"❌ Session summary file validation failed")
                    return None
                    
        except Exception as e:
            print(f"❌ Error creating session summary: {e}")
            return None

    def update_mentors_database(self, mentor_name: str, session_summary: Dict[str, Any]) -> bool:
        """Update the central mentors database."""
        try:
            mentors_db = load_mentors_db()
            safe_name = safe_filename(mentor_name)
            
            mentors_db[safe_name] = {
                "display_name": mentor_name,
                "safe_name": safe_name,
                "last_updated": datetime.datetime.now().isoformat(),
                "style_file": f"{safe_name}.json",
                "session_directory": self.output_dir,
                "status": "active"
            }
            
            if save_mentors_db(mentors_db):
                print(f"✅ Mentors database updated")
                return True
            else:
                print(f"❌ Failed to update mentors database")
                return False
                
        except Exception as e:
            print(f"❌ Error updating mentors database: {e}")
            return False

    def run_complete_analysis(self, content_file: str) -> Dict[str, Any]:
        """Run the complete analysis workflow."""
        results = {
            "success": False,
            "mentor_name": None,
            "errors": [],
            "completed_steps": []
        }
        
        try:
            # Load content
            content = self.load_mentor_content(content_file)
            print(f"📖 Loaded content from: {content_file}")
            
            # Step 1: Infer author name
            mentor_name = self.infer_author_from_content(content)
            results["mentor_name"] = mentor_name
            results["completed_steps"].append("author_inference")
            
            # Setup session directory
            session_dir = self.setup_session(mentor_name)
            print(f"📁 Session directory: {session_dir}")
            
            # Step 2: Analyze style
            style_analysis = self.analyze_mentor_style(content, mentor_name)
            if not style_analysis:
                results["errors"].append("Style analysis failed")
                return results
            results["completed_steps"].append("style_analysis")
            
            # Step 3: Generate prompts
            prompts = self.generate_mentor_prompts(style_analysis, mentor_name)
            if not prompts:
                results["errors"].append("Mentor prompts generation failed")
                return results
            results["completed_steps"].append("mentor_prompts")
            
            # Step 4: Generate mentorgram
            mentorgram = self.generate_daily_mentorgram(style_analysis, mentor_name)
            if not mentorgram:
                results["errors"].append("Mentor-gram generation failed")
                return results
            results["completed_steps"].append("mentorgram")
            
            # Step 5: Create session summary
            summary = self.create_session_summary(mentor_name, style_analysis, mentorgram, prompts)
            if not summary:
                results["errors"].append("Session summary creation failed")
                return results
            results["completed_steps"].append("session_summary")
            
            # Update mentors database
            if self.update_mentors_database(mentor_name, summary):
                results["completed_steps"].append("database_update")
            else:
                results["errors"].append("Database update failed")
            
            results["success"] = True
            print(f"\n🎉 Complete analysis finished successfully!")
            print(f"📊 Mentor '{mentor_name}' added to database")
            
        except Exception as e:
            results["errors"].append(f"Critical error: {e}")
            print(f"❌ Critical error in complete analysis: {e}")
        
        return results

    def load_style_analysis(self, mentor_name: str) -> Optional[Dict[str, Any]]:
        """Load a style analysis file from the central store."""
        safe_name = safe_filename(mentor_name)
        analysis_path = os.path.join(STYLE_DB_PATH, f"{safe_name}.json")
        if os.path.exists(analysis_path):
            with open(analysis_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return None

    def rewrite_text_with_style(self, user_text: str, style_analysis: dict) -> str:
        """Rewrites user text using the provided style analysis."""
        print("✍️ Rewriting text in mentor's style...")
        rewritten_text = self.style_emulator.rewrite_text_in_style(user_text, style_analysis)
        print("✅ Text rewriting complete.")
        return rewritten_text

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
    parser = argparse.ArgumentParser(description="MentorMirror Pipeline: Analyze, Generate, and Rewrite Content.")
    parser.add_argument("--service", type=str, default="openai", choices=["openai", "google"], help="AI service to use")
    parser.add_argument("--model", type=str, default="gpt-4o-mini", help="Model name to use")
    
    # Subparsers for different actions
    subparsers = parser.add_subparsers(dest="action", required=True)

    # Action: Complete Analysis
    parser_complete = subparsers.add_parser("complete", help="Run complete analysis workflow from scraped content.")
    parser_complete.add_argument("--content-file", required=True, help="Path to the scraped text file.")

    # Action: Rewrite
    parser_rewrite = subparsers.add_parser("rewrite", help="Rewrite text in a mentor's style.")
    parser_rewrite.add_argument("--mentor-name", required=True, help="Name of the mentor style to use.")
    parser_rewrite.add_argument("--input-text", required=True, help="Text to rewrite.")

    args = parser.parse_args()

    print(f"🧠 MentorMirror Pipeline - Service: {args.service.capitalize()}, Model: {args.model}")
    print("=" * 60)
    
    mentor_mirror = MentorMirror(service=args.service, model_name=args.model)

    if args.action == "complete":
        print(f"🎬 Action: Complete Analysis Workflow")
        results = mentor_mirror.run_complete_analysis(args.content_file)
        
        print(f"\n📊 Results Summary:")
        print(f"   Success: {results['success']}")
        print(f"   Mentor: {results['mentor_name']}")
        print(f"   Completed Steps: {', '.join(results['completed_steps'])}")
        if results['errors']:
            print(f"   Errors: {', '.join(results['errors'])}")

    elif args.action == "rewrite":
        print(f"🎬 Action: Rewrite text in the style of '{args.mentor_name}'")
        style_analysis = mentor_mirror.load_style_analysis(args.mentor_name)
        if not style_analysis:
            print(f"❌ Error: Style analysis for '{args.mentor_name}' not found in '{STYLE_DB_PATH}'.")
            print("   Please run the 'complete' action first.")
            return
        
        rewritten_text = mentor_mirror.rewrite_text_with_style(args.input_text, style_analysis)
        print("\n--- REWRITTEN TEXT ---")
        print(rewritten_text)
        print("--------------------")

    print("\n🎉 MentorMirror action complete!")

if __name__ == "__main__":
    asyncio.run(main()) 