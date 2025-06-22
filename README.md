# MentorMirror: AI-Powered Writing Style Emulation

MentorMirror is a desktop application that allows you to scrape the writings of your favorite authors, analyze their unique stylistic patterns, and then apply that style to your own text. It's like having a virtual mentor who can instantly show you how to write in their voice.

## Features

- **Intelligent Content Scraping**: Ingest content from any URL (blog posts, articles, and even PDFs).
- **Automatic Author Detection**: Uses AI to automatically infer the author's name from scraped content.
- **Smart Duplicate Handling**: Automatically handles duplicate "Unknown Author" entries with numerical suffixes (Unknown Author 1, Unknown Author 2, etc.).
- **Comprehensive Style Analysis**: Analyzes text for tone, voice, sentence structure, vocabulary, and rhetorical patterns.
- **Complete Workflow Automation**: Generates style analysis, mentor prompts, daily mentor-grams, and session summaries in one go.
- **Organized File Structure**: All mentor data is organized in a clean `mentors/` folder structure.
- **Visual Progress Tracking**: Real-time animated progress indicators show each step of the analysis workflow.
- **Error Handling & Validation**: Robust error detection with comprehensive file validation.
- **Style Rewriting**: Enter your own text and have the application rewrite it in any saved mentor's style.
- **Flexible Model Selection**: Supports both OpenAI and Google language models.
- **Intuitive GUI**: A streamlined desktop application built with PyQt6.

## How It Works

The system consists of four main Python scripts working together:

1.  **`mentor_mirror_gui.py`**: The main desktop application with animated progress tracking and streamlined interface.
2.  **`url2txts.py`**: A powerful scraper that extracts text content from web pages and PDF files.
3.  **`style_emulation_system.py`**: The core AI engine for style analysis, author inference, and text rewriting.
4.  **`mentor_mirror_pipeline.py`**: The backend orchestrator that runs the complete analysis workflow.

## Complete Workflow

When you add a new mentor, the system automatically performs these steps:

1. **Content Scraping**: Downloads and extracts text from the provided URL
2. **Author Inference**: Uses AI to automatically detect the author's name from the content
3. **Style Analysis**: Analyzes writing patterns, tone, vocabulary, and structure
4. **Mentor Prompts**: Generates specialized prompts for different mentoring scenarios
5. **Mentor-gram Creation**: Creates daily inspiration content in the author's voice
6. **Session Summary**: Builds a comprehensive summary of the analysis
7. **Database Update**: Adds the mentor to the central database

Each step includes validation to ensure all files are properly generated and contain valid data. The progress bar provides real-time animated feedback during processing.

## File Organization

All mentor data is organized in a clean folder structure:

```
MentorMirror/
├── mentors/                    # Main mentors directory
│   ├── mentors.json           # Central database of all mentors
│   ├── styles/                # Individual style analysis files
│   │   ├── paul_graham.json
│   │   ├── warren_buffett.json
│   │   ├── unknown_author_1.json
│   │   └── ...
│   └── sessions/              # Individual analysis sessions
│       ├── session_paul_graham_2025-01-15_14-30-25/
│       │   ├── style_analysis.json
│       │   ├── mentor_prompts.json
│       │   ├── mentorgram_2025-01-15.json
│       │   └── session_summary.json
│       └── ...
└── scraped_content_*/         # Temporary scraping directories
    ├── content.txt
    ├── content.json
    └── ...
```

## Getting Started

### Prerequisites

- Python 3.8+
- An OpenAI API key and/or a Google AI API key

### Installation

1.  **Clone the repository:**
    ```bash
    git clone <repository_url>
    cd MentorMirror
    ```

2.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

3.  **Set up your API keys:**
    Create a file named `.env` in the root directory:
    ```
    OPENAI_API_KEY="sk-..."
    GOOGLE_API_KEY="..."
    ```

### Running the Application

Launch the MentorMirror Control Panel:

```bash
python3 mentor_mirror_gui.py
```

## User Guide

### Adding a New Mentor (Streamlined Workflow)

1.  **Configure AI Settings**: Select your preferred AI service (OpenAI or Google) and model at the top of the "Add New Mentor" section.

2.  **Enter Content URL**: Paste any URL in the Content URL field:
    - Blog post URLs (e.g., `https://paulgraham.com/essay.html`)
    - PDF URLs (e.g., `https://example.com/document.pdf`)
    - Local file paths

3.  **Start Analysis**: Click "Start Complete Analysis" to begin the automated workflow.

4.  **Monitor Progress**: Watch the animated progress bar and step indicators:
    - Progress bar shows overall completion with smooth animation
    - Checkboxes indicate completed steps
    - Console shows detailed output and any errors

5.  **Review Results**: If successful, the new mentor will be automatically added to your database and available in the dropdown.

### Applying a Mentor's Style

1.  **Select a Mentor**: Choose from the dropdown (click "Refresh" if needed)
2.  **Enter Your Text**: Type or paste your text in the text box
3.  **Rewrite**: Click "Rewrite in Mentor's Style" 
4.  **View Results**: The rewritten text appears in the console output

The rewritten text preserves your original message while adopting the mentor's tone, vocabulary, and writing patterns.

## Smart Features

### Automatic Duplicate Handling

When the system encounters multiple "Unknown Author" entries, it automatically creates unique identifiers:
- First unknown: "Unknown Author 1"
- Second unknown: "Unknown Author 2"
- And so on...

This prevents conflicts and maintains a clean mentor database.

### Animated Progress Tracking

The progress bar provides visual feedback with smooth animations during processing, making it clear when the system is actively working versus completed.

### Organized File Management

All mentor-related files are automatically organized in the `mentors/` directory, keeping your workspace clean and making it easy to backup or share your mentor collection.

## Error Handling

The application includes comprehensive error handling:

- **File Validation**: All generated JSON files are validated for completeness and proper structure
- **Step-by-Step Tracking**: Each workflow step is individually monitored with clear success/failure indicators
- **Clear Error Messages**: Detailed console output helps identify and resolve issues
- **Graceful Degradation**: Failed steps don't crash the entire workflow

## Troubleshooting

**Q: The author name detection shows "Unknown Author 1, 2, etc."**
A: This happens when the AI cannot confidently identify the author from the content. The system automatically creates unique identifiers to prevent conflicts. You can manually edit the mentor name in the database if needed.

**Q: Some steps are failing during analysis**
A: Check the console output for specific error messages. Ensure your API keys are valid and you have sufficient credits/quota.

**Q: The mentor dropdown is empty**
A: Click the "Refresh" button or ensure you've successfully completed at least one full analysis workflow.

**Q: Can I add the same author multiple times?**
A: Yes, subsequent analyses will update the existing mentor entry. The system uses the inferred author name as the unique identifier.

## Advanced Usage

### Command Line Interface

You can also run the backend directly:

```bash
# Run complete analysis
python3 mentor_mirror_pipeline.py --service openai --model gpt-4o-mini complete --content-file path/to/content.txt

# Rewrite text
python3 mentor_mirror_pipeline.py --service google --model gemini-2.0-flash rewrite --mentor-name "Warren Buffett" --input-text "Your text here"
```

### Customizing Models

The GUI supports multiple AI models. Choose based on your needs:
- **GPT-4o Mini**: Fast and cost-effective for most tasks
- **GPT-4o**: Higher quality analysis for complex writing styles  
- **GPT-4 Turbo**: Enhanced capabilities for sophisticated analysis
- **Gemini Models**: Alternative provider with different strengths and pricing

### File Management

The organized folder structure makes it easy to:
- **Backup**: Simply copy the entire `mentors/` folder
- **Share**: Export specific mentor styles by sharing individual JSON files
- **Migrate**: Move the `mentors/` folder to different installations

Enjoy building your personal collection of writing mentors with MentorMirror!