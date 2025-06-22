#!/usr/bin/env python3
"""
MentorMirror GUI
A PyQt6 frontend for the MentorMirror scraping and generation pipeline.
"""

import sys
import os
import re
import json
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLineEdit, QTextEdit, QComboBox,
    QLabel, QGroupBox, QSplitter, QProgressBar, QCheckBox
)
from PyQt6.QtCore import QProcess, Qt, QTimer
from PyQt6.QtGui import QFont

# Updated paths to use mentors folder
MENTORS_BASE_PATH = "mentors"
STYLE_DB_PATH = os.path.join(MENTORS_BASE_PATH, "styles")
MENTORS_DB_FILE = os.path.join(MENTORS_BASE_PATH, "mentors.json")

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
        self.setGeometry(100, 100, 1000, 900)
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
        
        self.console_output = QTextEdit()
        self.console_output.setReadOnly(True)
        # Use system monospace font instead of "Courier"
        font = self.console_output.font()
        font.setFamily("Monaco" if sys.platform == "darwin" else "Consolas" if sys.platform == "win32" else "monospace")
        font.setPointSize(10)
        self.console_output.setFont(font)
        
        console_layout.addLayout(progress_layout)
        console_layout.addWidget(self.console_output)
        console_group.setLayout(console_layout)

        splitter.addWidget(top_widget)
        splitter.addWidget(console_group)
        splitter.setSizes([300, 600])

        main_layout.addWidget(splitter)
        self.setLayout(main_layout)

    def create_add_mentor_group(self):
        group = QGroupBox("1. Add New Mentor (Auto-detect Author)")
        layout = QVBoxLayout()
        layout.setSpacing(8)  # Reduced spacing
        layout.setContentsMargins(15, 15, 15, 15)
        
        # AI Service settings at the top
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

        text_label = QLabel("Your Text to Rewrite:")
        self.user_text_input = QTextEdit()
        self.user_text_input.setPlaceholderText("Enter your text here to rewrite in the mentor's style...")
        self.user_text_input.setMaximumHeight(120)

        self.rewrite_button = QPushButton("Rewrite in Mentor's Style")
        self.rewrite_button.setMinimumHeight(35)
        self.rewrite_button.clicked.connect(self.run_rewrite_text)

        layout.addLayout(mentor_select_layout)
        layout.addWidget(text_label)
        layout.addWidget(self.user_text_input)
        layout.addWidget(self.rewrite_button)
        group.setLayout(layout)
        
        self.populate_authors()
        return group
    
    def populate_services(self):
        self.service_selector.addItems(self.models_data.keys())

    def update_model_selector(self, service):
        self.model_selector.clear()
        if service in self.models_data:
            for name, mid in self.models_data[service].items():
                self.model_selector.addItem(name, mid)

    def populate_authors(self):
        """Populate authors from the mentors.json database."""
        self.author_selector.clear()
        mentors_db = load_mentors_db()
        
        for safe_name, mentor_info in mentors_db.items():
            if mentor_info.get("status") == "active":
                display_name = mentor_info.get("display_name", safe_name.replace("_", " ").title())
                self.author_selector.addItem(display_name, safe_name)

    def reset_progress_indicators(self):
        """Reset all progress indicators."""
        self.current_workflow_step = 0
        self.progress_bar.setValue(0)
        self.progress_bar.setVisible(False)
        self.progress_timer.stop()
        for checkbox in self.step_indicators:
            checkbox.setChecked(False)
        self.progress_label.setText("Ready to start...")

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
        
        # Check for success
        if "Complete analysis finished successfully!" in output:
            self.console_output.append("\n🎉 Complete workflow finished successfully!")
            self.populate_authors()  # Refresh the dropdown
        else:
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

        args = [
            "mentor_mirror_pipeline.py",
            "--service", service,
            "--model", model,
            "rewrite",
            "--mentor-name", mentor_display_name,
            "--input-text", user_text
        ]
        self.run_script(py_exec, args)
    
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
            if on_finish:
                on_finish(process.full_output)
            else:
                self.set_buttons_enabled(True)

        process.readyReadStandardOutput.connect(handle_output)
        process.finished.connect(handle_finish)
        
        self.processes.append(process)
        process.start(executable, args)
        self.set_buttons_enabled(False)

    def set_buttons_enabled(self, enabled):
        """Enable or disable the action buttons."""
        self.add_mentor_button.setEnabled(enabled)
        self.rewrite_button.setEnabled(enabled)

    def closeEvent(self, event):
        """Ensure child processes are killed on exit."""
        for p in self.processes:
            p.kill()
        event.accept()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = MentorMirrorGUI()
    ex.show()
    sys.exit(app.exec()) 