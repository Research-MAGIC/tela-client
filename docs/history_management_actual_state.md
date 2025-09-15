  The conversation_history.py demonstrates several key patterns for
  handling user interactions:

  1. Three-Role Message Structure

  The code uses the standard OpenAI chat format with three distinct
  roles:

  # System role - Sets behavior and context
  ("system", "You are a helpful Python programming assistant...")

  # User role - Human input and questions
  ("user", "Hello! I'm new to Python and need help getting started.")

  # Assistant role - AI responses and guidance
  ("assistant", "Hello! Welcome to Python programming! I'd be happy to
  help...")

  2. Natural Conversation Flow Patterns

  Greeting Pattern:
  ("user", "Hello! I'm new to Python and need help getting started."),
  ("assistant", "Hello! Welcome to Python programming! I'd be happy to
  help you get started! Python is a fantastic language for beginners...")

  Question-Answer Pattern:
  ("user", "Can you show me how to create and use variables?"),
  ("assistant", "Absolutely! Variables in Python are simple to create and
   use...")

  Follow-up Context Pattern:
  ("user", "That's helpful! What about loops? How do I repeat actions?"),
  ("assistant", "Great question! Loops are essential for repeating
  actions in Python...")

  3. Context Preservation and Continuity

  The conversation maintains context across exchanges:
  - References to previous topics ("That's helpful! What about loops?")
  - Building knowledge progressively (variables → loops → functions)
  - Maintaining conversational tone throughout

  4. Message Metadata Structure

  When exported to JSON, each message includes rich metadata:

  {
    "role": "user",
    "content": "Hello! I'm new to Python...",
    "metadata": {
      "timestamp": "2025-01-15T10:30:00Z",
      "message_index": 1,
      "character_count": 52,
      "conversation_id": "conv_12345"
    }
  }

● 5. Message Structure and Role Management

  System Message Strategy:
  - Sets assistant personality and capabilities
  - Defines response style and boundaries
  - Provides domain-specific context (Python programming)

  User Message Patterns:
  - Questions seeking information
  - Requests for examples or demonstrations
  - Follow-up clarifications
  - Natural conversational transitions

  Assistant Message Patterns:
  - Structured responses with explanations
  - Code examples with context
  - Encouraging and supportive tone
  - Building on previous conversation elements

  6. Conversation State Management

  The code demonstrates how to:

  # Add messages to ongoing conversation
  conversation.add_message("user", user_input)
  conversation.add_message("assistant", ai_response)

  # Retrieve full conversation history
  messages = conversation.get_messages()

  # Maintain conversation continuity across API calls
  response = await client.chat.completions.create(
      messages=messages,  # Full conversation context
      conversation_id=conversation.id
  )

  7. Export Formats for Different Use Cases

  API-Ready Format:
  [
    {"role": "system", "content": "You are a helpful..."},
    {"role": "user", "content": "Hello! I'm new to Python..."},
    {"role": "assistant", "content": "Hello! Welcome to Python..."}
  ]

  Human-Readable Format:
  SYSTEM: You are a helpful Python programming assistant...

  USER: Hello! I'm new to Python and need help getting started.

  ASSISTANT: Hello! Welcome to Python programming! I'd be happy to
  help...