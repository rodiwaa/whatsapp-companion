# Whatsapp AI Companion

Add a AI contact and talk to it using Whatsapp

---

Inspired from https://github.com/neural-maze/ava-whatsapp-agent-course

---

**The Big Picture: Ava, Your WhatsApp AI Buddy**

At its heart, Ava is an AI agent designed to interact with you naturally through WhatsApp. It can understand what you say (text or voice), what you show it (images), and respond in kind (text, voice, or even generated images). The goal is to make it feel like you're talking to a real person.

To make this happen, we need several specialized parts that communicate with each other. Think of it like a team of experts, each with a specific job, all working under a central coordinator.

Here are the high-level components:

1.  **External Interfaces (How We Talk to Ava):**
    *   **WhatsApp API Webhook:** This is Ava's primary way of receiving messages from you on WhatsApp and sending replies back. When you send a message, WhatsApp pings our system, and when Ava responds, our system pings WhatsApp.
    *   **Chainlit UI:** This is a separate, web-based chat interface. It's super useful for us as developers to test Ava, see what's happening internally, and try out new features without constantly using WhatsApp. It's like a control panel for Ava.

2.  **The Brain/Coordinator (LangGraph):**
    *   This is the most crucial part! `LangGraph` acts as Ava's "brain" or the central coordinator. It defines a step-by-step workflow (called a "graph") that Ava follows for every interaction.
    *   **Why LangGraph?** Imagine a flow chart. LangGraph lets us build complex flow charts where each box (a "node") does a specific task, and the arrows (an "edge") dictate how we move from one task to the next, often based on certain conditions. This makes the AI's behavior predictable and manageable.
    *   **`AICompanionState`:** This is like Ava's current "thought process" or temporary memory for a single conversation. It holds all the relevant information for the current interaction, like your latest message, past conversation history, and any internal decisions Ava has made (e.g., "I need to generate an image now"). All nodes read from and write to this state.
    *   **Nodes:** These are the "steps" or "actions" Ava takes. For example:
        *   `memory_extraction_node`: "What important facts did the user just tell me?"
        *   `router_node`: "Based on the message, should I chat, generate an image, or reply with audio?"
        *   `conversation_node`: "Formulate a text response."
        *   `image_node`: "Generate an image and then describe it."
        *   `audio_node`: "Convert my text response into speech."
        *   `summarize_conversation_node`: "Is the conversation getting too long? Let's summarize it."
    *   **Edges:** These are the "rules" that connect the nodes. They tell LangGraph which node to go to next. Some edges are simple (always go from A to B), while others are "conditional" (go to B if X happens, or C if Y happens).

3.  **Memory Systems (How Ava Remembers):**
    *   **Short-Term Memory (SQLite Checkpointer):** This stores the recent chat history and the current `AICompanionState` for each ongoing conversation. It's like Ava's working memory for individual chats, allowing it to pick up where it left off if you chat later. This is stored locally in a `memory.db` file.
    *   **Long-Term Memory (Qdrant Vector Store):** This is where Ava stores important facts and information it has learned about you or the world over time. It's a "vector database," which means it stores information in a way that allows for very fast and intelligent searches for relevant context, even from months ago. This helps Ava "remember" things you told it a long time ago.

4.  **Specialized AI Modules (Ava's Senses and Skills):**
    *   **Speech Modules (`SpeechToText`, `TextToSpeech`):**
        *   `SpeechToText` (STT, powered by Groq/Whisper): Converts your WhatsApp voice notes into text so Ava can understand them.
        *   `TextToSpeech` (TTS, powered by ElevenLabs): Converts Ava's text responses into natural-sounding voice notes to send back to you.
    *   **Image Modules (`ImageToText`, `TextToImage`):**
        *   `ImageToText` (VLM, powered by Groq/Llama 3.2 Vision): When you send an image, this module "looks" at it and describes what's inside, giving Ava visual understanding.
        *   `TextToImage` (Diffusion Models, powered by Together AI/FLUX): When Ava decides to send you an image, this module generates that image based on a textual description.
    *   **Large Language Models (LLMs - Groq):** These are the general "brains" behind understanding your queries and generating human-like text responses for conversations. Groq is used for its speed.
    *   **Scheduling Module (`ScheduleContextGenerator`):** This is a simple module that provides Ava with a "daily activity" or routine. This makes Ava seem more alive by allowing it to mention what it's "doing" at different times of the day, adding dynamic context to conversations.

**How to Start Contributing / Building Similar Projects:**

1.  **Get it Running:**
    *   The first and most important step is to follow the instructions in `docs/GETTING_STARTED.md`. This will guide you through setting up your environment, installing dependencies, and configuring API keys (`.env` file). You can't contribute until you can run the project yourself!
2.  **Understand the Core (`LangGraph`):**
    *   The `src/ai_companion/graph/` directory is your best friend.
        *   `state.py`: Understand the `AICompanionState` first. This is crucial because every piece of information that flows through Ava's brain is stored here. If you want Ava to know something new or produce a new type of output, it needs to be in this state.
        *   `nodes.py`: Look at how each node takes the `state`, processes it, and updates it. To add a new feature, you might create a new node or modify an existing one.
        *   `edges.py`: See how the `select_workflow` and `should_summarize_conversation` functions determine the flow. If you want to change how Ava decides what to do next, you'd modify or add new logic here.
        *   `graph.py`: This is where all the nodes and edges are wired together to form the complete workflow.
3.  **Explore the Modules:**
    *   Look into `src/ai_companion/modules/` to see how the speech, image, and memory functionalities are implemented. If you want to swap out ElevenLabs for another TTS provider, or use a different image generation model, you'd modify these modules.
4.  **Experiment with Interfaces:**
    *   Use the `Chainlit` interface (`src/ai_companion/interfaces/chainlit/app.py`) for quick testing and debugging. It's often easier than sending WhatsApp messages repeatedly.
    *   If you want to integrate Ava with another platform (e.g., Telegram, Slack), you'd look at how `src/ai_companion/interfaces/whatsapp/webhook_endpoint.py` is built and create a similar file for the new platform's API.

**Ideas for New Features/Modifications:**

*   **New Workflow Branch:** Add a new `workflow` type (e.g., "calendar," "web\_search") in `router_node` and `select_workflow`, then create a new node (e.g., `calendar_node`) to handle that functionality.
*   **Different LLM Providers:** Swap out Groq for OpenAI, Anthropic, or another provider by modifying the `get_chat_model` function (likely in `src/ai_companion/graph/utils/helpers.py` or similar).
*   **Personalization:** Enhance the `memory_extraction_node` or `memory_injection_node` to remember more specific user preferences or facts, and integrate those into responses.
*   **Timed Messages:** Create a new scheduling mechanism where Ava proactively sends messages at certain times (e.g., "Good morning!").
*   **More Complex Image Interactions:** Instead of just generating images, perhaps Ava could edit existing images or perform object detection on user-provided images and comment on specific elements.

The key is to always think about how your changes will affect the `AICompanionState` and how the LangGraph workflow will handle them. Start small, make one change at a time, and use the Chainlit UI for testing!

nodes.py: Look at how each node takes the state, processes it, and updates it. To add a new feature, you might create a new node or modify an existing one.
edges.py: See how the select_workflow and should_summarize_conversation functions determine the flow. If you want to change how Ava decides what to do next, you'd modify or add new logic here.
graph.py: This is where all the nodes and edges are wired together to form the complete workflow.
Explore the Modules:
Look into src/ai_companion/modules/ to see how the speech, image, and memory functionalities are implemented. If you want to swap out ElevenLabs for another TTS provider, or use a different image generation model, you'd modify these modules.
Experiment with Interfaces:
Use the Chainlit interface (src/ai_companion/interfaces/chainlit/app.py) for quick testing and debugging. It's often easier than sending WhatsApp messages repeatedly.
If you want to integrate Ava with another platform (e.g., Telegram, Slack), you'd look at how src/ai_companion/interfaces/whatsapp/webhook_endpoint.py is built and create a similar file for the new platform's API.
Ideas for New Features/Modifications:
New Workflow Branch: Add a new workflow type (e.g., "calendar," "web\search") in router_node and select_workflow, then create a new node (e.g., calendar_node) to handle that functionality.
Different LLM Providers: Swap out Groq for OpenAI, Anthropic, or another provider by modifying the get_chat_model function (likely in src/ai_companion/graph/utils/helpers.py or similar).
Personalization: Enhance the memory_extraction_node or memory_injection_node to remember more specific user preferences or facts, and integrate those into responses.
Timed Messages: Create a new scheduling mechanism where Ava proactively sends messages at certain times (e.g., "Good morning!").
More Complex Image Interactions: Instead of just generating images, perhaps Ava could edit existing images or perform object detection on user-provided images and comment on specific elements.
The key is to always think about how your changes will affect the AICompanionState and how the LangGraph workflow will handle them. Start small, make one change at a time, and use the Chainlit UI for testing!