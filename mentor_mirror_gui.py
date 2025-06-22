#!/usr/bin/env python3
"""
MentorMirror GUI
A PyQt6 frontend for the MentorMirror scraping and generation pipeline.
"""

import sys
import os
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLineEdit, QTextEdit, QComboBox,
    QLabel, QFrame, QGroupBox
)
from PyQt6.QtCore import QProcess, Qt
from PyQt6.QtGui import QFont, QIcon

class MentorMirrorGUI(QWidget):
    def __init__(self):
        super().__init__()
        self.process = None
        self.init_ui()

    def init_ui(self):
        """Initialize the user interface."""
        self.setWindowTitle("MentorMirror Control Panel")
        self.setGeometry(100, 100, 800, 700)

        # Main layout
        main_layout = QVBoxLayout(self)

        # --- Scraper Section ---
        scraper_group = QGroupBox("1. Content Scraping")
        scraper_layout = QVBoxLayout()

        # URL input
        url_layout = QHBoxLayout()
        url_label = QLabel("URL to Scrape:")
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("https://example.com/blog-post or /path/to/local.pdf")
        url_layout.addWidget(url_label)
        url_layout.addWidget(self.url_input)
        
        self.scrape_button = QPushButton("Start Scraping")
        self.scrape_button.clicked.connect(self.run_url2txts)

        scraper_layout.addLayout(url_layout)
        scraper_layout.addWidget(self.scrape_button)
        scraper_group.setLayout(scraper_layout)

        # --- Mentor Session Section ---
        mentor_group = QGroupBox("2. Mentor Session Generation")
        mentor_layout = QVBoxLayout()
        
        # Model selection
        model_layout = QHBoxLayout()
        model_label = QLabel("Select AI Model:")
        self.model_selector = QComboBox()
        self.populate_models()
        model_layout.addWidget(model_label)
        model_layout.addWidget(self.model_selector)
        
        self.mentor_button = QPushButton("Start Mentor Session")
        self.mentor_button.clicked.connect(self.run_mentor_mirror)

        mentor_layout.addLayout(model_layout)
        mentor_layout.addWidget(self.mentor_button)
        mentor_group.setLayout(mentor_layout)

        # --- Console Output Section ---
        console_group = QGroupBox("Console Output")
        console_layout = QVBoxLayout()
        self.console_output = QTextEdit()
        self.console_output.setReadOnly(True)
        self.console_output.setFont(QFont("Courier", 10))
        self.console_output.setStyleSheet("background-color: #f0f0f0; color: #333;")
        console_layout.addWidget(self.console_output)
        console_group.setLayout(console_layout)

        # Add groups to main layout
        main_layout.addWidget(scraper_group)
        main_layout.addWidget(mentor_group)
        main_layout.addWidget(console_group, 1) # Give console extra space
        
        self.setLayout(main_layout)

    def populate_models(self):
        """Populate the model selector dropdown."""
        models = [
            # Display Name, (service, model_id)
            ("OpenAI: GPT-4o Mini", ("openai", "gpt-4o-mini")),
            ("OpenAI: GPT-4o", ("openai", "gpt-4o")),
            ("OpenAI: GPT-4 Turbo", ("openai", "gpt-4-turbo")),
            ("Google: Gemini 2.5 Flash", ("google", "gemini-2.5-flash-latest")),
            ("Google: Gemini 2.5 Pro", ("google", "gemini-2.5-pro-latest")),
        ]
        
        for display_name, model_data in models:
            self.model_selector.addItem(display_name, model_data)

    def run_url2txts(self):
        """Execute the url2txts.py script."""
        url = self.url_input.text().strip()
        if not url:
            self.console_output.append("❌ Error: Please enter a URL to scrape.")
            return

        script_path = "url2txts.py"
        if not os.path.exists(script_path):
            self.console_output.append(f"❌ Error: Script not found at {script_path}")
            return
            
        self.console_output.clear()
        self.console_output.append(f"▶️ Starting scraping process for: {url}...")
        
        # Get path to python executable
        python_executable = sys.executable
        
        args = [url]
        self.run_script(python_executable, [script_path] + args)

    def run_mentor_mirror(self):
        """Execute the mentor_mirror_pipeline.py script."""
        script_path = "mentor_mirror_pipeline.py"
        if not os.path.exists(script_path):
            self.console_output.append(f"❌ Error: Script not found at {script_path}")
            return

        service, model_name = self.model_selector.currentData()
        
        self.console_output.clear()
        self.console_output.append(f"▶️ Starting MentorMirror session with {service.capitalize()}:{model_name}...")
        
        python_executable = sys.executable
        args = ["--service", service, "--model", model_name]
        self.run_script(python_executable, [script_path] + args)

    def run_script(self, executable, args):
        """Generic method to run a Python script as a subprocess."""
        if self.process and self.process.state() == QProcess.ProcessState.Running:
            self.console_output.append("⚠️ A process is already running. Please wait.")
            return

        self.process = QProcess(self)
        self.process.setProcessChannelMode(QProcess.ProcessChannelMode.MergedChannels)
        
        self.process.readyReadStandardOutput.connect(self.handle_stdout)
        self.process.finished.connect(self.process_finished)
        
        self.process.start(executable, args)
        self.set_buttons_enabled(False)

    def handle_stdout(self):
        """Read output from the running process."""
        data = self.process.readAllStandardOutput()
        try:
            # Try to decode as UTF-8, fall back to latin-1 if it fails
            text = data.data().decode('utf-8')
        except UnicodeDecodeError:
            text = data.data().decode('latin-1')
        self.console_output.append(text.strip())

    def process_finished(self):
        """Handle the process finishing."""
        self.console_output.append("\n✅ Process finished.")
        self.process = None
        self.set_buttons_enabled(True)

    def set_buttons_enabled(self, enabled):
        """Enable or disable the start buttons."""
        self.scrape_button.setEnabled(enabled)
        self.mentor_button.setEnabled(enabled)

    def closeEvent(self, event):
        """Ensure child process is killed on exit."""
        if self.process:
            self.process.kill()
        event.accept()

def main():
    app = QApplication(sys.argv)
    ex = MentorMirrorGUI()
    ex.show()
    sys.exit(app.exec())

if __name__ == '__main__':
    main() 