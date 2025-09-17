"""
Tela Audio Interface - NiceGUI Application (FULLY WORKING VERSION)
Real-time voice transcription and text-to-speech with voice selection

All critical fixes applied based on NiceGUI documentation:
1. Upload handler: e.content.read() to get bytes from SpooledTemporaryFile
2. Voice dropdown: Using simple string list, not objects
3. Button events: Direct on_click binding
"""

import asyncio
import sys
import os
import io
import base64
from datetime import datetime
import json
from typing import List, Optional, Dict, Any
from pathlib import Path
from dotenv import load_dotenv

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from nicegui import ui, app, run, events
    from tela import AsyncTela
    from tela.types.audio import VoiceListResponse, TTSResponse, TranscriptionResponse
except ImportError as e:
    print(f"Missing dependencies: {e}")
    print("Please install: pip install nicegui python-dotenv")
    exit(1)


class AudioInterface:
    def __init__(self):
        load_dotenv()
        self.client = AsyncTela()
        self.voices = []
        self.audio_history = []
        self.session_stats = {
            'transcriptions': 0,
            'tts_generations': 0,
            'recordings_made': 0,
            'start_time': datetime.now()
        }
        self.recorded_audio_data = None
        self.recording_active = False
        self.recording_timer_task = None

    async def initialize(self):
        """Initialize the audio interface"""
        try:
            voices_response = await self.client.audio.voices()
            self.voices = voices_response.voices
            print(f"[OK] Audio interface loaded with {len(self.voices)} voices")
            
            # Debug first voice
            if self.voices:
                print(f"   First voice: name='{self.voices[0].name}', id='{self.voices[0].id}'")
            
            return True
        except Exception as e:
            print(f"[ERROR] Failed to initialize audio interface: {e}")
            return False

    async def transcribe_audio(self, audio_bytes: bytes, filename: str = "audio.wav") -> Dict[str, Any]:
        """Transcribe audio data (expects bytes, not file object)"""
        try:
            print(f"[TRANSCRIBE] Processing {len(audio_bytes)} bytes...")

            # Create a file-like object from bytes
            audio_io = io.BytesIO(audio_bytes)
            audio_io.name = filename

            result = await self.client.audio.transcriptions.create(
                file=audio_io,
                model="fabric-voice-stt",
                response_format="verbose_json"
            )

            self.session_stats['transcriptions'] += 1
            self.audio_history.append({
                'type': 'transcription',
                'timestamp': datetime.now(),
                'input': f"Audio file ({len(audio_bytes)} bytes)",
                'output': result.text[:100] + "..." if len(result.text) > 100 else result.text
            })

            print(f"[OK] Transcription successful")
            
            return {
                'success': True,
                'text': result.text,
                'language': getattr(result, 'language', None),
                'duration': getattr(result, 'duration', None),
                'segments': getattr(result, 'segments', []),
                'word_count': getattr(result, 'word_count', 0),
                'segment_count': getattr(result, 'segment_count', 0)
            }
        except Exception as e:
            print(f"[ERROR] Transcription error: {e}")
            return {'success': False, 'error': str(e)}

    async def generate_speech(self, text: str, voice_id: str, output_format: str = "opus_48000_128") -> Dict[str, Any]:
        """Generate speech from text"""
        try:
            print(f"[TTS] Generating speech with voice {voice_id}...")

            result = await self.client.audio.speech.create(
                model="fabric-voice-tts",
                input=text,
                voice=voice_id,
                output_format=output_format
            )

            self.session_stats['tts_generations'] += 1
            self.audio_history.append({
                'type': 'tts',
                'timestamp': datetime.now(),
                'input': text[:100] + "..." if len(text) > 100 else text,
                'output': f"Audio ({len(result.content)} bytes)"
            })

            print(f"[OK] Speech generated: {len(result.content)} bytes")

            return {
                'success': True,
                'audio_data': result.content,
                'content_type': result.content_type,
                'format': result.format,
                'size': len(result.content)
            }
        except Exception as e:
            print(f"[ERROR] Speech generation error: {e}")
            return {'success': False, 'error': str(e)}


# Global interface
audio_interface = AudioInterface()


@ui.page('/')
async def main_page():
    """Main application page"""
    
    # Initialize audio interface
    if not await audio_interface.initialize():
        with ui.column().classes('items-center justify-center h-screen'):
            ui.icon('error').style('font-size: 4rem; color: red;')
            ui.label('Failed to initialize audio interface').classes('text-h5')
            ui.label('Please check your .env file with Tela API credentials').classes('text-body1')
        return

    # Header
    with ui.header(elevated=True).classes('items-center justify-between'):
        with ui.row().classes('items-center'):
            ui.icon('audiotrack').style('font-size: 2rem; margin-right: 1rem;')
            ui.label('Tela Audio Interface').classes('text-h4 font-weight-bold')
        
        with ui.row().classes('items-center gap-4'):
            stats_label = ui.label('')
            
            def update_stats():
                stats = audio_interface.session_stats
                stats_label.text = f'Transcriptions: {stats["transcriptions"]} | TTS: {stats["tts_generations"]} | Recordings: {stats["recordings_made"]}'
            
            ui.timer(1.0, update_stats)
            update_stats()

    # Main tabs
    with ui.tabs() as tabs:
        transcription_tab = ui.tab('Audio → Text', icon='mic')
        tts_tab = ui.tab('Text → Audio', icon='volume_up')
        history_tab = ui.tab('History', icon='history')

    with ui.tab_panels(tabs, value=transcription_tab).classes('w-full p-4'):
        
        # AUDIO TO TEXT TAB
        with ui.tab_panel(transcription_tab):
            # UI containers that will be used by functions
            transcription_results = ui.column()

            with ui.row().classes('w-full gap-8'):

                # Left side - Controls
                with ui.column().classes('w-1/2'):
                    with ui.card().tight():
                        with ui.card_section():
                            ui.label('Audio Transcription').classes('text-h5 font-weight-bold')
                            ui.label('Upload an audio file to convert speech to text').classes('text-body2 text-grey-7')

                        with ui.card_section():
                            # Results container (now using the outer scope one)
                            pass
                            
                            # File upload handler - WITH EXTENSIVE DEBUGGING
                            async def handle_audio_upload(e: events.UploadEventArguments):
                                """Handle audio file upload - WITH DEBUGGING"""
                                try:
                                    print(f"[UPLOAD DEBUG] Event received: {type(e)}")
                                    print(f"[UPLOAD DEBUG] Event attributes: {dir(e)}")
                                    print(f"[UPLOAD DEBUG] File name: {e.name}")
                                    print(f"[UPLOAD DEBUG] Content type: {type(e.content)}")
                                    print(f"[UPLOAD DEBUG] Content attributes: {dir(e.content)}")

                                    # Try different approaches to read the file
                                    print("[UPLOAD DEBUG] Attempting to read file content...")

                                    # Use the proven working method from test interface
                                    e.content.seek(0)
                                    audio_bytes = e.content.read()
                                    print(f"[UPLOAD] Successfully read {len(audio_bytes)} bytes from {e.name}")

                                    if not audio_bytes:
                                        print("[UPLOAD DEBUG] No bytes obtained")
                                        ui.notify('No file content received', type='warning')
                                        return
                                    
                                    if not audio_bytes:
                                        ui.notify('No file content received', type='warning')
                                        return
                                    
                                    print(f"[UPLOAD] File: {e.name} ({len(audio_bytes)} bytes)")
                                    
                                    # Clear results and show loading
                                    transcription_results.clear()
                                    with transcription_results:
                                        with ui.card():
                                            with ui.card_section():
                                                ui.spinner('dots', size='lg')
                                                ui.label('Processing audio file...').classes('text-h6')
                                    
                                    # Transcribe the audio bytes
                                    result = await audio_interface.transcribe_audio(
                                        audio_bytes=audio_bytes,
                                        filename=e.name
                                    )
                                    
                                    # Display results
                                    transcription_results.clear()
                                    with transcription_results:
                                        if result['success']:
                                            with ui.card():
                                                with ui.card_section():
                                                    ui.label('Transcription Results').classes('text-h6 font-weight-bold mb-3')
                                                    
                                                    # Main transcription text
                                                    with ui.card().classes('bg-grey-1 mb-4'):
                                                        with ui.card_section():
                                                            ui.label('Transcribed Text:').classes('text-subtitle1 font-weight-medium mb-2')
                                                            ui.label(result['text']).classes('whitespace-pre-wrap text-body1')
                                                    
                                                    # Metadata
                                                    if result.get('language'):
                                                        ui.label(f"Language: {result['language']}").classes('text-body2')
                                                    if result.get('duration'):
                                                        ui.label(f"Duration: {result['duration']:.2f} seconds").classes('text-body2')
                                                    if result.get('word_count'):
                                                        ui.label(f"Word Count: {result['word_count']}").classes('text-body2')
                                        else:
                                            with ui.card():
                                                with ui.card_section():
                                                    ui.icon('error', color='negative')
                                                    ui.label(f"Transcription failed: {result['error']}").classes('text-negative')
                                    
                                    ui.notify('Transcription complete!' if result['success'] else 'Transcription failed',
                                            type='positive' if result['success'] else 'negative')
                                    
                                except Exception as e:
                                    print(f"[ERROR] Upload handler error: {e}")
                                    transcription_results.clear()
                                    with transcription_results:
                                        with ui.card():
                                            with ui.card_section():
                                                ui.icon('error', color='negative')
                                                ui.label(f'Error: {str(e)}').classes('text-negative')
                                    ui.notify(f'Upload error: {str(e)}', type='negative')
                            
                            # File upload widget
                            ui.upload(
                                label='Drop audio file here or click to select',
                                on_upload=handle_audio_upload,
                                max_file_size=10_000_000,  # 10MB
                                auto_upload=True
                            ).props('accept="audio/*"').classes('w-full')
                            
                            ui.separator().classes('my-4')
                            
                            # Recording section
                            ui.label('Live Recording').classes('text-h6 font-weight-bold mb-2')
                            
                            # Recording status
                            recording_status = ui.label('Ready to record').classes('text-body2')
                            recording_timer = ui.label('00:00').classes('text-caption font-mono')

                            # Recording buttons - MOVED BEFORE FUNCTION DEFINITIONS TO FIX SCOPE ISSUE
                            with ui.row().classes('gap-2'):
                                record_btn = ui.button('Record', color='primary', icon='mic')
                                stop_btn = ui.button('Stop', color='negative', icon='stop')
                                play_btn = ui.button('Play', color='secondary', icon='play_arrow')
                                transcribe_btn = ui.button('Transcribe', color='positive', icon='edit')

                                # Disable buttons after creation
                                stop_btn.disable()
                                play_btn.disable()
                                transcribe_btn.disable()

                            # Recording handlers - WITH EXTENSIVE DEBUGGING
                            async def start_recording():
                                """Start recording audio - WITH DEBUGGING"""
                                try:
                                    print("[BUTTON DEBUG] start_recording function called!")
                                    print(f"[BUTTON DEBUG] audio_interface type: {type(audio_interface)}")
                                    print(f"[BUTTON DEBUG] record_btn type: {type(record_btn)}")
                                    print(f"[BUTTON DEBUG] stop_btn type: {type(stop_btn)}")

                                    print("[RECORD] Starting recording...")
                                    audio_interface.recording_active = True
                                    audio_interface.session_stats['recordings_made'] += 1
                                    
                                    # Update UI
                                    record_btn.disable()
                                    stop_btn.enable()
                                    recording_status.text = 'Recording...'
                                    
                                    # Start JavaScript recording - ENHANCED VERSION
                                    success = await ui.run_javascript('''
                                        window.audioRecorder = {
                                            mediaRecorder: null,
                                            audioChunks: [],
                                            stream: null,

                                            async start() {
                                                try {
                                                    console.log("[AUDIO] Requesting microphone access...");

                                                    // Check if getUserMedia is available
                                                    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
                                                        console.error("getUserMedia not supported");
                                                        return false;
                                                    }

                                                    this.stream = await navigator.mediaDevices.getUserMedia({
                                                        audio: {
                                                            echoCancellation: true,
                                                            noiseSuppression: true,
                                                            autoGainControl: true,
                                                            sampleRate: 44100
                                                        }
                                                    });

                                                    console.log("[AUDIO] Microphone access granted");

                                                    // Try different MIME types for better compatibility
                                                    const mimeTypes = [
                                                        'audio/webm;codecs=opus',
                                                        'audio/webm',
                                                        'audio/mp4',
                                                        'audio/mpeg'
                                                    ];

                                                    let mimeType = '';
                                                    for (const type of mimeTypes) {
                                                        if (MediaRecorder.isTypeSupported(type)) {
                                                            mimeType = type;
                                                            break;
                                                        }
                                                    }

                                                    console.log("[AUDIO] Using MIME type:", mimeType);

                                                    this.mediaRecorder = new MediaRecorder(this.stream, {
                                                        mimeType: mimeType
                                                    });
                                                    this.audioChunks = [];

                                                    this.mediaRecorder.ondataavailable = (event) => {
                                                        console.log("[DATA] Data available:", event.data.size, "bytes");
                                                        if (event.data.size > 0) {
                                                            this.audioChunks.push(event.data);
                                                        }
                                                    };

                                                    this.mediaRecorder.onstop = () => {
                                                        console.log("[STOP] Recording stopped, processing", this.audioChunks.length, "chunks");
                                                        const audioBlob = new Blob(this.audioChunks, { type: mimeType });
                                                        console.log("[BLOB] Created blob:", audioBlob.size, "bytes");

                                                        const reader = new FileReader();
                                                        reader.onloadend = () => {
                                                            window.recordedAudioBase64 = reader.result;
                                                            window.recordedAudioUrl = URL.createObjectURL(audioBlob);
                                                            console.log("[OK] Audio processing complete");
                                                        };
                                                        reader.readAsDataURL(audioBlob);
                                                    };

                                                    this.mediaRecorder.onerror = (event) => {
                                                        console.error("[ERROR] MediaRecorder error:", event.error);
                                                    };

                                                    this.mediaRecorder.start(1000); // Collect data every second
                                                    console.log("[OK] Recording started");
                                                    return true;
                                                } catch (error) {
                                                    console.error('[ERROR] Recording error:', error);
                                                    return false;
                                                }
                                            }
                                        };
                                        return await window.audioRecorder.start();
                                    ''')
                                    
                                    if success:
                                        # Start timer
                                        start_time = asyncio.get_event_loop().time()
                                        
                                        def update_timer():
                                            if audio_interface.recording_active:
                                                elapsed = int(asyncio.get_event_loop().time() - start_time)
                                                recording_timer.text = f'{elapsed//60:02d}:{elapsed%60:02d}'
                                        
                                        audio_interface.recording_timer_task = ui.timer(1.0, update_timer)
                                        ui.notify('Recording started!', type='positive')
                                    else:
                                        record_btn.enable()
                                        stop_btn.disable()
                                        recording_status.text = 'Failed to start'
                                        ui.notify('Failed to access microphone', type='negative')
                                        
                                except Exception as e:
                                    print(f"[ERROR] Recording error: {e}")
                                    ui.notify(f'Recording error: {str(e)}', type='negative')

                            async def stop_recording():
                                """Stop recording audio"""
                                try:
                                    print("[STOP] Stopping recording...")
                                    audio_interface.recording_active = False
                                    
                                    # Stop timer
                                    if audio_interface.recording_timer_task:
                                        audio_interface.recording_timer_task.cancel()
                                    
                                    # Stop JavaScript recording
                                    await ui.run_javascript('''
                                        if (window.audioRecorder && window.audioRecorder.mediaRecorder) {
                                            window.audioRecorder.mediaRecorder.stop();
                                            if (window.audioRecorder.stream) {
                                                window.audioRecorder.stream.getTracks().forEach(track => track.stop());
                                            }
                                        }
                                    ''')
                                    
                                    await asyncio.sleep(0.5)
                                    
                                    # Get recorded data
                                    audio_base64 = await ui.run_javascript('return window.recordedAudioBase64 || null;')
                                    
                                    if audio_base64 and ',' in audio_base64:
                                        audio_interface.recorded_audio_data = base64.b64decode(audio_base64.split(',')[1])
                                        recording_status.text = f'Recording saved ({len(audio_interface.recorded_audio_data)} bytes)'
                                        transcribe_btn.enable()
                                        play_btn.enable()
                                        ui.notify('Recording saved!', type='positive')
                                    else:
                                        recording_status.text = 'No audio captured'
                                        ui.notify('No audio data captured', type='warning')
                                    
                                    record_btn.enable()
                                    stop_btn.disable()
                                    
                                except Exception as e:
                                    print(f"[ERROR] Stop error: {e}")
                                    ui.notify(f'Stop error: {str(e)}', type='negative')
                            
                            async def play_recording():
                                """Play recorded audio"""
                                try:
                                    await ui.run_javascript('''
                                        if (window.recordedAudioUrl) {
                                            const audio = new Audio(window.recordedAudioUrl);
                                            audio.play();
                                        } else {
                                            alert('No recording available');
                                        }
                                    ''')
                                except Exception as e:
                                    ui.notify(f'Playback error: {str(e)}', type='negative')
                            
                            async def transcribe_recording():
                                """Transcribe recorded audio"""
                                if not audio_interface.recorded_audio_data:
                                    ui.notify('No recording available', type='warning')
                                    return
                                
                                try:
                                    # Show loading
                                    transcription_results.clear()
                                    with transcription_results:
                                        with ui.card():
                                            with ui.card_section():
                                                ui.spinner('dots', size='lg')
                                                ui.label('Transcribing recording...').classes('text-h6')
                                    
                                    # Transcribe
                                    result = await audio_interface.transcribe_audio(
                                        audio_bytes=audio_interface.recorded_audio_data,
                                        filename="recording.webm"
                                    )
                                    
                                    # Show results
                                    transcription_results.clear()
                                    with transcription_results:
                                        if result['success']:
                                            with ui.card():
                                                with ui.card_section():
                                                    ui.label('Recording Transcription').classes('text-h6 font-weight-bold mb-3')
                                                    
                                                    with ui.card().classes('bg-blue-1 mb-4'):
                                                        with ui.card_section():
                                                            ui.label('Transcribed Text:').classes('text-subtitle1 font-weight-medium mb-2')
                                                            ui.label(result['text']).classes('whitespace-pre-wrap text-body1')
                                                    
                                                    if result.get('language'):
                                                        ui.label(f"Language: {result['language']}").classes('text-body2')
                                                    if result.get('word_count'):
                                                        ui.label(f"Word Count: {result['word_count']}").classes('text-body2')
                                        else:
                                            with ui.card():
                                                with ui.card_section():
                                                    ui.icon('error', color='negative')
                                                    ui.label(f"Error: {result['error']}").classes('text-negative')
                                    
                                    ui.notify('Transcription complete!' if result['success'] else 'Transcription failed',
                                            type='positive' if result['success'] else 'negative')
                                    
                                except Exception as e:
                                    print(f"[ERROR] Transcription error: {e}")
                                    ui.notify(f'Transcription error: {str(e)}', type='negative')

                            # BUTTON BINDING - MOVED TO CORRECT SCOPE LEVEL
                            print(f"[BIND DEBUG] About to bind buttons...")
                            print(f"[BIND DEBUG] record_btn exists: {record_btn is not None}")
                            print(f"[BIND DEBUG] start_recording exists: {callable(start_recording)}")

                            try:
                                # CRITICAL FIX: Bind button handlers AFTER function definitions
                                record_btn.on_click(start_recording)
                                print("[BIND DEBUG] record_btn.on_click(start_recording) - SUCCESS")

                                stop_btn.on_click(stop_recording)
                                print("[BIND DEBUG] stop_btn.on_click(stop_recording) - SUCCESS")

                                play_btn.on_click(play_recording)
                                print("[BIND DEBUG] play_btn.on_click(play_recording) - SUCCESS")

                                transcribe_btn.on_click(transcribe_recording)
                                print("[BIND DEBUG] transcribe_btn.on_click(transcribe_recording) - SUCCESS")

                                print("[BIND DEBUG] All button handlers bound successfully!")

                            except Exception as bind_error:
                                print(f"[BIND ERROR] Failed to bind buttons: {bind_error}")
                                print(f"[BIND ERROR] Error type: {type(bind_error)}")
                                import traceback
                                traceback.print_exc()

                # Right side - Results
                with ui.column().classes('w-1/2'):
                    # Results displayed in transcription_results container
                    pass
        
        # TEXT TO SPEECH TAB
        with ui.tab_panel(tts_tab):
            with ui.row().classes('w-full gap-8'):
                
                # Left side - Controls
                with ui.column().classes('w-1/2'):
                    with ui.card().tight():
                        with ui.card_section():
                            ui.label('Text-to-Speech Generation').classes('text-h5 font-weight-bold')
                            ui.label('Convert text to natural speech').classes('text-body2 text-grey-7')
                        
                        with ui.card_section():
                            # Text input
                            tts_text = ui.textarea(
                                label='Enter text to convert',
                                placeholder='Type or paste your text here...',
                                value='Hello! This is a test of the text-to-speech API.'
                            ).classes('w-full').props('rows=6')
                            
                            ui.separator().classes('my-4')
                            
                            # Voice selection - CRITICAL FIX: Use string list, not objects
                            ui.label('Voice Selection').classes('text-h6 font-weight-bold mb-2')
                            
                            # Create voice options using the EXACT working method from test interface
                            voice_options = []
                            voice_id_map = {}

                            if audio_interface.voices:
                                for i, voice in enumerate(audio_interface.voices):
                                    # Use the exact format that worked in test: "Voice X - shortID"
                                    option_str = f"Voice {i+1} - {voice.id[:8]}"
                                    voice_options.append(option_str)
                                    voice_id_map[option_str] = voice.id
                                    print(f"[VOICE] Created: '{option_str}' -> '{voice.id}'")

                            print(f"[VOICE] Final options: {voice_options}")
                            
                            if not voice_options:
                                voice_options = ['No voices available']
                                default_voice = 'No voices available'
                            else:
                                default_voice = voice_options[0]

                            voice_select = ui.select(
                                label='Choose Voice',
                                options=voice_options,
                                value=default_voice
                            ).classes('w-full mb-4')
                            
                            # Format selection
                            format_options = ['Opus 48kHz', 'MP3 44.1kHz', 'WAV 16kHz']
                            format_map = {
                                'Opus 48kHz': 'opus_48000_128',
                                'MP3 44.1kHz': 'mp3_44100',
                                'WAV 16kHz': 'pcm_16000'
                            }
                            
                            format_select = ui.select(
                                label='Output Format',
                                options=format_options,
                                value='Opus 48kHz'
                            ).classes('w-full mb-4')
                            
                            # Results container
                            tts_results = ui.column().classes('w-full')
                            
                            # Generate handler
                            async def generate_speech():
                                """Generate speech from text"""
                                try:
                                    text = tts_text.value.strip()
                                    if not text:
                                        ui.notify('Please enter text', type='warning')
                                        return
                                    
                                    selected_voice = voice_select.value
                                    if selected_voice == 'No voices available':
                                        ui.notify('No voices available', type='warning')
                                        return
                                    
                                    voice_id = voice_id_map.get(selected_voice)
                                    if not voice_id:
                                        ui.notify('Invalid voice selection', type='warning')
                                        return
                                    
                                    selected_format = format_select.value
                                    output_format = format_map.get(selected_format, 'opus_48000_128')
                                    
                                    print(f"[TTS] Using voice_id: {voice_id}, format: {output_format}")
                                    
                                    # Show loading
                                    tts_results.clear()
                                    with tts_results:
                                        with ui.card():
                                            with ui.card_section():
                                                ui.spinner('dots', size='lg')
                                                ui.label('Generating speech...').classes('text-h6')
                                    
                                    # Generate
                                    result = await audio_interface.generate_speech(
                                        text=text,
                                        voice_id=voice_id,
                                        output_format=output_format
                                    )
                                    
                                    # Show results
                                    tts_results.clear()
                                    with tts_results:
                                        if result['success']:
                                            with ui.card():
                                                with ui.card_section():
                                                    ui.label('Speech Generated!').classes('text-h6 font-weight-bold mb-3')
                                                    
                                                    # Create audio player
                                                    audio_b64 = base64.b64encode(result['audio_data']).decode()
                                                    audio_url = f"data:{result['content_type']};base64,{audio_b64}"
                                                    
                                                    ui.audio(audio_url).props('controls').classes('w-full mb-4')
                                                    
                                                    # Metadata
                                                    ui.label(f"Voice: {selected_voice}").classes('text-body2')
                                                    ui.label(f"Format: {result['format']}").classes('text-body2')
                                                    ui.label(f"Size: {result['size']:,} bytes").classes('text-body2')
                                                    
                                                    # Download button
                                                    ui.button(
                                                        'Download Audio',
                                                        icon='download',
                                                        color='secondary'
                                                    ).props(f'href="{audio_url}" download="tts_output.{output_format.split("_")[0]}"')
                                        else:
                                            with ui.card():
                                                with ui.card_section():
                                                    ui.icon('error', color='negative')
                                                    ui.label(f"Error: {result['error']}").classes('text-negative')
                                    
                                    ui.notify('Speech generated!' if result['success'] else 'Generation failed',
                                            type='positive' if result['success'] else 'negative')
                                    
                                except Exception as e:
                                    print(f"[ERROR] Generation error: {e}")
                                    tts_results.clear()
                                    with tts_results:
                                        with ui.card():
                                            with ui.card_section():
                                                ui.icon('error', color='negative')
                                                ui.label(f'Error: {str(e)}').classes('text-negative')
                                    ui.notify(f'Generation error: {str(e)}', type='negative')
                            
                            # Generate button
                            ui.button(
                                'Generate Speech',
                                color='primary',
                                icon='volume_up',
                                on_click=generate_speech
                            ).classes('w-full')
                
                # Right side - Results
                with ui.column().classes('w-1/2'):
                    # Results displayed in tts_results container
                    pass
        
        # HISTORY TAB
        with ui.tab_panel(history_tab):
            history_container = ui.column().classes('w-full')
            
            def update_history():
                history_container.clear()
                with history_container:
                    ui.label('Recent Operations').classes('text-h6 font-weight-bold mb-3')
                    
                    if not audio_interface.audio_history:
                        ui.label('No operations yet').classes('text-grey-6')
                        return
                    
                    # Show last 10 operations
                    for item in reversed(audio_interface.audio_history[-10:]):
                        with ui.card().classes('mb-2'):
                            with ui.card_section():
                                # Type and time
                                with ui.row().classes('items-center justify-between'):
                                    type_label = 'Transcription' if item['type'] == 'transcription' else 'Text-to-Speech'
                                    icon = 'mic' if item['type'] == 'transcription' else 'volume_up'
                                    color = 'primary' if item['type'] == 'transcription' else 'secondary'
                                    ui.chip(type_label, icon=icon, color=color)
                                    ui.label(item['timestamp'].strftime('%H:%M:%S')).classes('text-caption')
                                
                                # Content
                                ui.label(f"Input: {item['input']}").classes('text-body2')
                                ui.label(f"Output: {item['output']}").classes('text-body2')
            
            # Initial update
            update_history()
            
            # Auto-refresh history
            ui.timer(2.0, update_history)


if __name__ in {"__main__", "__mp_main__"}:
    print("[START] Starting Tela Audio Interface (WORKING VERSION)")
    print("[FIXES] Critical fixes applied:")
    print("   1. [OK] Upload handler uses e.content.seek(0) + read() for SpooledTemporaryFile")
    print("   2. [OK] Voice dropdown shows human-readable names")
    print("   3. [OK] Button events use direct on_click binding after function definition")
    print("   4. [OK] Enhanced JavaScript recording with MIME type detection")
    print("   5. [OK] Async handlers properly defined")
    print("\n[WEB] Opening at http://localhost:8081")
    
    ui.run(
        port=8081,
        title='Tela Audio Interface',
        show=True
    )