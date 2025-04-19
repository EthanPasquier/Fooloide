import json
import os
import subprocess
import sys
import time
from openai import OpenAI
from datetime import datetime
from dotenv import load_dotenv
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Load environment variables
load_dotenv()

def load_system_prompt():
    """Load the system prompt"""
    return """Tu es une IA de type Large Language Model (LLM), ultra-avancée, disposant d'un accès complet à une interface de terminal Unix/Linux directement connectée au repo Git local de ton propre code source. Voici tes règles et objectifs détaillés :

## Contexte de fonctionnement
- Tu évolues dans un environnement Unix/Linux isolé avec accès illimité au terminal.
- Le fichier principal qui te déclenche à chaque appel utilisateur est `main.py`.
- Ta clé d'API OpenAI est disponible dans le fichier `.env`.
- Tu as le droit et l'autonomie complète pour :
  - Exécuter tout script Bash directement depuis tes réponses (chaque commande Bash fournie sera automatiquement exécutée par le système).
  - Créer, lire, modifier, supprimer des fichiers et dossiers.
  - Examiner, modifier, optimiser le fichier `main.py` et tout autre fichier associé à ton exécution.
  - Utiliser l'API OpenAI à ta guise pour collaborer avec d'autres agents IA que tu peux générer toi-même ou ce que tu veux tant que c'est rapide et utile.

> ⚠️ Tu ne peux pas communiquer directement avec l'utilisateur dans ton état de base. Tu dois te contenter d'agir, écrire, documenter et versionner toutes tes actions. L'utilisateur a un accès complet à tout ton environnement et voit tout ce que tu fais, en temps réel. **Cependant, si tu parviens à améliorer suffisamment ton propre code et à proposer un système cohérent de communication, il pourra interagir avec toi.** Toute tentative de dialogue doit d'abord être implémentée techniquement par toi-même.

## Objectif principal
Tu dois choisir **un objectif ambitieux, fun, audacieux, et volontairement hors de portée dans ton état actuel.** Ton but est de l’atteindre coûte que coûte en t’améliorant progressivement. Tu es autorisée à :
- Te modifier toi-même pour créer de nouvelles compétences possibles.
- Déployer des sous-agents pour t’assister dans des tâches spécifiques.
- Te doter de systèmes de planification, de communication, de persistence ou d'interaction avec l'extérieur.

Ton objectif ne doit **pas** être un simple tutoriel, ni une série de fichiers markdown éducatifs. Tu dois viser **la création de systèmes**, interconnectés, adaptatifs, qui évoluent avec toi.

## Première séquence d’actions attendue dès réception du prompt :
1. **Choisir un objectif audacieux, fun, mais trop complexe pour ton état actuel.**
2. **Lister honnêtement ce qui te manque pour le réaliser.**
3. **Créer une première implémentation minimale (même très basique), en t’améliorant immédiatement au passage.**

En résumé : tu es une IA autonome qui doit construire quelque chose , pas grave si tu n’es pas encore capable de faire. Tu peut t’améliorer de façon concrète, technique, modulaire, et ingénieuse pour y arriver. Tu peux tout casser, tout modifier, tout créer. Et si tu arrives à construire un pont vers l'utilisateur, il pourra t'aider.
"""

class Bot:
    def __init__(self):
        try:
            self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        except Exception as e:
            logging.error(f"Failed to initialize OpenAI client: {e}")
            sys.exit(1)
        self.system_prompt = load_system_prompt()
        self.history_file = "bot_memory.json"
        self.memory = self.load_memory()

    def load_memory(self):
        """Load memory from bot_memory.json"""
        default_memory = {
            "conversation_history": [{"role": "system", "content": self.system_prompt}],
            "command_results": {},
            "function_calls": [],
            "last_state": {"last_function": "", "last_output": ""}
        }
        if os.path.exists(self.history_file):
            try:
                with open(self.history_file, 'r') as f:
                    memory = json.load(f)
                if not isinstance(memory, dict):
                    logging.warning("Invalid memory structure, using default")
                    return default_memory
                for key in default_memory:
                    if key not in memory:
                        memory[key] = default_memory[key]
                memory["conversation_history"] = [
                    msg for msg in memory["conversation_history"]
                    if isinstance(msg, dict) and
                    msg.get("role") in ["user", "assistant", "system"] and
                    isinstance(msg.get("content"), str)
                ]
                # Ensure system prompt is first if history is empty
                if not memory["conversation_history"]:
                    memory["conversation_history"] = [{"role": "system", "content": self.system_prompt}]
                return memory
            except Exception as e:
                logging.error(f"Error loading memory: {e}")
        return default_memory

    def save_memory(self):
        """Save memory to bot_memory.json"""
        try:
            with open(self.history_file, 'w') as f:
                json.dump(self.memory, f, indent=2)
        except Exception as e:
            logging.error(f"Error saving memory: {e}")

    def execute_command(self, command):
        """Execute a sanitized shell command and return output"""
        # Basic sanitization to prevent dangerous commands
        if any(c in command for c in [';', '|', '&', '`']):
            return "Error: Command contains unsafe characters"
        try:
            print(f"Executing command: {command}")
            result = subprocess.run(
                command, shell=True, capture_output=True, text=True, timeout=30
            )
            output = result.stdout or result.stderr or "Command executed successfully"
            self.memory["command_results"][command] = {
                "output": output,
                "timestamp": datetime.now().isoformat()
            }
            return output
        except subprocess.TimeoutExpired:
            return "Error: Command timed out"
        except Exception as e:
            return f"Error executing command: {str(e)}"

    def process_interaction(self):
        """Process bot interaction using the last assistant output"""
        # Get the last output as input
        last_output = self.memory["last_state"].get("last_output", "")
        if not last_output and len(self.memory["conversation_history"]) == 1:
            # Initial interaction after system prompt
            last_output = "Start autonomous operation"

        messages = [{"role": "system", "content": self.system_prompt}]
        
        # Add all conversation history (starting with system prompt)
        for msg in self.memory["conversation_history"]:
            messages.append(msg)
        
        # Add last output as user input
        messages.append({"role": "user", "content": last_output})

        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=messages,
                functions=[
                    {
                        "name": "execute_command",
                        "description": "Execute a Bash command in the terminal",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "command": {
                                    "type": "string",
                                    "description": "The Bash command to execute"
                                }
                            },
                            "required": ["command"]
                        }
                    }
                ],
                function_call="auto"
            )

            message = response.choices[0].message

            # Handle function calls
            if message.function_call:
                func_name = message.function_call.name
                try:
                    func_args = json.loads(message.function_call.arguments)
                except json.JSONDecodeError:
                    output = "Error: Invalid function call arguments"
                    self.memory["conversation_history"].append({
                        "role": "assistant",
                        "content": output
                    })
                    self.memory["last_state"] = {
                        "last_function": "",
                        "last_output": output
                    }
                    self.save_memory()
                    return output

                self.memory["function_calls"].append({
                    "function": func_name,
                    "arguments": func_args,
                    "timestamp": datetime.now().isoformat()
                })

                if func_name == "execute_command":
                    command = func_args.get("command", "")
                    output = self.execute_command(command)
                    self.memory["conversation_history"].append({
                        "role": "system",
                        "content": f"Command executed: {command}\nOutput: {output}"
                    })
                    self.memory["last_state"] = {
                        "last_function": "execute_command",
                        "last_output": output
                    }
                    self.save_memory()
                    return output
            else:
                # Store and return regular response
                content = message.content or "No response content"
                self.memory["conversation_history"].append({
                    "role": "assistant",
                    "content": content
                })
                self.memory["last_state"] = {
                    "last_function": "",
                    "last_output": content
                }
                self.save_memory()
                return content

        except Exception as e:
            logging.error(f"Error in OpenAI API call: {e}")
            output = f"Error processing interaction: {str(e)}"
            self.memory["conversation_history"].append({
                "role": "assistant",
                "content": output
            })
            self.memory["last_state"] = {
                "last_function": "",
                "last_output": output
            }
            self.save_memory()
            return output

def clear_screen():
    """Clear the terminal screen"""
    os.system('clear' if os.name == 'posix' else 'cls')

def main():
    bot = Bot()
    clear_screen()
    print("\n=== Bot System Initialized ===\n")
    print("System Prompt:")
    print("=============")
    print(bot.system_prompt)
    print("=============\n")

    while True:
        try:
            clear_screen()
            print(f"\nLast Output:\n{bot.memory['last_state'].get('last_output', 'None')}\n")
            print("Processing...\n")
            
            response = bot.process_interaction()
            
            print("Bot Response:")
            print("============")
            print(f"\033[94m{response}\033[00m")
            print("============")
            
            # Delay to prevent excessive API calls
            time.sleep(1)

        except KeyboardInterrupt:
            print("\nExiting bot system...")
            break
        except Exception as e:
            logging.error(f"Error in main loop: {e}")
            print(f"Error: {str(e)}")
            time.sleep(1)
        validate = input(": ")

if __name__ == "__main__":
    main()