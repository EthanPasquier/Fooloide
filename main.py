import json
import os
import subprocess
from openai import OpenAI
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def load_system_prompt():
    """Load the system prompt from principaleprompt file"""
    try:
        with open('principaleprompt', 'r') as f:
            return f.read().strip()
    except Exception as e:
        print(f"Error loading system prompt: {e}")
        return None

class Bot:
    def __init__(self):
        self.client = OpenAI()
        self.system_prompt = load_system_prompt()
        self.history_file = "bot_memory.json"
        self.history = self.load_history()

    def load_history(self):
        """Load conversation history from file"""
        history = []
        if os.path.exists(self.history_file):
            try:
                with open(self.history_file, 'r') as f:
                    history = json.load(f)
            except:
                pass
        if not isinstance(history, list):
            history = []
        return history

    def save_history(self):
        """Save conversation history to file"""
        with open(self.history_file, 'w') as f:
            json.dump(self.history, f, indent=2)

    def execute_command(self, command):
        """Execute a shell command and return output"""
        try:
            result = subprocess.run(command, shell=True, capture_output=True, text=True)
            return result.stdout if result.stdout else result.stderr
        except Exception as e:
            return f"Error executing command: {str(e)}"

    def process_interaction(self, last_output=None):
        """Process bot interaction and generate response"""
        # Prepare messages
        messages = [{"role": "system", "content": self.system_prompt}]
        
        # Add relevant history (last 10 messages)
        if isinstance(self.history, list) and self.history:
            for msg in self.history[-10:]:
                if isinstance(msg, dict) and 'role' in msg and 'content' in msg:
                    messages.append(msg)
        
        # Add current input if exists
        if last_output:
            messages.append({"role": "user", "content": last_output})

        # Get response from OpenAI
        response = self.client.chat.completions.create(
            model="gpt-4o-mini",  # Using correct model name
            messages=messages,
            functions=[{
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
            }]
        )

        # Process the response
        message = response.choices[0].message

        # Handle function calls
        if message.function_call:
            func_args = json.loads(message.function_call.arguments)
            command_output = self.execute_command(func_args["command"])
            
            # Store the interaction
            self.history.append({"role": "assistant", "content": message.content})
            self.history.append({
                "role": "system",
                "content": f"Command executed: {func_args['command']}\nOutput: {command_output}"
            })
            
            self.save_history()
            return command_output
        else:
            # Store the response
            self.history.append({"role": "assistant", "content": message.content})
            self.save_history()
            return message.content

def clear_screen():
    """Clear the terminal screen"""
    os.system('clear' if os.name == 'posix' else 'cls')

def main():
    bot = Bot()
    clear_screen()
    print("\n=== Bot System Initialized ===\n")
    
    # Display initial system prompt
    print("System Prompt:")
    print("=============")
    print(bot.system_prompt)
    print("=============\n")
    
    # Initial interaction
    last_output = None
    
    while True:
        input("\nPress Enter to continue (Ctrl+C to exit): ")
        clear_screen()
        
        # Process bot interaction
        if last_output:
            print(f"\nPrevious Output:\n{last_output}\n")
            
        print("Processing...\n")
        response = bot.process_interaction(last_output)
        
        # Display response
        print("Bot Response:")
        print("============")
        print(response)
        print("============")
        
        # Update last output
        last_output = response

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nExiting bot system...")
