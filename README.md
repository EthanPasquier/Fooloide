# Fooloide Bot System

An advanced bot system that can execute commands, maintain memory, and process requests in a continuous loop.

## Features

- **Persistent Memory**: Stores conversation history, command results, and system state in a JSON file
- **Command Execution**: Can execute terminal commands and store their outputs
- **Context Awareness**: Uses previous interactions and command results for better responses
- **Function Execution**: Structured system for executing functions with arguments
- **Continuous Operation**: Runs in a loop, processing user inputs until explicitly stopped

## How It Works

1. **Memory System**
   - All interactions are stored in `bot_memory.json`
   - Maintains conversation history
   - Keeps track of executed commands and their results
   - Stores system state for context awareness

2. **Command Execution**
   - Can execute any terminal command
   - Captures and stores command output
   - Uses output as context for future interactions

3. **Context Management**
   - Maintains last 5 conversations for immediate context
   - Tracks last command execution and its result
   - Preserves system state between interactions

## Usage

1. Make sure you have Python installed and the required dependencies:
   ```bash
   pip install openai
   ```

2. Set up your OpenAI API key in a `.env` file:
   ```
   OPENAI_API_KEY=your_api_key_here
   ```

3. Run the bot:
   ```bash
   python main.py
   ```

4. Interact with the bot:
   - Type your commands or questions
   - The bot will respond and execute commands as needed
   - Type 'exit' to quit

## Memory Structure

The bot's memory (`bot_memory.json`) is structured as follows:
```json
{
    "conversation_history": [],
    "command_results": {},
    "function_calls": [],
    "last_state": null
}
```

- `conversation_history`: Array of past interactions
- `command_results`: Dictionary of executed commands and their outputs
- `function_calls`: List of executed functions with arguments and results
- `last_state`: Current system state information

## Security Note

The system uses a .gitignore file to prevent sensitive data (like API keys and memory files) from being tracked in version control. Always ensure your .env file is properly secured and never committed to the repository.
