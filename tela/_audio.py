"""
Audio transcription resource for Tela/Fabric API
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import TYPE_CHECKING, Any, BinaryIO, Dict, Optional, Union

from ._types import NOT_GIVEN, NotGiven
from .types.audio import TranscriptionResponse, VoiceListResponse, TTSResponse, Voice

if TYPE_CHECKING:
    from ._client import Tela, AsyncTela

__all__ = ["Audio", "AsyncAudio", "Transcriptions", "AsyncTranscriptions", "Speech", "AsyncSpeech"]


class Transcriptions:
    """
    Synchronous audio transcription resource
    """

    def __init__(self, audio: Audio) -> None:
        self._audio = audio
        self._client = audio._client

    def create(
        self,
        *,
        file: Union[str, Path, BinaryIO],
        model: str = "fabric-voice-stt",
        response_format: str = "verbose_json",
        language: Optional[str] = None,
        prompt: Optional[str] = None,
        temperature: float = 0.0,
        extra_headers: Optional[Dict[str, str]] = None,
        extra_query: Optional[Dict[str, object]] = None,
    ) -> TranscriptionResponse:
        """
        Transcribe audio to text

        Args:
            file: Audio file to transcribe (path or file object)
            model: Model to use for transcription (default: fabric-voice-stt)
            response_format: Output format (json, text, srt, vtt, verbose_json)
            language: Optional language hint (ISO-639-1 code)
            prompt: Optional text to guide the model
            temperature: Sampling temperature (0-1, default: 0)
            extra_headers: Additional headers to include
            extra_query: Additional query parameters

        Returns:
            TranscriptionResponse: Transcribed text with metadata

        Raises:
            FileNotFoundError: If file path doesn't exist
            BadRequestError: If request parameters are invalid
            APIError: For other API errors
        """
        from ._types import RequestOptions

        # Handle file input
        if isinstance(file, (str, Path)):
            file_path = Path(file)
            if not file_path.exists():
                raise FileNotFoundError(f"Audio file not found: {file_path}")
            file_obj = open(file_path, "rb")
            file_name = file_path.name
            close_file = True
        else:
            file_obj = file
            file_name = getattr(file, "name", "audio.wav")
            close_file = False

        try:
            # Prepare form data
            files = {
                "file": (file_name, file_obj, "application/octet-stream")
            }

            data = {
                "model": model,
                "response_format": response_format,
            }

            if language:
                data["language"] = language
            if prompt:
                data["prompt"] = prompt
            if temperature != 0.0:
                data["temperature"] = str(temperature)

            # Don't include Content-Type header, let httpx set it for multipart
            headers = {}
            if extra_headers:
                headers.update(extra_headers)

            options = RequestOptions(
                headers=headers,
                params=extra_query,
            )

            # Make the request
            response = self._client.post(
                "/audio/transcriptions",
                files=files,
                body=data,
                options=options,
            )

            # Parse response based on format
            if response_format == "text":
                return TranscriptionResponse(text=response)
            elif response_format in ["srt", "vtt"]:
                return TranscriptionResponse(text=response)
            else:
                # json or verbose_json
                return TranscriptionResponse.model_validate(response)

        finally:
            if close_file:
                file_obj.close()


class AsyncTranscriptions:
    """
    Asynchronous audio transcription resource
    """

    def __init__(self, audio: AsyncAudio) -> None:
        self._audio = audio
        self._client = audio._client

    async def create(
        self,
        *,
        file: Union[str, Path, BinaryIO],
        model: str = "fabric-voice-stt",
        response_format: str = "verbose_json",
        language: Optional[str] = None,
        prompt: Optional[str] = None,
        temperature: float = 0.0,
        extra_headers: Optional[Dict[str, str]] = None,
        extra_query: Optional[Dict[str, object]] = None,
    ) -> TranscriptionResponse:
        """
        Async version of transcription create

        See Transcriptions.create() for parameter documentation
        """
        from ._types import RequestOptions

        # Handle file input
        if isinstance(file, (str, Path)):
            file_path = Path(file)
            if not file_path.exists():
                raise FileNotFoundError(f"Audio file not found: {file_path}")

            # Read file asynchronously - try aiofiles first, fallback to sync
            try:
                import aiofiles
                async with aiofiles.open(file_path, "rb") as f:
                    file_content = await f.read()
            except ImportError:
                # Fallback to synchronous reading if aiofiles not available
                with open(file_path, "rb") as f:
                    file_content = f.read()

            file_name = file_path.name
            files = {
                "file": (file_name, file_content, "application/octet-stream")
            }
        else:
            # Assume it's already a file-like object
            file_name = getattr(file, "name", "audio.wav")
            if hasattr(file, "read"):
                file_content = file.read()
                if callable(file_content):
                    file_content = await file_content()
            else:
                file_content = file
            files = {
                "file": (file_name, file_content, "application/octet-stream")
            }

        # Prepare form data
        data = {
            "model": model,
            "response_format": response_format,
        }

        if language:
            data["language"] = language
        if prompt:
            data["prompt"] = prompt
        if temperature != 0.0:
            data["temperature"] = str(temperature)

        # Don't include Content-Type header, let httpx set it for multipart
        headers = {}
        if extra_headers:
            headers.update(extra_headers)

        options = RequestOptions(
            headers=headers,
            params=extra_query,
        )

        # Make the request
        response = await self._client.post(
            "/audio/transcriptions",
            files=files,
            body=data,
            options=options,
        )

        # Parse response based on format
        if response_format == "text":
            return TranscriptionResponse(text=response)
        elif response_format in ["srt", "vtt"]:
            return TranscriptionResponse(text=response)
        else:
            # json or verbose_json
            return TranscriptionResponse.model_validate(response)


class Speech:
    """
    Synchronous text-to-speech resource
    """

    def __init__(self, audio: Audio) -> None:
        self._audio = audio
        self._client = audio._client

    def create(
        self,
        *,
        model: str = "fabric-voice-tts",
        input: str,
        voice: str,
        output_format: str = "opus_48000_128",
        response_format: Optional[str] = None,
        speed: Optional[float] = None,
        extra_headers: Optional[Dict[str, str]] = None,
        extra_query: Optional[Dict[str, object]] = None,
    ) -> TTSResponse:
        """
        Generate speech from text

        Args:
            model: Model to use for TTS (default: fabric-voice-tts)
            input: Text to convert to speech
            voice: Voice ID to use for generation
            output_format: Audio output format (default: opus_48000_128)
            response_format: Optional response format
            speed: Speed of speech (0.25 to 4.0)
            extra_headers: Additional headers to include
            extra_query: Additional query parameters

        Returns:
            TTSResponse: Audio content and metadata

        Raises:
            BadRequestError: If request parameters are invalid
            APIError: For other API errors
        """
        from ._types import RequestOptions

        # Prepare JSON data
        data = {
            "model": model,
            "input": input,
            "voice": voice,
            "output_format": output_format,
        }

        if response_format:
            data["response_format"] = response_format
        if speed is not None:
            data["speed"] = speed

        headers = {"Content-Type": "application/json"}
        if extra_headers:
            headers.update(extra_headers)

        options = RequestOptions(
            headers=headers,
            params=extra_query,
        )

        # Make the request - need to handle binary response manually
        from ._types import RequestOptions
        from ._utils import is_given

        # Handle timeout properly
        timeout = None
        if hasattr(options, 'timeout') and is_given(options.timeout):
            timeout = options.timeout

        request = self._client._build_request(
            method="POST",
            url="/audio/speech",
            json_data=data,
            params=options.params,
            headers=options.headers,
            timeout=timeout,
        )

        raw_response = self._client._client.send(request)

        try:
            raw_response.raise_for_status()
        except Exception as e:
            self._client._handle_error_response(raw_response)

        # Response should be binary audio data
        audio_content = raw_response.content
        content_type = raw_response.headers.get("content-type", "audio/opus")

        return TTSResponse(
            content=audio_content,
            content_type=content_type,
            format=output_format,
        )


class AsyncSpeech:
    """
    Asynchronous text-to-speech resource
    """

    def __init__(self, audio: AsyncAudio) -> None:
        self._audio = audio
        self._client = audio._client

    async def create(
        self,
        *,
        model: str = "fabric-voice-tts",
        input: str,
        voice: str,
        output_format: str = "opus_48000_128",
        response_format: Optional[str] = None,
        speed: Optional[float] = None,
        extra_headers: Optional[Dict[str, str]] = None,
        extra_query: Optional[Dict[str, object]] = None,
    ) -> TTSResponse:
        """
        Async version of speech create

        See Speech.create() for parameter documentation
        """
        from ._types import RequestOptions

        # Prepare JSON data
        data = {
            "model": model,
            "input": input,
            "voice": voice,
            "output_format": output_format,
        }

        if response_format:
            data["response_format"] = response_format
        if speed is not None:
            data["speed"] = speed

        headers = {"Content-Type": "application/json"}
        if extra_headers:
            headers.update(extra_headers)

        options = RequestOptions(
            headers=headers,
            params=extra_query,
        )

        # Make the request - need to handle binary response manually
        from ._utils import is_given

        # Handle timeout properly
        timeout = None
        if hasattr(options, 'timeout') and is_given(options.timeout):
            timeout = options.timeout

        request = self._client._build_request(
            method="POST",
            url="/audio/speech",
            json_data=data,
            params=options.params,
            headers=options.headers,
            timeout=timeout,
        )

        raw_response = await self._client._client.send(request)

        try:
            raw_response.raise_for_status()
        except Exception as e:
            self._client._handle_error_response(raw_response)

        # Response should be binary audio data
        audio_content = raw_response.content
        content_type = raw_response.headers.get("content-type", "audio/opus")

        return TTSResponse(
            content=audio_content,
            content_type=content_type,
            format=output_format,
        )


class Audio:
    """
    Synchronous audio resource containing transcription and TTS functionality
    """

    def __init__(self, client: Tela) -> None:
        self._client = client
        self.transcriptions = Transcriptions(self)
        self.speech = Speech(self)

    def voices(
        self,
        *,
        extra_headers: Optional[Dict[str, str]] = None,
        extra_query: Optional[Dict[str, object]] = None,
    ) -> VoiceListResponse:
        """
        List available text-to-speech voices

        Args:
            extra_headers: Additional headers to include
            extra_query: Additional query parameters

        Returns:
            VoiceListResponse: List of available voices

        Raises:
            APIError: For API errors
        """
        from ._types import RequestOptions

        headers = {}
        if extra_headers:
            headers.update(extra_headers)

        options = RequestOptions(
            headers=headers,
            params=extra_query,
        )

        # Make the request
        response = self._client.get(
            "/audio/voices",
            options=options,
        )

        # Parse response
        if isinstance(response, dict):
            return VoiceListResponse.model_validate(response)
        else:
            # Handle unexpected response format
            raise ValueError(f"Unexpected response type: {type(response)}")


class AsyncAudio:
    """
    Asynchronous audio resource containing transcription and TTS functionality
    """

    def __init__(self, client: AsyncTela) -> None:
        self._client = client
        self.transcriptions = AsyncTranscriptions(self)
        self.speech = AsyncSpeech(self)

    async def voices(
        self,
        *,
        extra_headers: Optional[Dict[str, str]] = None,
        extra_query: Optional[Dict[str, object]] = None,
    ) -> VoiceListResponse:
        """
        List available text-to-speech voices (async version)

        Args:
            extra_headers: Additional headers to include
            extra_query: Additional query parameters

        Returns:
            VoiceListResponse: List of available voices

        Raises:
            APIError: For API errors
        """
        from ._types import RequestOptions

        headers = {}
        if extra_headers:
            headers.update(extra_headers)

        options = RequestOptions(
            headers=headers,
            params=extra_query,
        )

        # Make the request
        response = await self._client.get(
            "/audio/voices",
            options=options,
        )

        # Parse response
        if isinstance(response, dict):
            return VoiceListResponse.model_validate(response)
        else:
            # Handle unexpected response format
            raise ValueError(f"Unexpected response type: {type(response)}")