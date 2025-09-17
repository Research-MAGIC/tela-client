#!/usr/bin/env python3
"""
Test suite for audio transcription functionality
"""

import os
import sys
import pytest
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch, mock_open
from io import BytesIO

sys.path.insert(0, str(Path(__file__).parent.parent))

from tela import Tela, AsyncTela
from tela.types.audio import (
    TranscriptionResponse,
    TranscriptionSegment,
    TranscriptionRequest
)
from tela._exceptions import APIError


class TestTranscriptionTypes:
    """Test audio type models"""

    def test_transcription_segment(self):
        """Test TranscriptionSegment model"""
        segment = TranscriptionSegment(
            id=0,
            text=" Hello world",
            start=0.0,
            end=2.5,
            temperature=0.5,
            avg_logprob=-0.5,
            compression_ratio=1.2
        )

        assert segment.id == 0
        assert segment.text == " Hello world"
        assert segment.start == 0.0
        assert segment.end == 2.5
        assert segment.temperature == 0.5

    def test_transcription_response(self):
        """Test TranscriptionResponse model"""
        segments = [
            TranscriptionSegment(
                id=0,
                text=" Hello",
                start=0.0,
                end=1.0
            ),
            TranscriptionSegment(
                id=1,
                text=" world",
                start=1.0,
                end=2.0
            )
        ]

        response = TranscriptionResponse(
            text="Hello world",
            language="english",
            duration=2.0,
            task="transcribe",
            segments=segments
        )

        assert response.text == "Hello world"
        assert response.language == "english"
        assert response.duration == 2.0
        assert response.word_count == 2
        assert response.segment_count == 2

    def test_transcription_response_timestamps(self):
        """Test getting text with timestamps"""
        segments = [
            TranscriptionSegment(
                id=0,
                text=" Hello",
                start=0.0,
                end=1.5
            ),
            TranscriptionSegment(
                id=1,
                text=" world",
                start=1.5,
                end=3.0
            )
        ]

        response = TranscriptionResponse(
            text="Hello world",
            segments=segments
        )

        timestamped = response.get_text_with_timestamps()
        assert "[0.00s - 1.50s] Hello" in timestamped
        assert "[1.50s - 3.00s] world" in timestamped

    def test_transcription_to_srt(self):
        """Test SRT subtitle generation"""
        segments = [
            TranscriptionSegment(
                id=0,
                text=" Hello world",
                start=0.0,
                end=2.5
            )
        ]

        response = TranscriptionResponse(
            text="Hello world",
            segments=segments
        )

        srt = response.to_srt()
        assert "1" in srt
        assert "00:00:00,000 --> 00:00:02,500" in srt
        assert "Hello world" in srt

    def test_transcription_to_vtt(self):
        """Test WebVTT subtitle generation"""
        segments = [
            TranscriptionSegment(
                id=0,
                text=" Hello world",
                start=0.0,
                end=2.5
            )
        ]

        response = TranscriptionResponse(
            text="Hello world",
            segments=segments
        )

        vtt = response.to_vtt()
        assert "WEBVTT" in vtt
        assert "00:00:00.000 --> 00:00:02.500" in vtt
        assert "Hello world" in vtt


class TestAudioTranscription:
    """Test audio transcription functionality"""

    @pytest.fixture
    def mock_client(self):
        """Create a mock Tela client"""
        client = Mock(spec=Tela)
        client.api_key = "test-key"
        client.organization = "test-org"
        client.project = "test-project"
        return client

    def test_transcription_with_file_path(self, mock_client, tmp_path):
        """Test transcription with file path"""
        # Create a temporary audio file
        audio_file = tmp_path / "test.wav"
        audio_file.write_bytes(b"fake audio data")

        # Mock the post method
        mock_response = {
            "text": "This is a test transcription",
            "language": "english",
            "duration": 5.0,
            "segments": [
                {
                    "id": 0,
                    "text": " This is a test transcription",
                    "start": 0.0,
                    "end": 5.0,
                    "tokens": {},
                    "temperature": 0,
                    "avg_logprob": 0,
                    "compression_ratio": 1,
                    "no_speech_prob": 0,
                    "seek": 0
                }
            ]
        }
        mock_client.post.return_value = mock_response

        # Create transcription resource
        from tela._audio import Audio
        audio = Audio(mock_client)

        # Call transcription
        result = audio.transcriptions.create(
            file=str(audio_file),
            model="fabric-voice-stt"
        )

        # Verify result
        assert isinstance(result, TranscriptionResponse)
        assert result.text == "This is a test transcription"
        assert result.language == "english"
        assert result.duration == 5.0
        assert result.segment_count == 1

        # Verify the call
        mock_client.post.assert_called_once()
        call_args = mock_client.post.call_args
        assert call_args[0][0] == "/audio/transcriptions"

    def test_transcription_with_file_object(self, mock_client):
        """Test transcription with file object"""
        # Create a file-like object
        audio_data = BytesIO(b"fake audio data")
        audio_data.name = "test.wav"

        # Mock the post method
        mock_response = {
            "text": "Test with file object",
            "language": "english"
        }
        mock_client.post.return_value = mock_response

        # Create transcription resource
        from tela._audio import Audio
        audio = Audio(mock_client)

        # Call transcription
        result = audio.transcriptions.create(
            file=audio_data,
            model="fabric-voice-stt",
            response_format="json"
        )

        # Verify result
        assert isinstance(result, TranscriptionResponse)
        assert result.text == "Test with file object"

    def test_transcription_with_parameters(self, mock_client, tmp_path):
        """Test transcription with all parameters"""
        audio_file = tmp_path / "test.wav"
        audio_file.write_bytes(b"fake audio data")

        mock_response = {"text": "Test response"}
        mock_client.post.return_value = mock_response

        from tela._audio import Audio
        audio = Audio(mock_client)

        result = audio.transcriptions.create(
            file=str(audio_file),
            model="fabric-voice-stt",
            response_format="verbose_json",
            language="pt",
            prompt="This is about NiceGUI",
            temperature=0.5
        )

        # Verify the call included all parameters
        call_args = mock_client.post.call_args
        assert call_args[1]["body"]["model"] == "fabric-voice-stt"
        assert call_args[1]["body"]["response_format"] == "verbose_json"
        assert call_args[1]["body"]["language"] == "pt"
        assert call_args[1]["body"]["prompt"] == "This is about NiceGUI"
        assert call_args[1]["body"]["temperature"] == "0.5"

    def test_transcription_file_not_found(self, mock_client):
        """Test error when file doesn't exist"""
        from tela._audio import Audio
        audio = Audio(mock_client)

        with pytest.raises(FileNotFoundError) as exc_info:
            audio.transcriptions.create(
                file="/nonexistent/file.wav",
                model="fabric-voice-stt"
            )

        assert "Audio file not found" in str(exc_info.value)

    def test_transcription_text_format(self, mock_client, tmp_path):
        """Test transcription with text response format"""
        audio_file = tmp_path / "test.wav"
        audio_file.write_bytes(b"fake audio data")

        # For text format, the response is just a string
        mock_client.post.return_value = "This is plain text transcription"

        from tela._audio import Audio
        audio = Audio(mock_client)

        result = audio.transcriptions.create(
            file=str(audio_file),
            model="fabric-voice-stt",
            response_format="text"
        )

        assert isinstance(result, TranscriptionResponse)
        assert result.text == "This is plain text transcription"


class TestAsyncAudioTranscription:
    """Test async audio transcription functionality"""

    @pytest.fixture
    def mock_async_client(self):
        """Create a mock AsyncTela client"""
        client = Mock(spec=AsyncTela)
        client.api_key = "test-key"
        client.organization = "test-org"
        client.project = "test-project"

        # Make post method async
        async def async_post(*args, **kwargs):
            return {
                "text": "Async transcription result",
                "language": "english",
                "duration": 3.0
            }

        client.post = Mock(side_effect=async_post)
        return client

    @pytest.mark.asyncio
    async def test_async_transcription(self, mock_async_client, tmp_path):
        """Test async transcription"""
        audio_file = tmp_path / "test.wav"
        audio_file.write_bytes(b"fake audio data")

        from tela._audio import AsyncAudio
        audio = AsyncAudio(mock_async_client)

        # Test fallback to synchronous file reading (no aiofiles dependency)
        result = await audio.transcriptions.create(
            file=str(audio_file),
            model="fabric-voice-stt"
        )

        assert isinstance(result, TranscriptionResponse)
        assert result.text == "Async transcription result"
        assert result.language == "english"
        assert result.duration == 3.0

        # Verify the call
        mock_async_client.post.assert_called_once()


class TestIntegrationWithClient:
    """Test audio integration with main client"""

    def test_client_has_audio_resource(self):
        """Test that client has audio resource"""
        with patch.dict(os.environ, {
            "TELAOS_API_KEY": "test-key",
            "TELAOS_ORG_ID": "test-org",
            "TELAOS_PROJECT_ID": "test-project"
        }):
            client = Tela()
            assert hasattr(client, 'audio')
            assert hasattr(client.audio, 'transcriptions')

    @pytest.mark.asyncio
    async def test_async_client_has_audio_resource(self):
        """Test that async client has audio resource"""
        with patch.dict(os.environ, {
            "TELAOS_API_KEY": "test-key",
            "TELAOS_ORG_ID": "test-org",
            "TELAOS_PROJECT_ID": "test-project"
        }):
            client = AsyncTela()
            assert hasattr(client, 'audio')
            assert hasattr(client.audio, 'transcriptions')
            await client.close()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])