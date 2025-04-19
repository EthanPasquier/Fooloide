class CommunicationProtocol:
    def __init__(self):
        self.messages = []

    def send_message(self, message):
        self.messages.append(message)
        print(f"Message sent: {message}")

    def receive_messages(self):
        return self.messages

# Example usage of CommunicationProtocol
if __name__ == "__main__":
    cp = CommunicationProtocol()
    cp.send_message("Hello, User!")
    print(cp.receive_messages())
