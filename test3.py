from google import genai

# Connect to Gemini
client = genai.Client(api_key="config.py")

# Read the PRG notes once when the program starts
with open("prg_notes.txt", "r", encoding="utf-8") as f:
    notes = f.read()

print("PRG Chatbot is ready!")
print("Type 'exit' to quit.\n")

# Keep chatting until the user exits
while True:
    question = input("You: ")

    # Exit condition
    if question.lower() == "exit":
        print("Goodbye!")
        break

    # Send notes and question to Gemini
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=f"""
You are a Programming (PRG) class assistant.

Use only the notes below to answer the question.

Notes:
{notes}

Question:
{question}

If the answer is not contained in the notes, say:
"I don't have enough information in the provided notes to answer that."
"""
    )

    # Print Gemini's answer
    print("\nBot:", response.text)
    print()