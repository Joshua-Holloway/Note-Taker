import pyaudio, wave, sys
from faster_whisper import WhisperModel
from PySide6.QtWidgets import QApplication, QPushButton, QMainWindow, QLabel, QLineEdit, QTextEdit, QComboBox, QCheckBox, QProgressBar, QTabWidget, QListWidget, QStackedWidget
from PySide6.QtCore import Slot

@Slot()
def hello():
    print("Button clicked, sup")

app = QApplication(sys.argv)
button = QPushButton("click me")
button.clicked.connect(hello)
button.show()
app.exec()

model_size = "small"
chunk = 1024  # Record in chunks of 1024 samples
sample_format = pyaudio.paInt16  # 16 bits per sample
channels = 1
fs = 44100  # Record at 44100 samples per second
seconds = 10
filename = "output.wav"

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        
        self.setWindowTitle("Lecture Assistant")
        self.resize(1200, 800)
def record():
    p = pyaudio.PyAudio()  # Create an interface to PortAudio

    print("Recording")

    stream = p.open(format=sample_format,
                    channels=channels,
                    rate=fs,
                    frames_per_buffer=chunk,
                    input=True)

    frames = []  # Initialize array to store frames

    # Store data in chunks for 3 seconds
    for i in range(0, int(fs / chunk * seconds)):
        data = stream.read(chunk)
        frames.append(data)

    # Stop and close the stream 
    stream.stop_stream()
    stream.close()
    # Terminate the PortAudio interface
    p.terminate()

    print("Recording finished")

    # Save the recorded data as a WAV file
    wf = wave.open(filename, 'wb')
    wf.setnchannels(channels)
    wf.setsampwidth(p.get_sample_size(sample_format))
    wf.setframerate(fs)
    wf.writeframes(b''.join(frames))
    wf.close()
    
    return filename

def transcribe(file):
    print("Transcribing")
    model = WhisperModel(model_size, device="cpu", compute_type="int8")
    # Run on GPU with FP16
    # model = WhisperModel(model_size, device="cuda", compute_type="float16")
    # or run on GPU with INT8
    # model = WhisperModel(model_size, device="cuda", compute_type="int8_float16")
    # or run on CPU with INT8
    # model = WhisperModel(model_size, device="cpu", compute_type="int8")

    segments, info = model.transcribe(file, beam_size=5)
    
    to_txt(segments)
    
    print("Transcription finished")
    
    return

def to_txt(segments):
    with open("test.txt", "w") as f:
        for segment in segments:
            f.write(f"{segment.text}\n")
        f.close()
    return

if __name__ == "__main__":
    file = filename
    
    '''
    while True:
        user_input = input("Input: ")
        if user_input.lower() == "record":
            transcribe(record())
        elif user_input.lower() == "transcribe":
            transcribe(file)
        elif user_input.lower() == "exit":
            break
        else:
            print("Unknown input")
        '''