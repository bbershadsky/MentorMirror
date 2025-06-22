#!/usr/bin/env python3
"""
Marcus Aurelius Style Demo
Using the extracted Meditations PDF to create a philosophical mentor
"""

import asyncio
import json
from style_emulation_system import StyleEmulator
from mentor_mirror_pipeline import MentorMirror

async def main():
    print("🏛️  Marcus Aurelius Meditations Style Analysis")
    print("=" * 60)
    
    # Initialize the system
    mentor_mirror = MentorMirror()
    
    # Setup session for Marcus Aurelius
    mentor_name = "Marcus Aurelius"
    session_dir = mentor_mirror.setup_session(mentor_name)
    print(f"📁 Session directory: {session_dir}")
    
    # Load the extracted Meditations content
    # Get the most recent extraction directory
    import os
    import glob
    
    # Find the most recent Marcus Aurelius extraction
    meditations_dirs = glob.glob("maximusveritas_*")
    if not meditations_dirs:
        print("❌ No Marcus Aurelius extractions found. Please run:")
        print("   python url2txts.py https://www.maximusveritas.com/wp-content/uploads/2017/09/Marcus-Aurelius-Meditations.pdf")
        return
    
    latest_dir = max(meditations_dirs)
    meditations_file = os.path.join(latest_dir, "marcus-aurelius-meditations-pdf.txt")
    
    if not os.path.exists(meditations_file):
        print(f"❌ Meditations file not found: {meditations_file}")
        return
    
    print(f"📖 Loading Meditations from: {meditations_file}")
    
    # Read a sample of the meditations (first 10,000 characters for analysis)
    with open(meditations_file, 'r', encoding='utf-8') as f:
        full_content = f.read()
    
    # Extract a representative sample for style analysis
    # Skip the introduction and get to the actual meditations
    sample_start = full_content.find("THE FIRST BOOK")
    if sample_start == -1:
        sample_start = 2000  # Skip first pages if marker not found
    
    # Take a substantial sample for analysis
    sample_content = full_content[sample_start:sample_start+15000]
    
    print(f"📏 Analyzing {len(sample_content)} characters from the Meditations...")
    
    # Analyze Marcus Aurelius' philosophical style
    style_analysis = mentor_mirror.analyze_mentor_style(sample_content, mentor_name)
    
    # Generate philosophical mentor prompts
    mentor_prompts = mentor_mirror.generate_mentor_prompts(style_analysis, mentor_name)
    
    # Generate a daily philosophical reflection in Marcus' style
    meditations_topics = [
        "facing adversity with wisdom",
        "the nature of virtue and duty", 
        "accepting what cannot be changed",
        "finding inner peace",
        "the transience of life",
        "serving the common good"
    ]
    
    import random
    chosen_topic = random.choice(meditations_topics)
    
    philosophical_reflection = mentor_mirror.generate_daily_mentorgram(
        style_analysis, 
        mentor_name, 
        chosen_topic
    )
    
    print(f"\n🏛️  Daily Philosophical Reflection from Marcus Aurelius")
    print("=" * 70)
    print(f"📅 Date: {philosophical_reflection['date']}")
    print(f"🎯 Meditation Topic: {philosophical_reflection['topic']}")
    print(f"\n💭 Stoic Wisdom:")
    print(f'   "{philosophical_reflection["quote"]}"')
    print(f"\n🎯 Daily Practice:")
    print(f"   {philosophical_reflection['action']}")
    print(f"\n🤔 Self-Examination:")
    print(f"   {philosophical_reflection['reflection']}")
    print("=" * 70)
    
    # Generate new philosophical content in Marcus' style
    modern_topics = [
        "dealing with digital distractions in the modern world",
        "finding wisdom in times of uncertainty", 
        "maintaining virtue in competitive environments",
        "the role of technology in human flourishing"
    ]
    
    modern_topic = random.choice(modern_topics)
    print(f"\n✨ Generating Marcus Aurelius' perspective on: '{modern_topic}'")
    
    modern_meditation = mentor_mirror.generate_styled_content(
        style_analysis,
        modern_topic,
        mentor_name
    )
    
    print(f"\n📜 Modern Meditation in Marcus Aurelius' Style:")
    print("-" * 50)
    print(modern_meditation[:500] + "..." if len(modern_meditation) > 500 else modern_meditation)
    
    # Create session summary
    summary = mentor_mirror.create_session_summary(mentor_name, style_analysis, philosophical_reflection)
    
    print(f"\n🎉 Marcus Aurelius philosophical analysis complete!")
    print(f"📊 Files created in: {session_dir}")
    print(f"📏 Original text analyzed: {len(sample_content):,} characters")
    print(f"📄 Style elements captured: {len(style_analysis)} categories")

if __name__ == "__main__":
    asyncio.run(main()) 