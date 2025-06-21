import asyncio
import os
import sys
import datetime
import json
import re
import argparse
from typing import Any, List
from urllib.parse import urljoin, urlparse

from dotenv import load_dotenv
load_dotenv()

from langchain_openai import ChatOpenAI
from browser_use import Agent

def safe_filename(name: str) -> str:
    """Create a safe filename from a string."""
    name = name.lower().replace(" ", "-").replace("/", "-").replace(".", "-")
    return re.sub(r'[^a-z0-9_\-]', '', name)[:50]

def get_domain_name(url: str) -> str:
    """Extract a clean domain name from URL for folder naming."""
    parsed = urlparse(url)
    domain = parsed.netloc.lower()
    # Remove www. prefix
    if domain.startswith('www.'):
        domain = domain[4:]
    # Remove common TLDs for cleaner names
    domain = domain.replace('.com', '').replace('.org', '').replace('.net', '')
    return safe_filename(domain)

def setup_output_directory(base_url: str) -> str:
    """Create and return the output directory path based on the domain."""
    domain_name = get_domain_name(base_url)
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    output_dir = f"{domain_name}_{timestamp}"
    os.makedirs(output_dir, exist_ok=True)
    return output_dir

def clean_content(content: str) -> str:
    """Remove code block markers and clean up content."""
    if isinstance(content, str):
        # Remove markdown code block markers
        content = re.sub(r'^```[a-zA-Z]*\n?', '', content, flags=re.MULTILINE)
        content = re.sub(r'\n?```$', '', content, flags=re.MULTILINE)
        content = content.strip()
    return content

def save_content(content: Any, section_name: str, output_dir: str) -> bool:
    """Parse the content from the agent and save HTML, text, and JSON files."""
    try:
        html_content = ""
        text_content = ""
        json_content = None

        print(f"🔍 Processing content for '{section_name}':")
        print(f"   Content type: {type(content)}")
        
        # Show size info for large content
        content_size = len(str(content))
        print(f"   Content size: {content_size} characters")
        print(f"   Content preview: {str(content)[:200]}...")

        # Handle string content (most common case)
        if isinstance(content, str):
            # Clean the content first
            content = clean_content(content)
            
            try:
                # Try to parse as JSON
                parsed_content = json.loads(content)
                json_content = parsed_content
                content = parsed_content
            except json.JSONDecodeError:
                # It's raw text/HTML
                if content.strip().startswith("<"):
                    html_content = content
                else:
                    text_content = content

        # Handle dictionary content
        if isinstance(content, dict):
            json_content = content
            
            # Check if it's chunked content
            if content.get("extraction_method") == "chunked":
                # Handle chunked content specially
                text_content = content.get("combined_text", "")
                
                # Also save individual chunks
                chunks_dir = os.path.join(output_dir, f"{section_name}_chunks")
                os.makedirs(chunks_dir, exist_ok=True)
                
                for i, chunk in enumerate(content.get("chunks", []), 1):
                    chunk_filename = f"chunk_{i}.json"
                    chunk_path = os.path.join(chunks_dir, chunk_filename)
                    with open(chunk_path, "w", encoding="utf-8") as f:
                        json.dump(chunk, f, indent=2, ensure_ascii=False)
                print(f"💾 Saved {len(content.get('chunks', []))} individual chunks to {chunks_dir}")
            else:
                # Look for common content keys
                html_content = content.get("html", content.get("html_content", ""))
                text_content = content.get("text", content.get("text_content", content.get("plain_text", "")))
                
                # If not found, try to extract from nested structures
                if not html_content and not text_content:
                    # Look for any nested dictionary that might contain content
                    for key, value in content.items():
                        if isinstance(value, dict):
                            html_content = value.get("html", "")
                            text_content = value.get("text", "")
                            if html_content or text_content:
                                break
                        elif isinstance(value, str) and len(value) > 100:  # Likely content
                            text_content = value
                            break
                
                # If still no content, convert the whole dict to text
                if not html_content and not text_content:
                    text_content = json.dumps(content, indent=2)

        if not (html_content or text_content or json_content):
            print(f"⚠️  Could not extract content for section '{section_name}'.")
            return False

        filename_base = safe_filename(section_name)
        saved_files = []
        
        # Save JSON content if it exists
        if json_content:
            json_path = os.path.join(output_dir, f"{filename_base}.json")
            with open(json_path, "w", encoding="utf-8") as f_json:
                json.dump(json_content, f_json, indent=2, ensure_ascii=False)
            print(f"✅ Saved JSON for '{section_name}': {json_path}")
            saved_files.append("JSON")
        
        # Save HTML content if it exists
        if html_content:
            html_path = os.path.join(output_dir, f"{filename_base}.html")
            with open(html_path, "w", encoding="utf-8") as f_html:
                f_html.write(html_content)
            print(f"✅ Saved HTML for '{section_name}': {html_path}")
            saved_files.append("HTML")

        # Save text content if it exists
        if text_content:
            text_path = os.path.join(output_dir, f"{filename_base}.txt")
            with open(text_path, "w", encoding="utf-8") as f_txt:
                f_txt.write(text_content)
            print(f"✅ Saved text for '{section_name}': {text_path}")
            saved_files.append("TXT")

        print(f"📄 Saved formats: {', '.join(saved_files)}")
        return True

    except Exception as e:
        print(f"❌ Error saving content for section '{section_name}': {e}")
        return False

async def discover_sections(base_url: str, llm) -> List[str]:
    """Discover all relevant sections/pages to scrape from the base URL."""
    print(f"🔍 Discovering sections from: {base_url}")
    
    task = f"""Go to {base_url} and analyze the page to find all relevant sections or pages that should be scraped. 
    Look for navigation links, section links, or any other relevant content pages.
    Return a JSON list of URLs that should be scraped."""
    
    try:
        agent = Agent(task=task, llm=llm)
        history = await agent.run(max_steps=5)
        
        # Try to extract discovered sections from the agent's output
        sections = []
        history_steps = history.history if hasattr(history, 'history') else history
        
        for step in reversed(history_steps):
            if not hasattr(step, 'result') or not isinstance(step.result, list):
                continue
                
            for action_result in step.result:
                if hasattr(action_result, 'extracted_content') and action_result.extracted_content:
                    try:
                        content = action_result.extracted_content
                        content = clean_content(content)
                        if isinstance(content, str):
                            content = json.loads(content)
                        if isinstance(content, list):
                            sections = content
                            break
                    except:
                        continue
            if sections:
                break
        
        # If auto-discovery failed, just use the base URL
        if not sections:
            print("⚠️  Auto-discovery failed, using base URL only")
            sections = [base_url]
        
        print(f"📋 Discovered {len(sections)} sections: {sections}")
        return sections
        
    except Exception as e:
        print(f"❌ Error discovering sections: {e}")
        # Fallback: just scrape the base URL
        return [base_url]

async def extract_content_from_url(url: str, section_name: str, llm, max_steps: int = 8) -> Any:
    """Extract content from a single URL using a dedicated agent."""
    print(f"\n🚀 Extracting content from: {url}")
    
    # First try with normal extraction
    task = f"""Go to {url}. Wait for the page to load completely (wait at least 3 seconds), then use the `extract_content` action to get the main content of the page. 
    Extract both HTML and text content. Make sure to return the actual page content, not a summary or description of what you did.
    If the content is very long, focus on the most important parts first."""
    
    try:
        agent = Agent(task=task, llm=llm)
        history = await agent.run(max_steps=max_steps)
        
        # Look for extracted content in the history
        history_steps = history.history if hasattr(history, 'history') else history
        
        # First, look for the raw extracted JSON content in the logs
        # Sometimes the content is in the step's log messages
        for step in reversed(history_steps):
            if hasattr(step, 'result') and isinstance(step.result, list):
                for action_result in step.result:
                    # Check if this action result contains JSON content
                    if hasattr(action_result, 'extracted_content'):
                        raw_content = action_result.extracted_content
                        if isinstance(raw_content, str):
                            # Look for JSON patterns in the content
                            json_match = re.search(r'```json\s*(\{.*?\})\s*```', raw_content, re.DOTALL)
                            if json_match:
                                try:
                                    parsed_json = json.loads(json_match.group(1))
                                    if isinstance(parsed_json, dict) and len(str(parsed_json)) > 500:
                                        print(f"✅ Found JSON content in extract_content logs")
                                        return parsed_json
                                except json.JSONDecodeError:
                                    pass
        
        # Second, look specifically for extract_content action results
        for step in reversed(history_steps):
            if not hasattr(step, 'result') or not isinstance(step.result, list):
                continue
                
            for action_result in step.result:
                # Check if this is an extract_content action with substantial content
                if hasattr(action_result, 'extracted_content') and action_result.extracted_content:
                    content = action_result.extracted_content
                    
                    # Clean the content
                    if isinstance(content, str):
                        content = clean_content(content)
                    
                    # Filter out agent summaries and error messages - be more specific
                    if isinstance(content, str):
                        content_lower = content.lower()
                        
                        # Skip if it's clearly an agent summary (more specific filtering)
                        if (content.startswith("The task was successfully completed") or
                            content.startswith("Successfully extracted") or
                            content.startswith("The main content of") or
                            content.startswith("The page") or
                            "task completed" in content_lower or
                            "was extracted successfully" in content_lower or
                            "404 error" in content_lower or
                            "does not exist" in content_lower or
                            "cannot be completed" in content_lower or
                            len(content) < 200):
                            continue
                        
                        # Try to parse as JSON (the good content is usually JSON)
                        try:
                            parsed_content = json.loads(content)
                            if isinstance(parsed_content, dict) and len(str(parsed_content)) > 500:
                                print(f"✅ Found JSON content from extract_content")
                                return parsed_content
                        except json.JSONDecodeError:
                            pass
                        
                        # If it's a long string that's not a summary, keep it
                        if len(content) > 500:
                            print(f"✅ Found substantial text content from extract_content")
                            return content
                    
                    # If it's already a dict/object, use it
                    elif isinstance(content, (dict, list)) and len(str(content)) > 200:
                        print(f"✅ Found structured content from extract_content")
                        return content
                
                # Also check for action_type to specifically target extract_content actions
                if (hasattr(action_result, 'action_type') and 
                    action_result.action_type == 'extract_content' and
                    hasattr(action_result, 'result')):
                    content = action_result.result
                    
                    if isinstance(content, str):
                        content = clean_content(content)
                        # Try to parse as JSON
                        try:
                            parsed_content = json.loads(content)
                            if isinstance(parsed_content, dict) and len(str(parsed_content)) > 500:
                                print(f"✅ Found JSON content from extract_content action result")
                                return parsed_content
                        except json.JSONDecodeError:
                            pass
                    
                    if content and len(str(content)) > 200:
                        print(f"✅ Found content from extract_content action result")
                        return content
        
        # If no good extract_content found, look for other substantial content
        for step in reversed(history_steps):
            if not hasattr(step, 'result') or not isinstance(step.result, list):
                continue
                
            for action_result in step.result:
                # Skip done actions entirely to avoid summaries
                if (hasattr(action_result, 'action_type') and 
                    action_result.action_type == 'done'):
                    continue
                
                # Check for any substantial content that's not a summary
                for attr in ['content', 'text', 'result']:
                    if hasattr(action_result, attr):
                        content = getattr(action_result, attr)
                        if isinstance(content, str):
                            content = clean_content(content)
                        
                        if content and isinstance(content, str) and len(content) > 500:
                            # Skip obvious summaries (more comprehensive filtering)
                            if not (content.startswith("The task was successfully completed") or
                                   content.startswith("Successfully") or 
                                   content.startswith("The page") or
                                   content.startswith("The main content of") or
                                   "task completed" in content.lower() or
                                   "was extracted successfully" in content.lower() or
                                   "extracted" in content.lower()[:100]):
                                print(f"✅ Found substantial content via attribute '{attr}'")
                                return content
        
        print(f"⚠️  No substantial content extracted from {url}")
        return None
        
    except Exception as e:
        error_msg = str(e)
        print(f"⚠️  Agent error: {error_msg}")
        
        # Check if it's the string_too_long validation error
        if "string_too_long" in error_msg and "10000 characters" in error_msg:
            print(f"🔄 Content too long for single extraction, trying chunked approach...")
            return await extract_content_chunked(url, section_name, llm, max_steps)
        else:
            print(f"❌ Error extracting content from {url}: {e}")
            return None

async def extract_content_chunked(url: str, section_name: str, llm, max_steps: int = 8) -> Any:
    """Extract content in chunks when the content is too large for single extraction."""
    print(f"📄 Attempting chunked extraction from: {url}")
    
    # Try to extract in smaller, focused chunks
    chunks = []
    chunk_tasks = [
        "Extract the title, author, and introduction/first few paragraphs",
        "Extract the main body content, focusing on key points and arguments", 
        "Extract any conclusions, final thoughts, or call-to-action sections",
        "Extract any additional metadata like publication date, tags, or related links"
    ]
    
    for i, chunk_task in enumerate(chunk_tasks, 1):
        try:
            print(f"  📝 Extracting chunk {i}/{len(chunk_tasks)}: {chunk_task}")
            
            task = f"""Go to {url}. Wait for the page to load completely, then use the `extract_content` action to {chunk_task}.
            Keep the response concise and focused. Return only the requested content, not a summary."""
            
            agent = Agent(task=task, llm=llm)
            history = await agent.run(max_steps=min(max_steps, 6))  # Reduce steps for chunks
            
            # Extract content from this chunk
            history_steps = history.history if hasattr(history, 'history') else history
            chunk_content = None
            
            for step in reversed(history_steps):
                if not hasattr(step, 'result') or not isinstance(step.result, list):
                    continue
                    
                for action_result in step.result:
                    if hasattr(action_result, 'extracted_content') and action_result.extracted_content:
                        content = action_result.extracted_content
                        if isinstance(content, str):
                            content = clean_content(content)
                            
                        # Skip obvious summaries and errors
                        if isinstance(content, str) and len(content) > 50:
                            if not (content.startswith("Successfully") or 
                                   content.startswith("The page") or
                                   "extracted" in content.lower()[:50]):
                                chunk_content = content
                                break
                        elif isinstance(content, (dict, list)):
                            chunk_content = content
                            break
                
                if chunk_content:
                    break
            
            if chunk_content:
                chunks.append({
                    f"chunk_{i}": chunk_content,
                    "description": chunk_task
                })
                print(f"  ✅ Chunk {i} extracted successfully")
            else:
                print(f"  ⚠️  Chunk {i} extraction failed")
                
        except Exception as e:
            print(f"  ❌ Error extracting chunk {i}: {e}")
            continue
    
    if chunks:
        # Combine all chunks into a structured result
        combined_content = {
            "url": url,
            "extraction_method": "chunked",
            "total_chunks": len(chunks),
            "chunks": chunks
        }
        
        # Also try to create a flattened text version
        text_parts = []
        for chunk in chunks:
            for key, value in chunk.items():
                if key != "description":
                    if isinstance(value, str):
                        text_parts.append(value)
                    elif isinstance(value, dict):
                        text_parts.append(json.dumps(value, indent=2))
        
        if text_parts:
            combined_content["combined_text"] = "\n\n".join(text_parts)
        
        print(f"✅ Successfully extracted {len(chunks)} chunks")
        return combined_content
    else:
        print(f"❌ Failed to extract any chunks from {url}")
        return None

async def main():
    parser = argparse.ArgumentParser(description="Universal web scraper using browser-use")
    parser.add_argument(
        "url",
        help="URL to scrape (required)"
    )
    parser.add_argument(
        "--sections",
        nargs="*",
        help="Specific sections/URLs to scrape (if not provided, will auto-discover or use base URL)"
    )
    parser.add_argument(
        "--steps",
        type=int,
        default=8,
        help="Max steps per section (default: 8)"
    )
    parser.add_argument(
        "--discover",
        action="store_true",
        help="Auto-discover sections from the base URL"
    )
    
    args = parser.parse_args()

    base_url = args.url
    output_dir = setup_output_directory(base_url)
    print(f"📁 Output directory: {output_dir}")

    try:
        llm = ChatOpenAI(model='gpt-4o-mini')
    except Exception as e:
        print(f"❌ Error setting up LLM: {e}")
        return

    parsed_url = urlparse(base_url)
    base_domain = f"{parsed_url.scheme}://{parsed_url.netloc}"
    
    # Determine sections to scrape
    if args.sections:
        sections = args.sections
        print(f"📋 Using provided sections: {sections}")
    elif args.discover:
        sections = await discover_sections(base_url, llm)
    else:
        # Just use the base URL
        sections = [base_url]
        print(f"📋 Using base URL: {sections}")

    saved_count = 0

    for i, section in enumerate(sections, 1):
        # Construct full URL and section name
        if section.startswith('http'):
            url = section
            section_name = urlparse(section).path.split('/')[-1] or f"page_{i}"
        else:
            # Handle relative URLs
            if not section.startswith('/'):
                section = '/' + section
            url = urljoin(base_domain, section)
            section_name = section.split('/')[-1] or f"page_{i}"
        
        # Clean up section name
        if not section_name or section_name in ['', '/']:
            section_name = f"page_{i}"
        
        print("\n" + "="*80)
        print(f"🚀 Processing section {i}/{len(sections)}: '{section_name}'")
        print(f"📍 URL: {url}")
        print("="*80)

        content = await extract_content_from_url(url, section_name, llm, args.steps)
        
        if content:
            if save_content(content, section_name, output_dir):
                saved_count += 1
        else:
            print(f"⚠️  No content extracted for section '{section_name}'")

    print("\n" + "="*80)
    print("✅ Scraping complete!")
    print(f"📊 Total sections saved: {saved_count}/{len(sections)}")
    print(f"📁 Check the '{output_dir}' directory for saved files.")
    print("="*80)
    
    # List saved files
    try:
        files = os.listdir(output_dir)
        if files:
            print("📄 Saved files:")
            for file in sorted(files):
                file_path = os.path.join(output_dir, file)
                size = os.path.getsize(file_path)
                print(f"   {file} ({size} bytes)")
        else:
            print("⚠️  No files were saved.")
    except Exception as e:
        print(f"❌ Error listing files: {e}")
    
    print(f"\n🎉 Content saved to: {output_dir}")

if __name__ == "__main__":
    asyncio.run(main())

