#!/usr/bin/env python3
"""
Interface with maximum error logging to see what's really happening
"""

import asyncio
import sys
import os
import traceback
import logging
from pathlib import Path
from dotenv import load_dotenv

# Configure logging to see everything
logging.basicConfig(level=logging.DEBUG, format='[LOG] %(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

print("="*60)
print("STARTING ERROR LOGGING INTERFACE")
print("="*60)

try:
    print("[IMPORT] Importing NiceGUI...")
    from nicegui import ui, events
    print("[IMPORT] NiceGUI imported successfully")

    print("[IMPORT] Importing AsyncTela...")
    from tela import AsyncTela
    print("[IMPORT] AsyncTela imported successfully")

except ImportError as e:
    print(f"[IMPORT ERROR] {e}")
    traceback.print_exc()
    exit(1)


class ErrorLoggingInterface:
    def __init__(self):
        print("[INIT] Creating ErrorLoggingInterface...")
        load_dotenv()
        self.client = AsyncTela()
        self.voices = []
        self.initialization_error = None
        print("[INIT] ErrorLoggingInterface created")

    async def initialize(self):
        """Initialize with maximum error logging"""
        print("[INITIALIZE] Starting initialization...")
        try:
            print("[INITIALIZE] Creating AsyncTela client...")

            print("[INITIALIZE] Fetching voices from API...")
            voices_response = await self.client.audio.voices()

            print(f"[INITIALIZE] API response type: {type(voices_response)}")
            print(f"[INITIALIZE] API response attributes: {dir(voices_response)}")

            self.voices = voices_response.voices
            print(f"[INITIALIZE] Got voices: {len(self.voices)} voices")

            if self.voices:
                for i, voice in enumerate(self.voices):
                    print(f"[INITIALIZE] Voice {i}:")
                    print(f"  - Type: {type(voice)}")
                    print(f"  - ID: {voice.id}")
                    print(f"  - Name: {voice.name}")
                    print(f"  - Repr: {repr(voice)}")
                    print(f"  - Str: {str(voice)}")

            print("[INITIALIZE] Initialization successful")
            return True

        except Exception as e:
            error_msg = f"Initialization failed: {e}"
            print(f"[INITIALIZE ERROR] {error_msg}")
            traceback.print_exc()
            self.initialization_error = error_msg
            return False


# Global interface
print("[GLOBAL] Creating global interface...")
audio_interface = ErrorLoggingInterface()
print("[GLOBAL] Global interface created")


@ui.page('/')
async def main_page():
    """Page with maximum error logging"""
    print("\n" + "="*50)
    print("LOADING MAIN PAGE")
    print("="*50)

    try:
        print("[PAGE] Starting page setup...")

        # Initialize interface
        print("[PAGE] Initializing interface...")
        init_success = await audio_interface.initialize()
        print(f"[PAGE] Initialization result: {init_success}")

        if not init_success:
            print("[PAGE] Initialization failed, showing error")
            ui.label(f'Initialization Error: {audio_interface.initialization_error}').classes('text-negative text-h5')
            return

        print("[PAGE] Creating UI elements...")

        # Title
        ui.label('Error Logging Interface').classes('text-h4 mb-4')

        # Show initialization info
        ui.label(f'Voices loaded: {len(audio_interface.voices)}').classes('text-positive')

        # Test 1: Simple dropdown
        print("[PAGE] Creating simple dropdown...")
        simple_options = ['Test Option 1', 'Test Option 2', 'Test Option 3']
        print(f"[PAGE] Simple options: {simple_options}")
        print(f"[PAGE] Simple options types: {[type(x) for x in simple_options]}")

        ui.label('Simple Test Dropdown:').classes('text-h6 mt-4')
        simple_select = ui.select(options=simple_options, value=simple_options[0])
        print("[PAGE] Simple dropdown created successfully")

        # Test 2: Voice dropdown with detailed logging
        print("[PAGE] Creating voice dropdown...")
        voice_options = []

        if audio_interface.voices:
            print("[PAGE] Processing voices for dropdown...")

            for i, voice in enumerate(audio_interface.voices):
                print(f"[PAGE] Processing voice {i}:")

                try:
                    # Try different ways to create a string
                    option_str = f"Voice {i+1} - {voice.id[:8]}"
                    print(f"[PAGE] Created option string: '{option_str}'")
                    print(f"[PAGE] Option string type: {type(option_str)}")

                    voice_options.append(option_str)

                except Exception as voice_error:
                    print(f"[PAGE] Error processing voice {i}: {voice_error}")
                    traceback.print_exc()

        print(f"[PAGE] Final voice_options: {voice_options}")
        print(f"[PAGE] Voice options length: {len(voice_options)}")
        print(f"[PAGE] Voice options types: {[type(x) for x in voice_options]}")

        if voice_options:
            ui.label('Voice Dropdown:').classes('text-h6 mt-4')

            try:
                voice_select = ui.select(options=voice_options, value=voice_options[0])
                print("[PAGE] Voice dropdown created successfully")
            except Exception as dropdown_error:
                print(f"[PAGE] Error creating voice dropdown: {dropdown_error}")
                traceback.print_exc()
                ui.label(f'Dropdown Error: {dropdown_error}').classes('text-negative')
        else:
            ui.label('No voice options available').classes('text-warning')

        # Test 3: Button with error logging
        print("[PAGE] Creating test button...")

        def test_button():
            print("[BUTTON] Test button clicked!")
            ui.notify('Button works!', type='positive')

        try:
            test_btn = ui.button('Test Button', on_click=test_button)
            print("[PAGE] Button created successfully")
        except Exception as button_error:
            print(f"[PAGE] Error creating button: {button_error}")
            traceback.print_exc()

        # Show raw voice data for inspection
        if audio_interface.voices:
            ui.label('Raw Voice Data:').classes('text-h6 mt-4')
            for i, voice in enumerate(audio_interface.voices):
                voice_info = f"Voice {i}: ID={voice.id}, Name={voice.name}, Type={type(voice)}"
                ui.label(voice_info).classes('text-body2 font-mono')

        # Test 4: Recording functionality test
        print("[PAGE] Creating recording test section...")
        ui.label('Recording Test Section:').classes('text-h6 mt-6')

        # Recording status
        recording_status = ui.label('Ready to record').classes('text-body1 mb-2')
        recording_data = {'audio_data': None, 'recording': False}

        # Recording functions with detailed logging
        async def test_start_recording():
            """Test recording start functionality"""
            print("[RECORD TEST] start_recording called!")
            print(f"[RECORD TEST] Function type: {type(test_start_recording)}")
            print(f"[RECORD TEST] Button references exist: {record_btn is not None}")

            try:
                recording_data['recording'] = True
                recording_status.text = 'Testing JavaScript recording...'

                # Test JavaScript recording
                print("[RECORD TEST] Calling JavaScript...")
                success = await ui.run_javascript('''
                    console.log("[JS TEST] Testing recording capability...");

                    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
                        console.error("[JS TEST] getUserMedia not supported");
                        return {success: false, error: "getUserMedia not supported"};
                    }

                    try {
                        console.log("[JS TEST] Requesting microphone permission...");
                        const stream = await navigator.mediaDevices.getUserMedia({audio: true});
                        console.log("[JS TEST] Microphone permission granted!");

                        // Stop the stream immediately (we're just testing)
                        stream.getTracks().forEach(track => track.stop());

                        return {success: true, message: "Microphone access OK"};
                    } catch (error) {
                        console.error("[JS TEST] Microphone access failed:", error);
                        return {success: false, error: error.toString()};
                    }
                ''')

                print(f"[RECORD TEST] JavaScript result: {success}")

                if success and success.get('success'):
                    recording_status.text = f'✅ Recording test passed: {success.get("message", "OK")}'
                    ui.notify('Recording capability confirmed!', type='positive')
                    record_btn.disable()
                    stop_btn.enable()
                else:
                    error_msg = success.get('error', 'Unknown error') if success else 'No response'
                    recording_status.text = f'❌ Recording test failed: {error_msg}'
                    ui.notify('Recording capability failed', type='negative')

            except Exception as e:
                error_msg = str(e)
                print(f"[RECORD TEST] Exception: {error_msg}")
                recording_status.text = f'❌ Recording error: {error_msg}'
                ui.notify('Recording function error', type='negative')

        async def test_stop_recording():
            """Test recording stop functionality"""
            print("[STOP TEST] stop_recording called!")

            try:
                recording_data['recording'] = False
                recording_status.text = 'Recording stopped (test mode)'
                record_btn.enable()
                stop_btn.disable()
                ui.notify('Stop recording test passed!', type='positive')

            except Exception as e:
                print(f"[STOP TEST] Exception: {str(e)}")
                ui.notify('Stop recording error', type='negative')

        # Test file upload functionality
        async def test_file_upload(e):
            """Test file upload with detailed error logging"""
            print(f"[UPLOAD TEST] Upload triggered!")
            print(f"[UPLOAD TEST] Event type: {type(e)}")
            print(f"[UPLOAD TEST] Event attributes: {dir(e)}")
            print(f"[UPLOAD TEST] File name: {e.name}")
            print(f"[UPLOAD TEST] Content type: {type(e.content)}")

            try:
                # Test reading file content
                e.content.seek(0)
                content = e.content.read()
                print(f"[UPLOAD TEST] Successfully read {len(content)} bytes")

                # Show success
                recording_status.text = f'✅ File upload test: {e.name} ({len(content)} bytes)'
                ui.notify(f'Upload test passed: {len(content)} bytes read', type='positive')

            except Exception as upload_error:
                print(f"[UPLOAD TEST] Upload error: {upload_error}")
                recording_status.text = f'❌ Upload test failed: {str(upload_error)}'
                ui.notify('Upload test failed', type='negative')

        # Create test buttons
        print("[PAGE] Creating test recording buttons...")
        with ui.row().classes('gap-2 mt-2'):
            record_btn = ui.button('🎤 Test Record', color='primary')
            stop_btn = ui.button('⏹ Test Stop', color='negative').disable()

        # Create test upload
        ui.label('File Upload Test:').classes('text-h6 mt-4')
        ui.upload(
            label='Test file upload (any file)',
            on_upload=test_file_upload,
            max_file_size=1_000_000  # 1MB for testing
        ).classes('w-full mt-2')

        # Bind button handlers with error checking
        print("[PAGE] Binding button handlers...")
        try:
            record_btn.on_click(test_start_recording)
            stop_btn.on_click(test_stop_recording)
            print("[PAGE] ✅ Button handlers bound successfully!")

        except Exception as bind_error:
            print(f"[PAGE] ❌ Button binding error: {bind_error}")
            ui.label(f'Button binding error: {bind_error}').classes('text-negative')

        print("[PAGE] Page setup completed successfully")

    except Exception as page_error:
        error_msg = f"Page setup error: {page_error}"
        print(f"[PAGE ERROR] {error_msg}")
        traceback.print_exc()

        try:
            ui.label(f'Page Error: {error_msg}').classes('text-negative text-h5')
        except:
            print("[PAGE ERROR] Could not even create error label")


if __name__ in {"__main__", "__mp_main__"}:
    print("\n" + "="*60)
    print("STARTING NICEGUI SERVER")
    print("="*60)

    try:
        ui.run(port=8083, title='Error Logging Interface', show=True)
    except Exception as e:
        print(f"[SERVER ERROR] {e}")
        traceback.print_exc()