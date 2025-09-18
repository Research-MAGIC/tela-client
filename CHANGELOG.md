# Changelog

All notable changes to the Tela Client SDK will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.2.0] - 2025-01-18

### Added
- Full audio transcription support with Fabric Voice STT
  - `Audio` and `AsyncAudio` classes for audio operations
  - `Transcriptions` and `AsyncTranscriptions` for speech-to-text
  - Support for multiple audio formats (mp3, wav, m4a, webm, mp4, mpeg, mpga, oga, ogg, opus)
  - Detailed transcription segments with timestamps and confidence scores
- Text-to-Speech (TTS) synthesis capabilities
  - Multiple voice options (alloy, echo, fable, onyx, nova, shimmer)
  - Configurable speech parameters (speed, response format)
  - `TTSResponse` and `Voice` types for TTS operations
- Server-side chat management functionality
  - `Chats` and `AsyncChats` classes for chat operations
  - Chat listing with pagination support
  - Chat retrieval and deletion capabilities
  - `ChatPaginatedResponse` for handling paginated results
- Interactive NiceGUI examples
  - `audio_nicegui_interface.py` - Complete audio transcription interface
  - `text_to_speech_test.py` - TTS demonstration
  - `chat_management_test.py` - Chat management interface
  - `error_logging_interface.py` - Error tracking interface
- Optional UI dependencies for NiceGUI interfaces (`nicegui`, `python-dotenv`)

### Changed
- Updated package description to reflect audio capabilities
- Enhanced README with comprehensive audio feature documentation
- Expanded package keywords for better PyPI discoverability
- Improved example structure with separate audio and chat demos

### Fixed
- Variable scoping issues in NiceGUI async contexts
- Button reference errors in recording interfaces
- TTS generation async context slot stack issues
- Audio file upload handler byte stream processing

## [1.1.0] - 2025-01-10

### Added
- Conversation history management with `HistoryManager` class
- Automatic context tracking across conversations
- History persistence to JSON files
- Token usage tracking and statistics
- Model information retrieval (`Model`, `ModelList`, `ModelCapabilities`)
- Usage statistics (`UsageInfo`, `ParameterInfo`)
- Advanced NiceGUI test interface (`advanced_nicegui_test.py`)

### Changed
- Refactored client architecture to support modular features
- Improved async/sync client parity
- Enhanced error handling with specific exception types

### Fixed
- Context length handling for different models
- Message role validation
- JSON serialization for complex types

## [1.0.0] - 2025-01-01

### Added
- Initial release of Tela Client SDK
- Core client implementation (`Tela`, `AsyncTela`)
- Basic chat completion functionality
- Streaming response support
- Comprehensive exception handling
  - `TelaError` base exception
  - HTTP status-specific exceptions (400, 401, 403, 404, etc.)
  - Connection and timeout errors
- Type-safe interfaces with Pydantic models
- Full async/await support
- Basic examples and documentation
- MIT license

### Changed
- N/A (Initial release)

### Fixed
- N/A (Initial release)

### Deprecated
- N/A (Initial release)

### Removed
- N/A (Initial release)

### Security
- Secure API key handling
- HTTPS-only communication

[1.2.0]: https://github.com/Research-MAGIC/tela-client/compare/v1.1.0...v1.2.0
[1.1.0]: https://github.com/Research-MAGIC/tela-client/compare/v1.0.0...v1.1.0
[1.0.0]: https://github.com/Research-MAGIC/tela-client/releases/tag/v1.0.0