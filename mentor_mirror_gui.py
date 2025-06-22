#!/usr/bin/env python3
"""
MentorMirror GUI
A PyQt6 frontend for the MentorMirror scraping and generation pipeline.
"""

import sys
import os
import re
import json
import tempfile
import requests
import time
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLineEdit, QTextEdit, QComboBox,
    QLabel, QGroupBox, QSplitter, QProgressBar, QCheckBox,
    QStatusBar
)
from PyQt6.QtCore import QProcess, Qt, QTimer, QThread, pyqtSignal
from PyQt6.QtGui import QFont
from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput
from PyQt6.QtCore import QUrl
from dotenv import load_dotenv

load_dotenv()

# Updated paths to use mentors folder
MENTORS_BASE_PATH = "mentors"
STYLE_DB_PATH = os.path.join(MENTORS_BASE_PATH, "styles")
MENTORS_DB_FILE = os.path.join(MENTORS_BASE_PATH, "mentors.json")

# Voice mapping for specific mentors
VOICE_MAPPINGS = {
    "eminem": "Xlpccr56K0lJCUlWyRFz",
    "winston_churchill":    "m5qbXI0CgAFzPG5UoMRP",
    "andrew_tate":  "dWpPffaVSc5yhGXUqsnc",
    "john_f_kennedy": "0s2PKBiONhElJhZwfnGL",
}

def safe_filename(name: str) -> str:
    """Create a safe, lowercase filename from a string."""
    name = name.lower().replace(" ", "_")
    return re.sub(r'[^a-z0-9_\-]', '', name)

def load_mentors_db():
    """Load the mentors database."""
    if os.path.exists(MENTORS_DB_FILE):
        try:
            with open(MENTORS_DB_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return {}
    return {}

class TTSWorker(QThread):
    """Worker thread for text-to-speech processing."""
    finished = pyqtSignal(str)  # Emits the path to the generated audio file
    error = pyqtSignal(str)     # Emits error message
    
    def __init__(self, text: str, voice_id: str):
        super().__init__()
        self.text = text
        self.voice_id = voice_id
        
    def run(self):
        """Generate speech using ElevenLabs API."""
        try:
            api_key = os.getenv("ELEVENLABS_API_KEY")
            if not api_key:
                self.error.emit("ElevenLabs API key not found in environment variables")
                return
            
            url = f"https://api.elevenlabs.io/v1/text-to-speech/{self.voice_id}"
            
            headers = {
                "Accept": "audio/mpeg",
                "Content-Type": "application/json",
                "xi-api-key": api_key
            }
            
            data = {
                "text": self.text,
                "model_id": "eleven_monolingual_v1",
                "voice_settings": {
                    "stability": 0.5,
                    "similarity_boost": 0.5
                }
            }
            
            response = requests.post(url, json=data, headers=headers, timeout=30)
            
            if response.status_code == 200:
                # Save audio to temporary file
                with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as tmp_file:
                    tmp_file.write(response.content)
                    self.finished.emit(tmp_file.name)
            else:
                self.error.emit(f"ElevenLabs API error: {response.status_code} - {response.text}")
                
        except Exception as e:
            self.error.emit(f"TTS generation failed: {str(e)}")

class MentorMirrorGUI(QWidget):
    def __init__(self):
        super().__init__()
        self.processes = []
        self.current_workflow_step = 0
        self.progress_timer = QTimer()
        self.progress_timer.timeout.connect(self.update_progress_animation)
        self.progress_animation_value = 0
        self.workflow_steps = [
            "Scraping Content",
            "Inferring Author", 
            "Analyzing Style",
            "Generating Prompts",
            "Creating Mentor-gram",
            "Building Summary",
            "Updating Database"
        ]
        
        # TTS components
        self.media_player = QMediaPlayer()
        self.audio_output = QAudioOutput()
        self.media_player.setAudioOutput(self.audio_output)
        self.media_player.mediaStatusChanged.connect(self.on_media_status_changed)
        self.media_player.playbackStateChanged.connect(self.on_playback_state_changed)
        self.tts_worker = None
        self.current_audio_file = None
        self.last_rewritten_text = ""
        
        # Timing components
        self.operation_start_time = None
        self.status_bar = None
        
        self.init_models_data()
        self.init_ui()
        # Ensure mentors folder structure exists
        os.makedirs(MENTORS_BASE_PATH, exist_ok=True)
        os.makedirs(STYLE_DB_PATH, exist_ok=True)

    def init_models_data(self):
        self.models_data = {
            "OpenAI": {
                "GPT-4o Mini": "gpt-4o-mini", 
                "GPT-4o": "gpt-4o",
                "GPT-4 Turbo": "gpt-4-turbo"
            },
            "Google": {
                "Gemini 2.5 Pro": "gemini-2.5-pro", 
                "Gemini 2.5 Flash": "gemini-2.5-flash",
                "Gemini 2.0 Flash": "gemini-2.0-flash",
                "Gemini 2.0 Flash-Lite": "gemini-2.0-flash-lite"
            }
        }

    def init_ui(self):
        self.setWindowTitle("MentorMirror Control Panel")
        self.setGeometry(100, 100, 1000, 950)

        # Initialize console_output first to avoid race condition during setup
        self.console_output = QTextEdit()
        self.console_output.setReadOnly(True)
        font = self.console_output.font()
        font.setFamily("Monaco" if sys.platform == "darwin" else "Consolas" if sys.platform == "win32" else "monospace")
        font.setPointSize(10)
        self.console_output.setFont(font)
        
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(15)
        main_layout.setContentsMargins(20, 20, 20, 20)
        
        # --- Main UI using a splitter ---
        splitter = QSplitter(Qt.Orientation.Vertical)

        # Top half of the splitter
        top_widget = QWidget()
        top_layout = QHBoxLayout(top_widget)
        top_layout.setSpacing(20)
        top_layout.setContentsMargins(0, 0, 0, 0)
        
        # --- Add Mentor Section ---
        add_mentor_group = self.create_add_mentor_group()
        
        # --- Apply Style Section ---
        apply_style_group = self.create_apply_style_group()

        top_layout.addWidget(add_mentor_group)
        top_layout.addWidget(apply_style_group)
        
        # Bottom half for the console
        console_group = QGroupBox("Console Output & Progress")
        console_layout = QVBoxLayout()
        console_layout.setSpacing(10)
        console_layout.setContentsMargins(15, 15, 15, 15)
        
        # Cancel button above progress bar
        cancel_layout = QHBoxLayout()
        self.cancel_button = QPushButton("Cancel Current Operation")
        self.cancel_button.setEnabled(False)
        self.cancel_button.clicked.connect(self.cancel_current_operation)
        self.cancel_button.setStyleSheet("QPushButton { background-color: #ff6b6b; color: white; }")
        cancel_layout.addWidget(self.cancel_button)
        cancel_layout.addStretch()
        
        # Progress tracking
        progress_layout = QVBoxLayout()
        progress_layout.setSpacing(8)
        self.progress_label = QLabel("Ready to start...")
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        
        # Step indicators
        steps_layout = QHBoxLayout()
        steps_layout.setSpacing(5)
        self.step_indicators = []
        for i, step in enumerate(self.workflow_steps):
            checkbox = QCheckBox(step)
            checkbox.setEnabled(False)
            checkbox.setStyleSheet("QCheckBox { font-size: 11px; }")
            self.step_indicators.append(checkbox)
            steps_layout.addWidget(checkbox)
        
        progress_layout.addWidget(self.progress_label)
        progress_layout.addWidget(self.progress_bar)
        progress_layout.addLayout(steps_layout)

        console_layout.addLayout(cancel_layout)
        console_layout.addLayout(progress_layout)
        console_layout.addWidget(self.console_output)
        console_group.setLayout(console_layout)

        splitter.addWidget(top_widget)
        splitter.addWidget(console_group)
        splitter.setSizes([300, 600])

        main_layout.addWidget(splitter)
        
        # Add status bar at the bottom
        self.status_bar = QStatusBar()
        self.status_bar.showMessage("Ready")
        main_layout.addWidget(self.status_bar)
        
        self.setLayout(main_layout)

    def create_legend_section(self):
        """Create the legend/instructions section."""
        group = QGroupBox("")
        layout = QVBoxLayout()
        layout.setSpacing(8)
        layout.setContentsMargins(15, 15, 15, 15)
        
        # Main description
        description = QLabel(
            "🎯 <b>MentorMirror</b> analyzes the writing style of your favorite authors and applies it to your own text.<br/>"
            "📝 <b>Step 1:</b> Enter any blog post or PDF URL → AI automatically detects the author and analyzes their style<br/>"
            "✍️ <b>Step 2:</b> Type your text → Get it rewritten in your chosen mentor's voice<br/>"
            "🎤 <b>Bonus:</b> Some mentors (like Eminem) support text-to-speech playback!"
        )
        description.setWordWrap(True)
        description.setStyleSheet("QLabel { color: #555; font-size: 12px; line-height: 1.4; }")
        
        layout.addWidget(description)
        group.setLayout(layout)
        return group

    def create_add_mentor_group(self):
        group = QGroupBox("1. Add New Mentor (Auto-detect Author)")
        layout = QVBoxLayout()
        layout.setSpacing(8)  # Reduced spacing
        layout.setContentsMargins(15, 15, 15, 15)
        
        # --- Legend/Instructions Section at the top ---
        legend_group = self.create_legend_section()
        
        # AI Service settings
        config_layout = QHBoxLayout()
        config_layout.setSpacing(15)
        
        service_label = QLabel("AI Service:")
        service_label.setFixedWidth(80)
        self.service_selector = QComboBox()
        self.service_selector.setFixedWidth(120)
        
        model_label = QLabel("Model:")
        model_label.setFixedWidth(50)
        self.model_selector = QComboBox()
        self.model_selector.setFixedWidth(150)
        
        # Add stretch to push everything to the left
        config_layout.addWidget(service_label)
        config_layout.addWidget(self.service_selector)
        config_layout.addWidget(model_label)
        config_layout.addWidget(self.model_selector)
        config_layout.addStretch()
        
        self.populate_services()
        self.service_selector.currentTextChanged.connect(self.update_model_selector)
        self.update_model_selector(self.service_selector.currentText())
        
        url_label = QLabel("Content URL (Blog Post or PDF):")
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("https://example.com/blog-post or path/to/document.pdf")
        
        self.add_mentor_button = QPushButton("Start Complete Analysis")
        self.add_mentor_button.setMinimumHeight(35)
        self.add_mentor_button.clicked.connect(self.run_complete_workflow)
        
        layout.addWidget(legend_group)
        layout.addLayout(config_layout)
        layout.addWidget(url_label)
        layout.addWidget(self.url_input)
        layout.addWidget(self.add_mentor_button)
        group.setLayout(layout)
        return group

    def create_apply_style_group(self):
        group = QGroupBox("2. Apply Mentor Style")
        layout = QVBoxLayout()
        layout.setSpacing(12)
        layout.setContentsMargins(15, 15, 15, 15)

        # Mentor selection
        mentor_select_layout = QHBoxLayout()
        mentor_select_layout.setSpacing(10)
        author_label = QLabel("Select Mentor:")
        author_label.setFixedWidth(100)
        self.author_selector = QComboBox()
        self.author_selector.setMinimumWidth(200)
        self.refresh_authors_button = QPushButton("Refresh")
        self.refresh_authors_button.setFixedWidth(80)
        self.refresh_authors_button.clicked.connect(self.populate_authors)
        
        mentor_select_layout.addWidget(author_label)
        mentor_select_layout.addWidget(self.author_selector)
        mentor_select_layout.addWidget(self.refresh_authors_button)
        mentor_select_layout.addStretch()
        
        # Connect mentor selection change to TTS availability check
        self.author_selector.currentTextChanged.connect(self.on_mentor_selection_changed)

        text_label = QLabel("Your Text to Rewrite:")
        self.user_text_input = QTextEdit()
        self.user_text_input.setPlaceholderText("Enter your text here to rewrite in the mentor's style...")
        self.user_text_input.setMaximumHeight(120)
        self.user_text_input.textChanged.connect(self.on_user_text_changed)

        # Preserve text without tone checkbox
        self.preserve_tone_checkbox = QCheckBox("Preserve text without tone (use mentor's voice for original text)")
        self.preserve_tone_checkbox.stateChanged.connect(self.on_preserve_tone_changed)

        self.rewrite_button = QPushButton("Rewrite in Mentor's Style")
        self.rewrite_button.setMinimumHeight(35)
        self.rewrite_button.clicked.connect(self.run_rewrite_text)

        # TTS Controls (initially hidden)
        tts_layout = QHBoxLayout()
        self.play_pause_button = QPushButton("▶️ Play")
        self.play_pause_button.setVisible(False)
        self.play_pause_button.clicked.connect(self.toggle_playback)
        self.tts_status_label = QLabel("")
        self.tts_status_label.setVisible(False)
        
        tts_layout.addWidget(self.play_pause_button)
        tts_layout.addWidget(self.tts_status_label)
        tts_layout.addStretch()

        layout.addLayout(mentor_select_layout)
        layout.addWidget(text_label)
        layout.addWidget(self.user_text_input)
        layout.addWidget(self.preserve_tone_checkbox)
        layout.addWidget(self.rewrite_button)
        layout.addLayout(tts_layout)
        group.setLayout(layout)
        
        self.populate_authors()
        return group

    def cancel_current_operation(self):
        """Cancel the currently running operation."""
        for process in self.processes:
            if process.state() == QProcess.ProcessState.Running:
                process.kill()
                self.console_output.append("\n🛑 Operation cancelled by user.")
        
        # End timing for cancelled operation
        self.end_operation_timer("Operation cancelled by user")
        
        self.reset_progress_indicators()
        self.set_buttons_enabled(True)
        self.cancel_button.setEnabled(False)
    
    def populate_services(self):
        self.service_selector.addItems(self.models_data.keys())

    def update_model_selector(self, service):
        self.model_selector.clear()
        if service in self.models_data:
            for name, mid in self.models_data[service].items():
                self.model_selector.addItem(name, mid)

    def populate_authors(self):
        """Populate authors from the mentors.json database."""
        # Temporarily disconnect signal to prevent multiple triggers during population
        self.author_selector.currentTextChanged.disconnect(self.on_mentor_selection_changed)
        
        self.author_selector.clear()
        mentors_db = load_mentors_db()
        
        for safe_name, mentor_info in mentors_db.items():
            if mentor_info.get("status") == "active":
                display_name = mentor_info.get("display_name", safe_name.replace("_", " ").title())
                self.author_selector.addItem(display_name, safe_name)
        
        # Reconnect signal after population
        self.author_selector.currentTextChanged.connect(self.on_mentor_selection_changed)
        
        # Update TTS availability after populating authors
        self.update_tts_availability()

    def reset_progress_indicators(self):
        """Reset all progress indicators."""
        self.current_workflow_step = 0
        self.progress_bar.setValue(0)
        self.progress_bar.setVisible(False)
        self.progress_timer.stop()
        for checkbox in self.step_indicators:
            checkbox.setChecked(False)
        self.progress_label.setText("Ready to start...")
        self.status_bar.showMessage("Ready")

    def update_progress_animation(self):
        """Animate the progress bar while processing."""
        if self.progress_bar.isVisible():
            self.progress_animation_value = (self.progress_animation_value + 2) % 100
            if self.current_workflow_step < len(self.workflow_steps):
                base_progress = int((self.current_workflow_step / len(self.workflow_steps)) * 100)
                animated_progress = min(base_progress + (self.progress_animation_value // 10), 
                                      int(((self.current_workflow_step + 1) / len(self.workflow_steps)) * 100))
                self.progress_bar.setValue(animated_progress)

    def update_progress(self, step_name: str, completed: bool = True):
        """Update progress indicators."""
        self.progress_bar.setVisible(True)
        
        if completed:
            # Find and check the completed step
            for i, checkbox in enumerate(self.step_indicators):
                if step_name.lower() in checkbox.text().lower():
                    checkbox.setChecked(True)
                    self.current_workflow_step = max(self.current_workflow_step, i + 1)
                    break
            
            progress_percent = int((self.current_workflow_step / len(self.workflow_steps)) * 100)
            self.progress_bar.setValue(progress_percent)
            self.progress_label.setText(f"Completed: {step_name}")
            
            # Stop animation if all steps completed
            if self.current_workflow_step >= len(self.workflow_steps):
                self.progress_timer.stop()
        else:
            self.progress_label.setText(f"Working on: {step_name}")
            # Start animation timer for active processing
            if not self.progress_timer.isActive():
                self.progress_timer.start(100)  # Update every 100ms

    def run_complete_workflow(self):
        """Run the complete mentor analysis workflow."""
        url = self.url_input.text().strip()
        if not url:
            self.console_output.append("❌ Error: Please enter a URL to scrape.")
            return
        self.run_scrape_then_analyze(url)

    def run_scrape_then_analyze(self, url):
        """Run scraping followed by complete analysis."""
        self.console_output.clear()
        self.reset_progress_indicators()
        self.update_progress("Scraping Content", False)
        
        # Start timing for complete workflow
        self.start_operation_timer("Starting complete analysis workflow...")
        
        py_exec = sys.executable
        self.run_script(py_exec, ["url2txts.py", url], on_finish=self.on_scraping_finished)

    def on_scraping_finished(self, output):
        """Handle completion of scraping step."""
        self.update_progress("Scraping Content", True)
        
        # Extract the content file from scraper output
        output_dir_match = re.search(r"Content saved to: (.*)", output)
        if not output_dir_match:
            self.console_output.append("❌ Error: Could not determine scraper output directory.")
            self.set_buttons_enabled(True)
            return

        output_dir = output_dir_match.group(1).strip()
        txt_files = [f for f in os.listdir(output_dir) if f.endswith('.txt')]
        if not txt_files:
            self.console_output.append(f"❌ Error: No .txt file found in {output_dir}.")
            self.set_buttons_enabled(True)
            return

        content_file = os.path.join(output_dir, txt_files[0])
        self.run_complete_analysis(content_file)

    def run_complete_analysis(self, content_file):
        """Run the complete analysis pipeline."""
        service = self.service_selector.currentText().lower()
        model = self.model_selector.currentData()
        py_exec = sys.executable

        self.update_progress("Starting Analysis", False)
        
        args = [
            "mentor_mirror_pipeline.py",
            "--service", service,
            "--model", model,
            "complete",
            "--content-file", content_file
        ]
        self.run_script(py_exec, args, on_finish=self.on_analysis_finished)

    def on_analysis_finished(self, output):
        """Handle completion of the complete analysis."""
        # Parse the output to update progress indicators
        if "Step 1/5: Inferring author name" in output:
            self.update_progress("Inferring Author", True)
        if "Step 2/5: Analyzing writing style" in output:
            self.update_progress("Analyzing Style", True)
        if "Step 3/5: Generating mentor prompts" in output:
            self.update_progress("Generating Prompts", True)
        if "Step 4/5: Generating daily Mentor-gram" in output:
            self.update_progress("Creating Mentor-gram", True)
        if "Step 5/5: Creating session summary" in output:
            self.update_progress("Building Summary", True)
        if "Mentors database updated" in output:
            self.update_progress("Updating Database", True)
        
        # Check for success and end timing
        if "Complete analysis finished successfully!" in output:
            self.end_operation_timer("Complete analysis finished successfully!")
            self.console_output.append("\n🎉 Complete workflow finished successfully!")
            self.populate_authors()  # Refresh the dropdown
        else:
            self.end_operation_timer("Complete analysis finished with issues")
            self.console_output.append("\n⚠️ Workflow completed with some issues. Check console for details.")
        
        self.set_buttons_enabled(True)

    def run_rewrite_text(self):
        """Rewrite user text in mentor's style."""
        user_text = self.user_text_input.toPlainText().strip()

        if not user_text:
            self.console_output.append("❌ Error: Please enter text to rewrite.")
            return
        
        # Get mentor name from dropdown
        mentor_safe_name = self.author_selector.currentData()
        if not mentor_safe_name:
            self.console_output.append("❌ Error: Please select a mentor.")
            return
        
        # Get display name for the mentor from database
        mentors_db = load_mentors_db()
        mentor_info = mentors_db.get(mentor_safe_name, {})
        mentor_display_name = mentor_info.get("display_name", mentor_safe_name.replace("_", " ").title())
        
        service = self.service_selector.currentText().lower()
        model = self.model_selector.currentData()
        py_exec = sys.executable

        self.console_output.clear()
        self.console_output.append(f"▶️ Rewriting text in the style of {mentor_display_name}...")
        
        # Start timing for text rewriting
        self.start_operation_timer(f"Rewriting text in {mentor_display_name}'s style...")

        args = [
            "mentor_mirror_pipeline.py",
            "--service", service,
            "--model", model,
            "rewrite",
            "--mentor-name", mentor_display_name,
            "--input-text", user_text
        ]
        self.run_script(py_exec, args, on_finish=self.on_rewrite_finished)

    def on_mentor_selection_changed(self):
        """Handle mentor selection changes."""
        self.update_tts_availability()

    def on_user_text_changed(self):
        """Handle changes to user text input."""
        if self.preserve_tone_checkbox.isChecked():
            self.update_tts_availability()

    def update_tts_availability(self):
        """Update TTS controls visibility based on current state."""
        mentor_safe_name = self.author_selector.currentData()
        user_text = self.user_text_input.toPlainText().strip()
        
        # Check if mentor has voice mapping (more robust checking)
        has_voice_mapping = False
        if mentor_safe_name:
            # Try multiple variations to find voice mapping
            mentor_variations = [
                mentor_safe_name.lower(),
                mentor_safe_name.lower().replace(' ', '_'),
                mentor_safe_name.lower().replace('_', ' ')
            ]
            has_voice_mapping = any(var in VOICE_MAPPINGS for var in mentor_variations)
        
        # Debug output for troubleshooting
        if mentor_safe_name:
            self.console_output.append(f"🔍 Debug: Mentor '{mentor_safe_name}' -> Voice available: {has_voice_mapping}")
        
        if self.preserve_tone_checkbox.isChecked():
            # For preserve tone mode: need mentor with voice + user text
            if has_voice_mapping and user_text:
                self.show_tts_controls()
                self.console_output.append("🎤 TTS available: Using mentor's voice for original text")
            else:
                self.hide_tts_controls()
                if not has_voice_mapping and mentor_safe_name:
                    self.console_output.append(f"❌ No voice mapping found for mentor: {mentor_safe_name}")
        else:
            # For rewrite mode: need mentor with voice + rewritten text
            if has_voice_mapping and self.last_rewritten_text:
                self.show_tts_controls()
                self.console_output.append("🎤 TTS available: Using mentor's voice for rewritten text")
            else:
                self.hide_tts_controls()
                if not has_voice_mapping and mentor_safe_name:
                    self.console_output.append(f"❌ No voice mapping found for mentor: {mentor_safe_name}")

    def on_preserve_tone_changed(self):
        """Handle preserve tone checkbox state change."""
        if self.preserve_tone_checkbox.isChecked():
            # Set the text to be used for TTS as the original user input
            user_text = self.user_text_input.toPlainText().strip()
            if user_text:
                self.last_rewritten_text = user_text
        
        # Update TTS availability based on new state
        self.update_tts_availability()

    def on_rewrite_finished(self, output):
        """Handle completion of text rewriting."""
        # End timing for text rewriting
        self.end_operation_timer("Text rewriting completed")
        
        self.set_buttons_enabled(True)
        
        # Extract the rewritten text from output
        rewritten_match = re.search(r"--- REWRITTEN TEXT ---\n(.*?)\n--------------------", output, re.DOTALL)
        if rewritten_match:
            self.last_rewritten_text = rewritten_match.group(1).strip()
        
        # Update TTS availability based on new rewritten text
        self.update_tts_availability()

    def show_tts_controls(self):
        """Show the TTS play/pause controls."""
        self.play_pause_button.setVisible(True)
        self.tts_status_label.setVisible(True)
        self.tts_status_label.setText("🎤 Voice available - Click play to hear!")
        self.play_pause_button.setText("▶️ Play")

    def hide_tts_controls(self):
        """Hide the TTS controls."""
        self.play_pause_button.setVisible(False)
        self.tts_status_label.setVisible(False)
        if self.media_player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
            self.media_player.stop()

    def toggle_playback(self):
        """Toggle audio playback based on player state."""
        state = self.media_player.playbackState()

        if state == QMediaPlayer.PlaybackState.PlayingState:
            self.media_player.pause()
        elif state == QMediaPlayer.PlaybackState.PausedState:
            self.media_player.play()
        else:  # StoppedState
            self.generate_and_play_audio()

    def generate_and_play_audio(self):
        """Generate audio using ElevenLabs API and play it."""
        # Stop any currently playing audio and clean up old file
        if self.media_player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
            self.media_player.stop()
        
        # Clean up old audio file
        if self.current_audio_file and os.path.exists(self.current_audio_file):
            try:
                os.unlink(self.current_audio_file)
                self.current_audio_file = None
            except OSError:
                pass

        # Get mentor voice ID with robust matching
        mentor_safe_name = self.author_selector.currentData()
        voice_id = None
        if mentor_safe_name:
            # Try multiple variations to find voice mapping
            mentor_variations = [
                mentor_safe_name.lower(),
                mentor_safe_name.lower().replace(' ', '_'),
                mentor_safe_name.lower().replace('_', ' ')
            ]
            for variation in mentor_variations:
                if variation in VOICE_MAPPINGS:
                    voice_id = VOICE_MAPPINGS[variation]
                    break
        
        # Determine text to convert based on preserve tone checkbox
        if self.preserve_tone_checkbox.isChecked():
            # Use the original user text for preserve tone mode
            text_to_convert = self.user_text_input.toPlainText().strip()
        else:
            text_to_convert = self.last_rewritten_text
            
        # Check if we have text to convert
        if not text_to_convert:
            self.tts_status_label.setText("❌ No text to convert")
            return
            
        if not voice_id:
            self.tts_status_label.setText("❌ Voice not available")
            return

        self.play_pause_button.setEnabled(False)
        self.tts_status_label.setText("🔄 Generating audio...")
        
        # Start timing for TTS generation
        self.start_operation_timer("Generating audio...")

        # Start TTS worker thread
        self.tts_worker = TTSWorker(text_to_convert, voice_id)
        self.tts_worker.finished.connect(self.on_tts_finished)
        self.tts_worker.error.connect(self.on_tts_error)
        self.tts_worker.start()

    def on_tts_finished(self, audio_file_path):
        """Handle successful TTS generation."""
        # End timing for TTS generation
        self.end_operation_timer("Audio generation completed")
        
        self.current_audio_file = audio_file_path
        self.media_player.setSource(QUrl.fromLocalFile(audio_file_path))
        self.media_player.play()
        
        self.play_pause_button.setEnabled(True)
        # UI update is handled by on_playback_state_changed

    def on_tts_error(self, error_message):
        """Handle TTS generation error."""
        # End timing for TTS generation
        self.end_operation_timer("Audio generation failed")
        
        self.play_pause_button.setEnabled(True)
        self.tts_status_label.setText(f"❌ TTS Error: {error_message}")
        self.console_output.append(f"❌ Text-to-Speech Error: {error_message}")

    def on_media_status_changed(self, status):
        """Handle media player status changes."""
        if status == QMediaPlayer.MediaStatus.EndOfMedia:
            # When audio finishes, the state automatically becomes StoppedState.
            # on_playback_state_changed will handle the UI update.
            pass

    def on_playback_state_changed(self, state):
        """Handle playback state changes and update UI."""
        if state == QMediaPlayer.PlaybackState.PlayingState:
            self.play_pause_button.setText("⏸️ Pause")
            self.tts_status_label.setText("🔊 Playing...")
        elif state == QMediaPlayer.PlaybackState.PausedState:
            self.play_pause_button.setText("▶️ Play")
            self.tts_status_label.setText("⏸️ Paused")
        else:  # StoppedState
            self.play_pause_button.setText("▶️ Play")
            if self.tts_status_label.isVisible() and "error" not in self.tts_status_label.text().lower():
                self.tts_status_label.setText("🎤 Voice available - Click play to hear!")

    def run_script(self, executable, args, on_finish=None):
        """Generic method to run a Python script as a subprocess."""
        if any(p.state() == QProcess.ProcessState.Running for p in self.processes):
            self.console_output.append("⚠️ A process is already running. Please wait.")
            return

        process = QProcess(self)
        process.setProcessChannelMode(QProcess.ProcessChannelMode.MergedChannels)
        process.full_output = ""

        def handle_output():
            data = process.readAllStandardOutput().data().decode(errors='ignore')
            process.full_output += data
            self.console_output.moveCursor(self.console_output.textCursor().MoveOperation.End)
            self.console_output.insertPlainText(data)
            self.console_output.moveCursor(self.console_output.textCursor().MoveOperation.End)
            
            # Real-time progress updates
            if "Step" in data and ":" in data:
                for line in data.split('\n'):
                    if "Step" in line and ":" in line:
                        step_text = line.split(':', 1)[-1].strip()
                        self.update_progress(step_text, False)

        def handle_finish():
            self.console_output.append(f"\n✅ Process finished.")
            self.processes.remove(process)
            self.cancel_button.setEnabled(False)
            if on_finish:
                on_finish(process.full_output)
            else:
                self.set_buttons_enabled(True)

        process.readyReadStandardOutput.connect(handle_output)
        process.finished.connect(handle_finish)
        
        self.processes.append(process)
        process.start(executable, args)
        self.set_buttons_enabled(False)
        self.cancel_button.setEnabled(True)

    def start_operation_timer(self, operation_name):
        """Start timing an operation."""
        self.operation_start_time = time.time()
        self.status_bar.showMessage(f"{operation_name}")

    def end_operation_timer(self, operation_name):
        """End timing an operation and display the elapsed time."""
        if self.operation_start_time:
            elapsed_time = time.time() - self.operation_start_time
            self.status_bar.showMessage(f"{operation_name} in {elapsed_time:.1f}s")
            self.operation_start_time = None
        else:
            self.status_bar.showMessage(operation_name)

    def set_buttons_enabled(self, enabled):
        """Enable or disable the action buttons."""
        self.add_mentor_button.setEnabled(enabled)
        self.rewrite_button.setEnabled(enabled)

    def closeEvent(self, event):
        """Ensure child processes are killed on exit."""
        for p in self.processes:
            p.kill()
        
        # Clean up temporary audio files
        if self.current_audio_file and os.path.exists(self.current_audio_file):
            try:
                os.unlink(self.current_audio_file)
            except OSError:
                pass
        
        event.accept()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = MentorMirrorGUI()
    ex.show()
    sys.exit(app.exec()) 