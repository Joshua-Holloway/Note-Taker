# Lecture Assistant

A local desktop application for recording lectures, importing existing lecture material, transcribing audio and generating structured revision notes using AI.

The application is built in Python using PySide6, faster-whisper and Ollama.

The current version provides the core functionality required to record or import lecture material and convert it into usable revision notes.

## Features

### Lecture recording

Record audio directly from the application using the system microphone.

Recordings are saved locally and can then be transcribed using Whisper.

### Audio and video transcription

The application supports importing common audio and video formats, including:

- `.wav`
- `.mp3`
- `.m4a`
- `.mp4`
- `.webm`
- `.mkv`

Imported media can be transcribed using `faster-whisper`.

The Whisper model can be selected from within the application:

- tiny
- base
- small
- medium
- large-v3

### Document importing

Lecture material can also be imported directly from:

- `.txt`
- `.pdf`
- `.docx`
- `.pptx`

Text is extracted from the document and can then be sent directly to the note-generation system without requiring transcription.

PowerPoint files are processed slide-by-slide so that the original lecture structure is preserved as much as possible.

### AI-generated revision notes

Extracted or transcribed lecture content can be processed locally using Ollama.

The current model is:

```text
qwen3:4b
```

The note-generation prompt is designed to:

- cover the entire lecture;
- preserve important definitions and examples;
- maintain the conceptual order of the source;
- preserve technical syntax such as JDL, SQL and code;
- avoid inventing coursework or assessment requirements;
- produce structured Markdown revision notes;
- generate key definitions, rules, revision points and summaries.

The application currently uses a larger Ollama context window so that longer lecture material can be processed in a single request.

## Application flow

The basic workflow is:

```text
Record lecture
      ↓
Audio file
      ↓
Whisper transcription
      ↓
Text
      ↓
Ollama
      ↓
Revision notes
```

Imported audio and video follow the same transcription process:

```text
MP3 / MP4 / WAV / other media
              ↓
        faster-whisper
              ↓
             Text
              ↓
            Ollama
              ↓
        Revision notes
```

Documents can bypass transcription entirely:

```text
PDF / DOCX / PPTX / TXT
           ↓
      Text extraction
           ↓
          Ollama
           ↓
     Revision notes
```

The aim is for every supported source format to eventually become plain text before being sent to the same note-generation pipeline.

## Technologies

The application currently uses:

- Python
- PySide6
- PyAudio
- faster-whisper
- Ollama
- Qwen3
- PyMuPDF
- python-docx
- python-pptx

## Requirements

Python 3 is required.

Install the main Python dependencies with:

```bash
pip install pyside6 pyaudio faster-whisper ollama pymupdf python-docx python-pptx
```

Ollama must also be installed separately.

Download Ollama from:

```text
https://ollama.com/
```

The current note-generation model can then be installed with:

```bash
ollama pull qwen3:4b
```

You can verify that the model is installed with:

```bash
ollama list
```

## Running the application

Run the main Python file:

```bash
python main.py
```

Replace `main.py` with the actual filename if the project entry point has a different name.

## Using the application

### Recording a lecture

1. Press **Record**.
2. Speak or allow the lecture audio to play.
3. Press **Stop**.
4. Press **Transcribe**.
5. Wait for Whisper to generate the transcript.
6. Press **Generate Notes**.
7. The generated revision notes will appear in the Notes section.

### Importing audio or video

1. Press **Import File**.
2. Select a supported media file.
3. Press **Transcribe**.
4. Once transcription is complete, press **Generate Notes**.

### Importing a document

1. Press **Import File**.
2. Select a PDF, DOCX, PPTX or TXT file.
3. The application extracts the available text.
4. Press **Generate Notes**.

No Whisper transcription is required for document files.

## Threading

Long-running operations are performed using Qt worker threads so that the GUI remains responsive.

Separate workers are currently used for:

- recording;
- transcription;
- note generation.

Qt signals and slots are used to communicate between workers and the main GUI thread.

Workers request their thread to stop when processing is complete, and Qt objects are cleaned up after the associated thread has finished.

## Current project status

The application is currently an early functional version / MVP.

The basic pipeline is operational:

- recording;
- audio transcription;
- media importing;
- document importing;
- text extraction;
- local AI note generation;
- transcript display;
- notes display;
- selectable Whisper models.

The application is usable, but several areas still require further development and refinement.

## Current limitations

Some known limitations include:

- scanned PDFs may not contain extractable text;
- OCR is not currently implemented;
- PowerPoint extraction primarily works with textual slide content;
- heavily visual slides may lose information during extraction;
- note quality depends on the local Ollama model;
- large lectures can take several minutes to process;
- the user interface is still an early version;
- lecture saving and management are not yet fully implemented;
- the recording duration indicator is not yet functional;
- drag-and-drop importing is not yet implemented.

## Possible future improvements

Potential future work includes:

- drag-and-drop file importing;
- lecture library and saved lecture management;
- automatic lecture titles;
- improved file organisation;
- editable transcripts;
- editable generated notes;
- exporting notes;
- better progress indicators;
- recording duration tracking;
- improved error messages;
- support for OCR on scanned PDFs;
- richer PowerPoint extraction;
- lecture summaries;
- automatic key-term extraction;
- configurable note-generation models;
- configurable note styles;
- improved handling of very long lectures.

## Privacy

The current note-generation system uses Ollama locally.

This means lecture text and generated notes can be processed on the user's own machine rather than being sent to a paid cloud AI API.

Whisper transcription is also performed locally.

## Project goal

The long-term goal is to create a desktop lecture assistant capable of taking material from several sources:

```text
Microphone
Audio
Video
PDF
Word
PowerPoint
Text
```

and converting it into:

```text
Transcript
Structured revision notes
Summary
Saved lecture material
```

through a single simple interface.

## Status

**Current state: functional MVP**

The core lecture-to-notes pipeline is working and ready for further development.
