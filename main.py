import json
import os
import subprocess
from typing import Dict, Any, List
from openai import OpenAI
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

def load_system_prompt():
    """Load the system prompt from principaleprompt file"""
    try:
        with open('principaleprompt', 'r') as f:
            return f.read()
    except Exception as e:
        print(f"Error loading system prompt: {e}")
        return None

SYSTEM_PROMPT = load_system_prompt()

class BotSystem:
    def __init__(self):
        self.client = OpenAI()
        self.memory_file = "bot_memory.json"
        self.load_memory()

    def load_memory(self):
        """Load bot's memory from file or create new if doesn't exist"""
        self.memory = {
            'conversation_history': [],
            'function_calls': [],
            'last_state': None
        }
        
        if os.path.exists(self.memory_file):
            try:
                with open(self.memory_file, 'r') as f:
                    loaded_memory = json.load(f)
                    # Verify the loaded memory has all required keys
                    if all(key in loaded_memory for key in self.memory.keys()):
                        self.memory = loaded_memory
            except (json.JSONDecodeError, Exception) as e:
                print(f"Error loading memory file: {e}")
                print("Using fresh memory state")
        
        self.save_memory()

    def save_memory(self):
        """Save bot's memory to file"""
        try:
            # First write to a temporary file
            temp_file = f"{self.memory_file}.tmp"
            with open(temp_file, 'w') as f:
                json.dump(self.memory, f, indent=2)
            
            # Then rename it to the actual file (atomic operation)
            os.replace(temp_file, self.memory_file)
        except Exception as e:
            print(f"Error saving memory file: {e}")
            # If saving fails, ensure temp file is cleaned up
            if os.path.exists(temp_file):
                try:
                    os.remove(temp_file)
                except:
                    pass

    def execute_command(self, command: str) -> str:
        """Execute a terminal command and return its output"""
        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True
            )
            output = result.stdout if result.stdout else result.stderr
            
            return output
        except Exception as e:
            error_msg = f"Error executing command: {str(e)}"
            # Store error in conversation history
            self.memory['conversation_history'].append({
                'role': 'assistant',
                'content': f"Command failed: {command}\nError: {error_msg}",
                'timestamp': datetime.now().isoformat()
            })
            self.save_memory()
            return error_msg

    def process_request(self, user_input: str) -> str:
        """Process user input and generate response"""
        # Add user input to conversation history
        self.memory['conversation_history'].append({
            'role': 'user',
            'content': user_input,
            'timestamp': datetime.now().isoformat()
        })

        # Get response from OpenAI
        # Prepare messages array with system prompt and conversation history
        messages = [
            {
                "role": "system",
                "content": SYSTEM_PROMPT
            }
        ]
        
        # Add last 50 messages from conversation history
        if self.memory['conversation_history']:
            # Get last 50 messages
            recent_history = self.memory['conversation_history'][-50:]
            for msg in recent_history:
                messages.append({
                    "role": msg['role'],
                    "content": msg['content']
                })
        
        response = self.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            functions=[
                {
                    "name": "execute_command",
                    "description": "Execute a terminal command",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "command": {
                                "type": "string",
                                "description": "The terminal command to execute"
                            }
                        },
                        "required": ["command"]
                    }
                }
            ]
        )

        # Process the response
        assistant_message = response.choices[0].message
        
        # Handle function calls if present
        if assistant_message.function_call:
            func_name = assistant_message.function_call.name
            func_args = json.loads(assistant_message.function_call.arguments)
            
            if func_name == "execute_command":
                command_output = self.execute_command(func_args["command"])
                
                # Store function call in memory
                self.memory['function_calls'].append({
                    'function': func_name,
                    'arguments': func_args,
                    'result': command_output,
                    'timestamp': datetime.now().isoformat()
                })
                
                # Update last state
                self.memory['last_state'] = {
                    'last_function': func_name,
                    'last_output': command_output
                }
                
                # Store command execution in conversation history
                self.memory['conversation_history'].append({
                    'role': 'assistant',
                    'content': f"Executing command: {func_args['command']}\nOutput: {command_output}",
                    'timestamp': datetime.now().isoformat()
                })
                
                self.save_memory()
                return f"Command executed. Output:\n{command_output}"
        
        # Store assistant's response in conversation history
        self.memory['conversation_history'].append({
            'role': 'assistant',
            'content': assistant_message.content,
            'timestamp': datetime.now().isoformat()
        })
        
        self.save_memory()
        return assistant_message.content

# ANSI color codes
YELLOW = "\033[93m"
BLUE = "\033[94m"
PURPLE = "\033[95m"
RESET = "\033[0m"

def clear_terminal():
    """Clear the terminal screen"""
    os.system('clear' if os.name == 'posix' else 'cls')

def main():
    bot = BotSystem()
    clear_terminal()
    print("\n=== Bot System Initialized ===\n")
    
    # First message should be the system prompt
    print("Initial System Prompt:")
    print("=====================")
    print(SYSTEM_PROMPT)
    print("=====================\n")
    
    while True:
        # Wait for user to press Enter
        user_action = input("Press Enter to continue: ")
        if user_action.lower() == 'exit':
            break
            
        clear_terminal()
        
        # Get bot response
        current_input = "Start"
        if bot.memory['last_state'] and isinstance(bot.memory['last_state'], dict) and 'last_output' in bot.memory['last_state']:
            current_input = bot.memory['last_state']['last_output']
        print(f"\n{YELLOW}Current Input:{RESET}\n{current_input}")
        
        response = bot.process_request(current_input)

        # Display the interaction with colors
        print("\nLatest Interaction:")
        print("==================")
        
        # Show the message/response
        if "Command executed. Output:" in response and bot.memory['function_calls']:
            try:
                # For command executions, show the command and its output
                last_command = bot.memory['function_calls'][-1]
                # Safely get the bot's message before command
                if len(bot.memory['conversation_history']) >= 2:
                    message = bot.memory['conversation_history'][-2]['content']
                    print(f"\n{YELLOW}Message:{RESET}\n{message}")
                print(f"\n{BLUE}Bash Command:{RESET}\n{last_command['arguments']['command']}")
                print(f"\n{PURPLE}Command Output:{RESET}\n{last_command['result']}")
            except (IndexError, KeyError) as e:
                print(f"\n{YELLOW}Error displaying command details: {e}{RESET}")
        else:
            # For regular responses, show the response
            print(f"\n{YELLOW}Message:{RESET}\n{response}")

        print("\n==================")
        
        # Clear last_state if no command was executed
        if "Command executed. Output:" not in response:
            bot.memory['last_state'] = None
            bot.save_memory()

if __name__ == "__main__":
    main()
