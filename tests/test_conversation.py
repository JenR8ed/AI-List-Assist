import os
# from dotenv import load_dotenv
from services.conversation_orchestrator import ConversationOrchestrator

# Load env to get your Gemini API Key
# load_dotenv()

def run_cli_test():
    print("🤖 Initializing Conversation Orchestrator...")
    orchestrator = ConversationOrchestrator()

    # 1. Simulate an item with some missing info
    # We know the Name and Category, but missing Price, Condition, Weight, etc.
    initial_data = {
        "item_name": "Vintage Nikon Camera",
        "category": "Cameras",
        "brand": "Nikon"
    }

    # 2. Start the Session
    print(f"\n📦 Item: {initial_data['item_name']}")
    state = orchestrator.start_conversation("test_item_123", initial_data)

    print(f"🤖 AI: {state.current_question}")

    # 3. Interactive Loop
    while not state.is_complete:
        # Get user input from terminal
        user_answer = input("You: ")

        # Process the answer
        state = orchestrator.process_answer(state.session_id, user_answer)

        # Debug: Show what the AI extracted
        print(f"   [Debug] Known fields: {list(state.known_fields.keys())}")
        print(f"   [Debug] Confidence: {state.confidence}")

        if state.current_question:
            print(f"🤖 AI: {state.current_question}")
        else:
            print("\n✅ Conversation Complete!")
            print("Final Data Gathered:")
            print(state.known_fields)

if __name__ == "__main__":
    run_cli_test()
