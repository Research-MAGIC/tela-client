from __future__ import annotations

import asyncio
from typing import Any, Callable, Optional, Union

try:
    import nicegui as ui
    NICEGUI_AVAILABLE = True
except ImportError:
    NICEGUI_AVAILABLE = False


class StreamingDisplay:
    """
    Utility class for displaying streaming content in different environments
    
    Supports both CLI and NiceGUI interfaces with real-time updates
    """
    
    def __init__(self, output_type: str = "auto") -> None:
        """
        Initialize streaming display
        
        Args:
            output_type: "cli", "nicegui", or "auto" (detect environment)
        """
        self.output_type = output_type
        self.accumulated_text = ""
        self.ui_element = None
        
        if output_type == "auto":
            self.output_type = "nicegui" if NICEGUI_AVAILABLE and self._is_nicegui_context() else "cli"
    
    def _is_nicegui_context(self) -> bool:
        """Check if we're running in a NiceGUI context"""
        if not NICEGUI_AVAILABLE:
            return False
        try:
            # Try to access NiceGUI's current context
            import inspect
            frame = inspect.currentframe()
            while frame:
                if 'nicegui' in str(frame.f_code.co_filename):
                    return True
                frame = frame.f_back
            return False
        except:
            return False
    
    def setup_nicegui_element(self, container=None) -> Any:
        """
        Setup NiceGUI element for streaming display
        
        Args:
            container: Optional NiceGUI container to add element to
            
        Returns:
            The created NiceGUI element
        """
        if not NICEGUI_AVAILABLE:
            raise RuntimeError("NiceGUI is not available")
        
        if container:
            with container:
                self.ui_element = ui.markdown("")
        else:
            self.ui_element = ui.markdown("")
        
        return self.ui_element
    
    def update_content(self, new_content: str) -> None:
        """
        Update display with new streaming content
        
        Args:
            new_content: New content chunk to add
        """
        self.accumulated_text += new_content
        
        if self.output_type == "cli":
            print(new_content, end="", flush=True)
        elif self.output_type == "nicegui" and self.ui_element:
            # Update NiceGUI element
            self.ui_element.content = self.accumulated_text
            # Force UI update
            if hasattr(self.ui_element, 'update'):
                self.ui_element.update()
    
    def finalize(self) -> str:
        """
        Finalize the streaming display
        
        Returns:
            The complete accumulated text
        """
        if self.output_type == "cli":
            print()  # Add newline at end
        
        return self.accumulated_text
    
    def clear(self) -> None:
        """Clear the accumulated content"""
        self.accumulated_text = ""
        if self.output_type == "nicegui" and self.ui_element:
            self.ui_element.content = ""
            if hasattr(self.ui_element, 'update'):
                self.ui_element.update()


class NiceGUIStreamHandler:
    """
    Specialized handler for NiceGUI streaming with advanced features
    """
    
    def __init__(self, ui_element=None, typing_speed: float = 0.02) -> None:
        """
        Initialize NiceGUI stream handler
        
        Args:
            ui_element: NiceGUI element to update (markdown, label, etc.)
            typing_speed: Speed of typing animation in seconds per character
        """
        if not NICEGUI_AVAILABLE:
            raise RuntimeError("NiceGUI is not available")
        
        self.ui_element = ui_element
        self.typing_speed = typing_speed
        self.accumulated_text = ""
        self.is_streaming = False
    
    def create_markdown_element(self, container=None, **kwargs) -> Any:
        """
        Create a markdown element for streaming
        
        Args:
            container: Optional container to add element to
            **kwargs: Additional arguments for ui.markdown()
            
        Returns:
            Created markdown element
        """
        if container:
            with container:
                self.ui_element = ui.markdown("", **kwargs)
        else:
            self.ui_element = ui.markdown("", **kwargs)
        
        return self.ui_element
    
    def create_chat_message(self, name: str = "Assistant", avatar=None) -> Any:
        """
        Create a chat message element for streaming
        
        Args:
            name: Name to display for the message
            avatar: Optional avatar URL or path
            
        Returns:
            Created chat message element
        """
        with ui.chat_message(name=name, avatar=avatar):
            self.ui_element = ui.markdown("")
        
        return self.ui_element
    
    async def stream_content(
        self,
        content_generator,
        typing_animation: bool = True,
        chunk_delay: float = 0.05
    ) -> str:
        """
        Stream content to the UI element with optional typing animation
        
        Args:
            content_generator: Async generator yielding content chunks
            typing_animation: Whether to show typing animation
            chunk_delay: Delay between chunks for animation effect
            
        Returns:
            Complete streamed content
        """
        self.is_streaming = True
        self.accumulated_text = ""
        
        try:
            async for chunk in content_generator:
                if hasattr(chunk, 'choices') and chunk.choices:
                    choice = chunk.choices[0]
                    if hasattr(choice, 'delta') and choice.delta and choice.delta.content:
                        content = choice.delta.content
                        
                        if typing_animation:
                            # Add character by character for typing effect
                            for char in content:
                                self.accumulated_text += char
                                self._update_ui()
                                await asyncio.sleep(self.typing_speed)
                        else:
                            self.accumulated_text += content
                            self._update_ui()
                            
                        if chunk_delay > 0:
                            await asyncio.sleep(chunk_delay)
            
        finally:
            self.is_streaming = False
        
        return self.accumulated_text
    
    def add_content(self, content: str) -> None:
        """
        Add content to the display
        
        Args:
            content: Content to add
        """
        self.accumulated_text += content
        self._update_ui()
    
    def _update_ui(self) -> None:
        """Update the UI element with current content"""
        if self.ui_element and hasattr(self.ui_element, 'content'):
            self.ui_element.content = self.accumulated_text
            # Force update if available
            if hasattr(self.ui_element, 'update'):
                self.ui_element.update()
    
    def clear(self) -> None:
        """Clear the content"""
        self.accumulated_text = ""
        self._update_ui()
    
    def set_content(self, content: str) -> None:
        """Set the complete content"""
        self.accumulated_text = content
        self._update_ui()


def create_cli_stream_handler(
    show_thinking: bool = False,
    prefix: str = "",
    suffix: str = "\n"
) -> Callable[[str], None]:
    """
    Create a simple CLI stream handler function
    
    Args:
        show_thinking: Whether to show thinking indicators (dots)
        prefix: Prefix to show before streaming starts
        suffix: Suffix to show after streaming ends
        
    Returns:
        Handler function for stream content
    """
    if prefix:
        print(prefix, end="")
    
    def handle_content(content: str) -> None:
        print(content, end="", flush=True)
    
    def finalize() -> None:
        print(suffix, end="")
    
    handle_content.finalize = finalize
    return handle_content


def create_nicegui_stream_handler(
    element_type: str = "markdown",
    container=None,
    **element_kwargs
) -> NiceGUIStreamHandler:
    """
    Create a NiceGUI stream handler with specified element type
    
    Args:
        element_type: Type of UI element ("markdown", "chat_message", "label")
        container: Optional container to add element to
        **element_kwargs: Additional arguments for element creation
        
    Returns:
        Configured NiceGUIStreamHandler
    """
    if not NICEGUI_AVAILABLE:
        raise RuntimeError("NiceGUI is not available")
    
    handler = NiceGUIStreamHandler()
    
    if element_type == "markdown":
        handler.create_markdown_element(container, **element_kwargs)
    elif element_type == "chat_message":
        handler.create_chat_message(**element_kwargs)
    elif element_type == "label":
        if container:
            with container:
                handler.ui_element = ui.label("", **element_kwargs)
        else:
            handler.ui_element = ui.label("", **element_kwargs)
    else:
        raise ValueError(f"Unsupported element type: {element_type}")
    
    return handler


# Convenience functions for common streaming patterns
async def stream_to_nicegui_chat(
    stream,
    name: str = "Assistant",
    avatar=None,
    typing_speed: float = 0.02
) -> str:
    """
    Stream content to a NiceGUI chat interface
    
    Args:
        stream: Stream object to consume
        name: Chat message name
        avatar: Optional avatar
        typing_speed: Typing animation speed
        
    Returns:
        Complete streamed content
    """
    handler = NiceGUIStreamHandler(typing_speed=typing_speed)
    handler.create_chat_message(name=name, avatar=avatar)
    
    return await handler.stream_content(stream, typing_animation=True)


def stream_to_cli(stream, prefix: str = "", suffix: str = "\n") -> str:
    """
    Stream content to CLI with simple formatting
    
    Args:
        stream: Stream object to consume
        prefix: Text to show before streaming
        suffix: Text to show after streaming
        
    Returns:
        Complete streamed content
    """
    if prefix:
        print(prefix, end="")
    
    accumulated = ""
    for chunk in stream:
        if hasattr(chunk, 'choices') and chunk.choices:
            choice = chunk.choices[0]
            if hasattr(choice, 'delta') and choice.delta and choice.delta.content:
                content = choice.delta.content
                print(content, end="", flush=True)
                accumulated += content
    
    print(suffix, end="")
    return accumulated