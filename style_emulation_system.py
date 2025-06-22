#!/usr/bin/env python3
"""
Style Emulation System - Analyze and emulate author writing styles
Based on the MentorMirror concept from IDEA.md
"""

import json
import re
from typing import Dict, Any
from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI
from dotenv import load_dotenv

load_dotenv()

class StyleEmulator:
    def __init__(self, service: str = "openai", model_name: str = "gpt-4o-mini"):
        """Initializes the style emulator with a specific model."""
        if service.lower() == "google":
            self.llm = ChatGoogleGenerativeAI(model=model_name, temperature=0.7)
        else: # default to openai
            self.llm = ChatOpenAI(model=model_name, temperature=0.7)
    
    def analyze_writing_style(self, text: str, author_name: str = "Unknown") -> Dict[str, Any]:
        """
        Analyze the writing style, tone, and patterns of a given text.
        """
        analysis_prompt = f"""
        You are a literary style analyst. Analyze the following text by {author_name} and extract:

        1. **Tone & Voice**: Describe the overall tone (formal/casual, optimistic/pessimistic, etc.)
        2. **Sentence Structure**: Analyze sentence length, complexity, use of lists/bullets
        3. **Vocabulary & Diction**: Level of technical language, common word choices, jargon
        4. **Rhetorical Patterns**: How they present arguments, use of examples, storytelling style
        5. **Unique Stylistic Elements**: Signature phrases, punctuation habits, paragraph structure
        6. **Content Themes**: What topics/concepts they frequently discuss
        7. **Audience Engagement**: How they connect with readers (direct address, questions, etc.)

        Text to analyze:
        \"\"\"
        {text}
        \"\"\"

        Return your analysis as a structured JSON with the above categories as keys.
        """
        
        response = self.llm.invoke(analysis_prompt)
        
        try:
            # Try to extract JSON from the response
            json_match = re.search(r'```json\s*(\{.*?\})\s*```', response.content, re.DOTALL)
            if json_match:
                return json.loads(json_match.group(1))
            else:
                # If no JSON blocks, try to parse the whole response
                return json.loads(response.content)
        except json.JSONDecodeError:
            # Fallback: return as structured text
            return {
                "analysis": response.content,
                "raw_response": True
            }

    def infer_author_name(self, text: str) -> str:
        """
        Attempt to infer the author's name from the content.
        """
        inference_prompt = f"""
        Analyze the following text and try to determine who the author is based on:
        - Any self-references or mentions of their own name
        - Writing style and topics that might indicate a specific well-known author
        - Any biographical details or personal anecdotes mentioned
        - The overall voice and perspective

        Text to analyze:
        \"\"\"
        {text[:2000]}...
        \"\"\"

        Return ONLY the author's name (first and last name if available). If you cannot determine the author with reasonable confidence, return "Unknown Author".
        """
        
        try:
            response = self.llm.invoke(inference_prompt)
            author_name = response.content.strip().strip('"').strip("'")
            
            # Basic validation - should be a reasonable name
            if len(author_name) > 50 or len(author_name.split()) > 4:
                return "Unknown Author"
            
            return author_name if author_name else "Unknown Author"
        except Exception:
            return "Unknown Author"
    
    def create_style_emulation_prompt(self, style_analysis: Dict[str, Any], target_topic: str) -> str:
        """
        Create a prompt that can generate content in the analyzed style.
        """
        if style_analysis.get("raw_response"):
            style_description = style_analysis["analysis"]
        else:
            style_description = json.dumps(style_analysis, indent=2)
        
        emulation_prompt = f"""
        You are a writing style emulator. Based on the following style analysis, write content about "{target_topic}" that matches this exact writing style:

        STYLE ANALYSIS:
        {style_description}

        INSTRUCTIONS:
        - Match the tone, sentence structure, and vocabulary patterns exactly
        - Use the same rhetorical approaches and stylistic elements
        - Maintain the same level of technical language and audience engagement
        - Include similar content themes where relevant
        - Keep the same paragraph structure and flow

        Topic to write about: {target_topic}

        Generate 2-3 paragraphs in this style:
        """
        
        return emulation_prompt
    
    def rewrite_text_in_style(self, user_text: str, style_analysis: dict) -> str:
        """
        Rewrites the user's text to match the mentor's style.
        """
        if style_analysis.get("raw_response"):
            style_description = style_analysis["analysis"]
        else:
            style_description = json.dumps(style_analysis, indent=2)

        rewrite_prompt = f"""
        You are an expert writing style editor. Your task is to rewrite the "USER TEXT" provided below so that it matches the style defined in the "STYLE ANALYSIS".

        **Key Instructions:**
        - **Preserve the Core Message:** The original meaning, message, and key information of the user's text MUST be maintained. Do not add new ideas or remove essential points.
        - **Adopt the Style:** Infuse the rewritten text with the specified tone, voice, sentence structure, vocabulary, and rhetorical patterns from the style analysis.
        - **Be Subtle:** The goal is a natural-sounding text, not a caricature. The style should be adopted seamlessly.

        **STYLE ANALYSIS:**
        ---
        {style_description}
        ---

        **USER TEXT:**
        ---
        {user_text}
        ---

        **REWRITTEN TEXT (in the mentor's style):**
        """
        response = self.llm.invoke(rewrite_prompt)
        return response.content

    def generate_styled_content(self, style_analysis: Dict[str, Any], target_topic: str) -> str:
        """
        Generate content in the analyzed style about a target topic.
        """
        prompt = self.create_style_emulation_prompt(style_analysis, target_topic)
        response = self.llm.invoke(prompt)
        return response.content
    
    def create_mentor_style_prompts(self, style_analysis: Dict[str, Any]) -> Dict[str, str]:
        """
        Create specialized prompts for different mentor use cases based on IDEA.md workflow.
        """
        base_style = json.dumps(style_analysis, indent=2) if not style_analysis.get("raw_response") else style_analysis["analysis"]
        
        prompts = {
            "daily_reflection": f"""
            Based on this writing style analysis:
            {base_style}
            
            Generate a daily reflection prompt that sounds like this author would write it. Include:
            1. A thought-provoking question in their voice
            2. A brief context or example in their style
            3. An actionable step for self-improvement
            """,
            
            "decision_framework": f"""
            Using this writing style:
            {base_style}
            
            Create a decision-making framework that sounds like this author. Include:
            1. Key principles they would emphasize
            2. Questions they would ask when making decisions
            3. Their approach to weighing tradeoffs
            """,
            
            "habit_formation": f"""
            In the style of this analysis:
            {base_style}
            
            Generate advice for building good habits that matches their tone and approach:
            1. Their perspective on habit formation
            2. Practical steps in their voice
            3. How they would motivate someone to stay consistent
            """,
            
            "problem_solving": f"""
            Using this writing style:
            {base_style}
            
            Create a problem-solving methodology in their voice:
            1. How they would approach breaking down complex problems
            2. Their method for generating solutions
            3. Their approach to implementation and iteration
            """
        }
        
        return prompts

if __name__ == "__main__":
    print("StyleEmulator module loaded. Use this class in other scripts for style analysis and emulation.") 