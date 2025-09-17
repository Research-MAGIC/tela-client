"""
Audio-related type definitions for Tela/Fabric API
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field


class TranscriptionSegment(BaseModel):
    """Single segment of transcribed audio"""

    id: int
    text: str
    start: float
    end: float
    tokens: Dict[str, Any] = Field(default_factory=dict)
    temperature: float = 0.0
    avg_logprob: float = 0.0
    compression_ratio: float = 1.0
    no_speech_prob: float = 0.0
    seek: int = 0


class TranscriptionResponse(BaseModel):
    """Response from audio transcription endpoint"""

    text: str
    language: Optional[str] = None
    duration: Optional[float] = None
    task: Optional[str] = None
    segments: Optional[List[TranscriptionSegment]] = None

    @property
    def word_count(self) -> int:
        """Get the word count of the transcribed text"""
        return len(self.text.split()) if self.text else 0

    @property
    def segment_count(self) -> int:
        """Get the number of segments in the transcription"""
        return len(self.segments) if self.segments else 0

    def get_text_with_timestamps(self) -> str:
        """Get transcribed text with timestamps for each segment"""
        if not self.segments:
            return self.text

        lines = []
        for segment in self.segments:
            timestamp = f"[{segment.start:.2f}s - {segment.end:.2f}s]"
            lines.append(f"{timestamp} {segment.text.strip()}")
        return "\n".join(lines)

    def to_srt(self) -> str:
        """Convert transcription to SRT subtitle format"""
        if not self.segments:
            return ""

        srt_lines = []
        for segment in self.segments:
            # SRT format uses commas for milliseconds
            start_time = self._seconds_to_srt_time(segment.start)
            end_time = self._seconds_to_srt_time(segment.end)

            srt_lines.append(str(segment.id + 1))
            srt_lines.append(f"{start_time} --> {end_time}")
            srt_lines.append(segment.text.strip())
            srt_lines.append("")  # Empty line between subtitles

        return "\n".join(srt_lines)

    def to_vtt(self) -> str:
        """Convert transcription to WebVTT subtitle format"""
        if not self.segments:
            return "WEBVTT\n\n"

        vtt_lines = ["WEBVTT", ""]
        for segment in self.segments:
            start_time = self._seconds_to_vtt_time(segment.start)
            end_time = self._seconds_to_vtt_time(segment.end)

            vtt_lines.append(f"{start_time} --> {end_time}")
            vtt_lines.append(segment.text.strip())
            vtt_lines.append("")

        return "\n".join(vtt_lines)

    @staticmethod
    def _seconds_to_srt_time(seconds: float) -> str:
        """Convert seconds to SRT time format (00:00:00,000)"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        millis = int((seconds % 1) * 1000)
        return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"

    @staticmethod
    def _seconds_to_vtt_time(seconds: float) -> str:
        """Convert seconds to WebVTT time format (00:00:00.000)"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        millis = int((seconds % 1) * 1000)
        return f"{hours:02d}:{minutes:02d}:{secs:02d}.{millis:03d}"


class TranscriptionRequest(BaseModel):
    """Request parameters for audio transcription"""

    file: Any  # File object or path
    model: str = "fabric-voice-stt"
    response_format: str = "verbose_json"  # Options: json, text, srt, vtt, verbose_json
    language: Optional[str] = None  # Optional language hint (ISO-639-1)
    prompt: Optional[str] = None  # Optional text to guide the model
    temperature: float = 0.0  # Sampling temperature (0-1)


# Text-to-Speech Types

class Voice(BaseModel):
    """Voice model for text-to-speech"""

    id: str
    name: str
    description: Optional[str] = None
    language_code: Optional[str] = None
    gender: Optional[str] = None
    preview_url: Optional[str] = None
    category: Optional[str] = None
    settings: Optional[Dict[str, Any]] = None


class VoiceListResponse(BaseModel):
    """Response from voices listing endpoint"""

    data: List[Voice]  # API returns 'data' not 'voices'
    object: str = "list"

    @property
    def voices(self) -> List[Voice]:
        """Backward compatibility property"""
        return self.data


class TTSRequest(BaseModel):
    """Request parameters for text-to-speech"""

    model: str = "fabric-voice-tts"
    input: str  # Text to convert to speech
    voice: str  # Voice ID to use
    output_format: str = "opus_48000_128"  # Audio output format
    response_format: Optional[str] = None  # Optional response format
    speed: Optional[float] = None  # Speed of speech (0.25 to 4.0)


class TTSResponse(BaseModel):
    """Response from text-to-speech endpoint"""

    content: bytes  # Audio content
    content_type: str = "audio/opus"  # MIME type of the audio
    format: str = "opus_48000_128"  # Audio format

    def save_to_file(self, filepath: str) -> None:
        """Save audio content to a file"""
        with open(filepath, 'wb') as f:
            f.write(self.content)


__all__ = [
    "TranscriptionSegment",
    "TranscriptionResponse",
    "TranscriptionRequest",
    "Voice",
    "VoiceListResponse",
    "TTSRequest",
    "TTSResponse",
]