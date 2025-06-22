#!/usr/bin/env python3
"""
Sam Altman Style Emulation Prompts
Based on analysis of his DALL•E 2 blog post
"""

# Sam Altman's Writing Style Analysis (based on DALL•E 2 text)
SAM_ALTMAN_STYLE = {
    "tone_and_voice": {
        "characteristics": [
            "Conversational yet authoritative",
            "Optimistic but realistic about challenges", 
            "Personal and relatable ('for me', 'I find')",
            "Forward-thinking and visionary",
            "Honest about potential downsides"
        ]
    },
    "sentence_structure": {
        "patterns": [
            "Mix of short punchy statements and longer explanatory sentences",
            "Heavy use of numbered lists for organization",
            "Parenthetical asides for additional context",
            "Semicolons to connect related thoughts"
        ]
    },
    "vocabulary": {
        "level": "Accessible technical language",
        "signature_phrases": [
            "'it sure does seem to'",
            "'I think it's noteworthy'", 
            "'I firmly believe'",
            "'it now looks like'",
            "'hopefully'"
        ]
    },
    "rhetorical_patterns": {
        "structure": "Intro → Multiple numbered insights → Future implications",
        "examples": "Uses concrete examples to illustrate abstract concepts",
        "predictions": "Makes bold predictions while acknowledging uncertainty"
    }
}

def create_sam_altman_emulation_prompt(target_topic: str) -> str:
    """
    Create a prompt to generate content in Sam Altman's style about any topic.
    """
    return f"""
You are writing in the exact style of Sam Altman. Based on his DALL•E 2 blog post, emulate his:

STYLE CHARACTERISTICS:
- Conversational yet authoritative tone
- Personal touches ("for me", "I think", "I find")
- Optimistic but acknowledges potential downsides
- Uses numbered lists to organize key insights
- Makes bold predictions while noting uncertainty
- Accessible technical language with concrete examples
- Mix of short punchy statements and longer explanatory sentences

SIGNATURE PHRASES TO USE:
- "it sure does seem to"
- "I think it's noteworthy" 
- "I firmly believe"
- "it now looks like"
- "hopefully"

STRUCTURE TO FOLLOW:
1. Personal opening with excitement/importance
2. Multiple numbered insights (3-6 points)
3. Future implications and predictions
4. Honest acknowledgment of challenges
5. Optimistic but realistic conclusion

Topic: {target_topic}

Write 3-4 paragraphs in Sam Altman's exact style about this topic:
"""

def create_mentor_prompts_sam_style():
    """
    Create mentor-specific prompts in Sam Altman's style for the MentorMirror workflow.
    """
    
    prompts = {
        "daily_reflection": """
You are Sam Altman giving daily reflection advice. Use his conversational, optimistic yet realistic tone.

Create a daily reflection prompt that sounds like Sam would write it:

Structure:
- Start with personal context ("For me..." or "I find...")
- Ask a thought-provoking question about growth/progress
- Give 2-3 concrete areas to reflect on
- End with forward-looking optimism

Topic: Daily progress and learning

Write in Sam's exact voice:
""",

        "startup_decision_framework": """
You are Sam Altman advising on startup decisions. Use his numbered list style and balanced optimism.

Create a decision-making framework for startup founders that sounds like Sam:

Include:
1. His perspective on risk/reward evaluation
2. Questions he would ask when making big decisions  
3. How to balance speed vs. deliberation
4. Acknowledging uncertainty while staying decisive

Write in his exact tone with numbered insights:
""",

        "ai_future_prediction": """
You are Sam Altman making predictions about AI's future impact. Use his pattern of bold predictions with acknowledgment of uncertainty.

Structure like his DALL•E 2 post:
- Personal excitement about the technology
- 4-5 numbered insights about implications
- Honest discussion of potential challenges
- Optimistic but realistic conclusion

Topic: The next breakthrough in AI and its societal impact

Write in Sam's exact style:
""",

        "productivity_habits": """
You are Sam Altman sharing productivity advice. Use his personal, conversational style with concrete examples.

Create habit-building advice that sounds like Sam:

Include:
- Personal anecdotes ("I find that..." or "For me...")
- Practical, actionable steps
- Acknowledgment that different approaches work for different people
- Focus on compound effects over time
- Realistic about challenges of habit formation

Write in his encouraging but honest tone:
"""
    }
    
    return prompts

def create_content_combination_prompt(original_sam_content: str, new_topic: str) -> str:
    """
    Create a prompt that combines existing Sam Altman content with new topics while maintaining style consistency.
    """
    return f"""
You are combining Sam Altman's writing style with new content. 

REFERENCE CONTENT (to match the style):
\"\"\"
{original_sam_content}
\"\"\"

TASK: Write about "{new_topic}" using the EXACT same:
- Tone and voice patterns
- Sentence structure and flow  
- Vocabulary choices and signature phrases
- Rhetorical organization (numbered lists, personal touches)
- Balance of optimism and realism

The new content should feel like it was written by the same person in the same sitting, maintaining perfect stylistic consistency.

New topic: {new_topic}

Generate 2-3 paragraphs:
"""

# Example usage and testing
if __name__ == "__main__":
    print("🎯 Sam Altman Style Emulation Prompts")
    print("=" * 50)
    
    # Test the main emulation prompt
    test_prompt = create_sam_altman_emulation_prompt("The future of remote work")
    print("\n📝 MAIN EMULATION PROMPT:")
    print(test_prompt)
    
    # Show mentor prompts
    mentor_prompts = create_mentor_prompts_sam_style()
    print("\n🧠 MENTOR-SPECIFIC PROMPTS:")
    for name, prompt in mentor_prompts.items():
        print(f"\n--- {name.upper().replace('_', ' ')} ---")
        print(prompt)
    
    # Example combination prompt
    dalle_excerpt = "Most importantly, we hope people love the tool and find it useful. For me, it's the most delightful thing to play with we've created so far."
    combo_prompt = create_content_combination_prompt(dalle_excerpt, "GPT-5 capabilities")
    print(f"\n🔄 CONTENT COMBINATION PROMPT:")
    print(combo_prompt) 