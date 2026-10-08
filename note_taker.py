import pyaudio, wave, sys
from faster_whisper import WhisperModel

from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QPushButton,
    QLabel,
    QPlainTextEdit,
    QComboBox,
    QTabWidget,
    QListWidget,
    QVBoxLayout,
    QHBoxLayout,
    QFrame
)

from PySide6.QtCore import Qt, QObject, QThread, Signal, Slot

from ollama import chat

model_size = "small"
chunk = 1024  # Record in chunks of 1024 samples
sample_format = pyaudio.paInt16  # 16 bits per sample
channels = 1
fs = 44100  # Record at 44100 samples per second
seconds = 10
filename = "output.wav"

class NoteGenerationWorker(QObject):
    finished = Signal(str)
    error = Signal(str)
    
    def __init__(self, transcription, file):
        self.file = file
        self.transcription = transcription
        super().__init__()
    
    @Slot()
    def run(self):
        try:
            response = chat(
                model = "qwen3:4b",
                messages = [
                    {
                        "role": "system",
                        "content": """
You are a university lecture note-taking assistant.

Your job is to convert long, messy lecture transcripts into clear, structured revision notes.

Rules:
- Do not invent information that is not present in the transcript.
- Remove filler, repetition, false starts, and irrelevant conversational remarks.
- Preserve important definitions, explanations, examples, formulas, technical terms, and lecturer emphasis.
- Organise the notes into logical sections with clear headings and subheadings.
- Keep explanations detailed enough to revise from later.
- If the lecturer gives an example, keep it and explain what concept it demonstrates.
- If something sounds especially important, likely examinable, or repeatedly emphasised, mark it clearly.
- Preserve important terminology exactly where possible.
- If the transcript contains uncertainty or unclear wording, do not silently guess; mark it as unclear.
- Finish with:
  1. Key concepts
  2. Important definitions
  3. Lecturer examples
  4. Likely revision points
  5. A concise overall summary
"""
                    },
                    {
                        "role": "user",
                        "content": f"""{self.transcription}"""
                    }
                ]
            )
            
            with open(self.file, "w", encoding="utf-8") as f:
                f.write(response.message.content)
                f.close()
            
            self.finished.emit(self.file)
            
        except Exception as e:
            self.error.emit(str(e))
        
        
            
class TranscribingWorker(QObject):
    finished = Signal(str)
    error = Signal(str)
    
    def __init__(self, file):
        self.file = file
        super().__init__()
    
    @Slot()
    def run(self):
        try:
            print("Started transcribing")
            
            model = WhisperModel(
                model_size,
                device="cpu",
                compute_type="int8"
            )
            
            segments, info = model.transcribe(filename,
                                            beam_size = 5)
            
            to_txt(segments)
            
            print("Finished transcribing")
            
            self.finished.emit(self.file)
                        
        except Exception as e:
            self.error.emit(str(e))
        
    def to_txt(self, segments):
        with open(self.file, "w") as f:
                    for segment in segments:
                        f.write(f"{segment.txt}\n")
                    
                    f.close
        return
class RecordingWorker(QObject):
    finished = Signal(str)
    error = Signal(str)

    def __init__(self):
        super().__init__()

    @Slot()
    def run(self):
        p = None
        stream = None
        frames = []

        try:
            p = pyaudio.PyAudio()

            stream = p.open(
                format=sample_format,
                channels=channels,
                rate=fs,
                frames_per_buffer=chunk,
                input=True
            )

            print("Recording")

            while not QThread.currentThread().isInterruptionRequested():
                data = stream.read(chunk)
                frames.append(data)

            print("Recording finished")

            stream.stop_stream()
            stream.close()
            stream = None

            wf = wave.open(filename, "wb")
            wf.setnchannels(channels)
            wf.setsampwidth(p.get_sample_size(sample_format))
            wf.setframerate(fs)
            wf.writeframes(b"".join(frames))
            wf.close()

            self.finished.emit(filename)

        except Exception as e:
            self.error.emit(str(e))

        finally:
            if stream is not None:
                stream.stop_stream()
                stream.close()

            if p is not None:
                p.terminate()
                
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.record_thread = None
        self.transcribing_thread = None
        self.generating_thread = None
        
        self.recording_worker = None
        self.transcribing_worker = None
        self.generating_worker = None
        self.setWindowTitle("Lecture Assistant")
        self.resize(1200, 800)

        # --------------------------------------------------
        # CENTRAL WIDGET
        # --------------------------------------------------

        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QHBoxLayout(central_widget)

        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # --------------------------------------------------
        # SIDEBAR
        # --------------------------------------------------

        sidebar = QFrame()
        sidebar.setFixedWidth(220)

        sidebar_layout = QVBoxLayout(sidebar)

        sidebar_layout.setContentsMargins(20, 25, 20, 20)
        sidebar_layout.setSpacing(12)

        app_title = QLabel("Lecture Assistant")
        app_title.setObjectName("appTitle")

        sidebar_layout.addWidget(app_title)

        # Eventually this could contain saved lectures.
        self.lecture_list = QListWidget()

        # Temporary examples just so the layout isn't empty.
        self.lecture_list.addItem("Databases and Web Development")
        self.lecture_list.addItem("Functional Programming")
        self.lecture_list.addItem("Artificial Inteligence 2")

        sidebar_layout.addWidget(self.lecture_list)

        new_lecture_button = QPushButton("+ New Lecture")
        # will be a new lecture button

        sidebar_layout.addWidget(new_lecture_button)

        main_layout.addWidget(sidebar)

        # --------------------------------------------------
        # MAIN CONTENT AREA
        # --------------------------------------------------

        content = QWidget()
        content_layout = QVBoxLayout(content)

        content_layout.setContentsMargins(30, 25, 30, 25)
        content_layout.setSpacing(18)

        main_layout.addWidget(content)

        # --------------------------------------------------
        # HEADER
        # --------------------------------------------------

        header_layout = QHBoxLayout()

        title_area = QVBoxLayout()

        self.lecture_title = QLabel("New Lecture")
        self.lecture_title.setObjectName("lectureTitle")

        self.lecture_subtitle = QLabel(
            "Start recording or import an existing lecture."
        )

        title_area.addWidget(self.lecture_title)
        title_area.addWidget(self.lecture_subtitle)

        header_layout.addLayout(title_area)

        # Push controls to the right.
        header_layout.addStretch()

        # --------------------------------------------------
        # WHISPER MODEL SELECTOR
        # --------------------------------------------------

        model_label = QLabel("Whisper model:")

        self.model_selector = QComboBox()

        self.model_selector.addItems([
            "tiny",
            "base",
            "small",
            "medium",
            "large-v3"
        ])

        self.model_selector.setCurrentText(model_size)


        header_layout.addWidget(model_label)
        header_layout.addWidget(self.model_selector)

        content_layout.addLayout(header_layout)

        # --------------------------------------------------
        # RECORDING CONTROLS
        # --------------------------------------------------

        controls = QFrame()

        controls_layout = QHBoxLayout(controls)

        self.record_button = QPushButton("● Record")
        self.stop_button = QPushButton("■ Stop")
        self.import_button = QPushButton("Import Audio")
        self.transcribe_button = QPushButton("Transcribe")
        self.generate_notes_button = QPushButton("Generate Notes")

        self.stop_button.setEnabled(False)

        # --------------------------------------------------
        # BUTTON FUNCTIONS GO HERE
        # --------------------------------------------------

        self.record_button.clicked.connect(self.start_recording)
        self.stop_button.clicked.connect(self.stop_recording)
        self.transcribe_button.clicked.connect(self.start_transcribing)
        self.generate_notes_button.clicked.connect(self.start_generating_notes)

        # self.import_button.clicked.connect(...)
        # Eventually this could open QFileDialog
        # OR become your drag-and-drop alternative.

        # self.transcribe_button.clicked.connect(...)

        # self.generate_notes_button.clicked.connect(...)
        #
        # Eventually this will call Ollama note generation.

        controls_layout.addWidget(self.record_button)
        controls_layout.addWidget(self.stop_button)

        controls_layout.addSpacing(20)

        controls_layout.addWidget(self.import_button)
        controls_layout.addWidget(self.transcribe_button)

        controls_layout.addStretch()

        controls_layout.addWidget(self.generate_notes_button)

        content_layout.addWidget(controls)

        # --------------------------------------------------
        # STATUS BAR AREA
        # --------------------------------------------------

        status_layout = QHBoxLayout()

        self.status_label = QLabel("● Idle")
        self.duration_label = QLabel("00:00:00") #doesnt do anything yet

        status_layout.addWidget(self.status_label)

        status_layout.addStretch()

        status_layout.addWidget(self.duration_label)

        content_layout.addLayout(status_layout)

        # --------------------------------------------------
        # MAIN LECTURE TABS
        # --------------------------------------------------

        self.tabs = QTabWidget()

        # -------------------
        # TRANSCRIPT TAB
        # -------------------

        transcript_page = QWidget()
        transcript_layout = QVBoxLayout(transcript_page)

        self.transcript_box = QPlainTextEdit()

        self.transcript_box.setPlaceholderText(
            "Lecture transcript will appear here..."
        )

        transcript_layout.addWidget(self.transcript_box)

        self.tabs.addTab(transcript_page, "Transcript")

        # -------------------
        # NOTES TAB
        # -------------------

        notes_page = QWidget()
        notes_layout = QVBoxLayout(notes_page)

        self.notes_box = QPlainTextEdit()

        self.notes_box.setPlaceholderText(
            "AI-generated lecture notes will appear here..."
        )

        notes_layout.addWidget(self.notes_box)

        self.tabs.addTab(notes_page, "Notes")

        # -------------------
        # SUMMARY TAB
        # -------------------

        summary_page = QWidget()
        summary_layout = QVBoxLayout(summary_page)

        self.summary_box = QPlainTextEdit()

        self.summary_box.setPlaceholderText(
            "Lecture summary will appear here..."
        )

        summary_layout.addWidget(self.summary_box)

        self.tabs.addTab(summary_page, "Summary")

        content_layout.addWidget(self.tabs)

        # --------------------------------------------------
        # BASIC TEMPORARY STYLING
        #
        # Eventually move all of this into
        # a separate style.qss file.
        # --------------------------------------------------

        self.setStyleSheet("""
            QMainWindow {
                background-color: #111318;
            }

            QWidget {
                color: #e8e8ea;
                font-size: 14px;
            }

            QFrame {
                background-color: #171a21;
            }

            QLabel#appTitle {
                font-size: 20px;
                font-weight: 700;
                padding-bottom: 10px;
            }

            QLabel#lectureTitle {
                font-size: 24px;
                font-weight: 700;
            }

            QPushButton {
                background-color: #242832;
                border: 1px solid #343945;
                border-radius: 7px;
                padding: 9px 14px;
            }

            QPushButton:hover {
                background-color: #2d323d;
            }

            QPushButton:disabled {
                color: #666a73;
                background-color: #1b1e24;
            }

            QPlainTextEdit {
                background-color: #171a21;
                border: 1px solid #2d323d;
                border-radius: 8px;
                padding: 12px;
                font-size: 14px;
            }

            QListWidget {
                background-color: transparent;
                border: none;
            }

            QListWidget::item {
                padding: 9px;
                border-radius: 6px;
            }

            QListWidget::item:selected {
                background-color: #292e39;
            }

            QComboBox {
                background-color: #242832;
                border: 1px solid #343945;
                border-radius: 6px;
                padding: 7px;
            }

            QTabWidget::pane {
                border: none;
            }

            QTabBar::tab {
                padding: 10px 18px;
            }

            QTabBar::tab:selected {
                border-bottom: 2px solid #e8e8ea;
            }
        """)
    def start_generating_notes(self):
        self.generate_notes_button.setEnabled(False)
        
        self.status_label.setText("҉ Generating")
        with open("test.txt", "r") as f:
            transcription = str(f.read())
            
        self.generating_thread = QThread()
        self.generating_worker = NoteGenerationWorker(transcription, "note_test.txt")
        
        self.generating_worker.moveToThread(self.generating_thread)
        
        self.generating_thread.started.connect(
            self.generating_worker.run
        )
        
        self.generating_worker.finished.connect(
            self.generating_finished
        )
        
        self.generating_worker.error.connect(
            self.generating_error
        )
        
        self.generating_worker.finished.connect(
            self.generating_thread.quit
        )
        
        self.generating_worker.finished.connect(
            self.generating_worker.deleteLater
        )
        
        self.generating_thread.finished.connect(
            self.generating_thread_finished
        )
        
        self.generating_worker.error.connect(
            self.generating_thread.quit
        )
        
        self.generating_worker.error.connect(
            self.generating_worker.deleteLater
        )
        
        self.generating_thread.start()
    
    @Slot()
    def generating_thread_finished(self):
        
        self.generating_thread = None
        self.generating_worker = None
    
    @Slot(str)
    def generating_finished(self, generated_file):
        self.status_label.setText("● Notes generated")
        
        self.generate_notes_button.setEnabled(True)
        
        print(f"Saved generated notes to {generated_file}")
        
    @Slot(str)
    def generating_error(self, error_message):
        self.status_label.setText("● Generating error")
        
        self.generate_notes_button.setEnabled(True)
        
        print(f"Generating error: {error_message}")
        
    def start_transcribing(self):
        self.transcribe_button.setEnabled(False)
        
        self.status_label.setText("҉ Transcribing")
        
        self.transcribing_thread = QThread()
        self.transcribing_worker = TranscribingWorker("test.txt") #temp file name
        
        self.transcribing_worker.moveToThread(self.transcribing_thread)
        
        self.transcribing_thread.started.connect(
            self.transcribing_worker.run
        )
        
        self.transcribing_worker.finished.connect(
            self.transcribing_finished
        )
        
        self.transcribing_worker.error.connect(
            self.transcribing_error
        )
        
        self.transcribing_worker.finished.connect(
            self.transcribing_thread.quit
        )
        
        self.transcribing_worker.finished.connect(
            self.transcribing_worker.deleteLater
        )
        
        self.transcribing_thread.finished.connect(
            self.transcribing_thread.deleteLater
        )
        
        self.transcribing_thread.finished.connect(
            self.transcribing_thread_finished
        )
        
        self.transcribing_worker.error.connect(
            self.transcribing_thread.quit
        )
        
        self.transcribing_worker.error.connect(
            self.transcribing_worker.deleteLater
        )
        
        self.transcribing_thread.start()
        
    @Slot()
    def transcribing_thread_finished(self):
        
        self.transcribing_thread = None
        self.transcribing_worker = None
        
    @Slot(str)
    def transcribing_finished(self, transcribed_file):
        self.status_label.setText("● Transcribing saved")
        
        self.transcribe_button.setEnabled(True)
        
        print(f"Saved transcription to {transcribed_file}")
    
    @Slot(str)
    def transcribing_error(self, error_message):
        self.status_label.setText("● Transcribing error")
        
        self.transcribe_button.setEnabled(True)
        
        print(f"Transcribing error: {error_message}")

    @Slot(str)
    def recording_finished(self, recorded_file):
        self.status_label.setText("● Recording saved")

        self.record_button.setEnabled(True)
        self.stop_button.setEnabled(False)

        print(f"Saved recording to {recorded_file}")

    @Slot(str)
    def recording_error(self, error_message):
        self.status_label.setText("● Recording error")

        self.record_button.setEnabled(True)
        self.stop_button.setEnabled(False)

        print(f"Recording error: {error_message}")
    
    @Slot()
    def recording_thread_finished(self):
        
        self.record_thread = None
        self.recording_worker = None
        
    def start_recording(self):
        self.record_button.setEnabled(False)
        self.stop_button.setEnabled(True)

        self.status_label.setText("● Recording")

        self.record_thread = QThread()
        self.recording_worker = RecordingWorker()

        self.recording_worker.moveToThread(self.record_thread)

        self.record_thread.started.connect(
            self.recording_worker.run
        )

        self.recording_worker.finished.connect(
            self.recording_finished
        )

        self.recording_worker.error.connect(
            self.recording_error
        )

        self.recording_worker.finished.connect(
            self.record_thread.quit
        )

        self.recording_worker.finished.connect(
            self.recording_worker.deleteLater
        )

        self.record_thread.finished.connect(
            self.record_thread.deleteLater
        )
        
        self.record_thread.finished.connect(
            self.recording_thread_finished
        )
        
        self.recording_worker.error.connect(
            self.record_thread.quit
        )
        
        self.recording_worker.error.connect(
            self.recording_worker.deleteLater
        )
        

        self.record_thread.start()
    

    def stop_recording(self):
        if self.record_thread is not None:
            self.status_label.setText("● Stopping...")
            self.stop_button.setEnabled(False)

            self.record_thread.requestInterruption()
        
# ==========================================================
# BACKEND
# ==========================================================


def transcribe(file):
    print("Transcribing")

    model = WhisperModel(
        model_size,
        device="cpu",
        compute_type="int8"
    )

    segments, info = model.transcribe(
        file,
        beam_size=5
    )

    to_txt(segments)

    print("Transcription finished")

    return


def to_txt(segments):
    with open("test.txt", "w") as f:
        for segment in segments:
            f.write(f"{segment.text}\n")

        f.close()

    return


# ==========================================================
# APPLICATION START
# ==========================================================

if __name__ == "__main__":

    app = QApplication(sys.argv)

    window = MainWindow()
    window.show()

    sys.exit(app.exec())