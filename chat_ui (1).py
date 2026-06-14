"""
PRG 200 Chatbot - chat_ui.py
=============================
Tkinter desktop chat interface for the PRG 200 RAG chatbot.

Features:
- Chat window showing the conversation
- Input box + Send button
- Sidebar listing past sessions (loaded from SQLite)
- Click a past session to reload that conversation
- "New Chat" button to start a fresh session

HOW TO RUN:
    python3 chat_ui.py

Requires:
    - rag.py        (your RAG pipeline)
    - database.py   (SQLite chat history)
    - chroma_db/    (created by ingest.py)
"""

import tkinter as tk
from tkinter import scrolledtext, messagebox
import threading

import database
import rag


# ── MAIN APPLICATION CLASS ────────────────────────────────────────────────────

class ChatbotApp:
    def __init__(self, root):
        self.root = root
        self.root.title("PRG 200 Chatbot")
        self.root.geometry("900x600")
        self.root.configure(bg="#1e1e1e")

        # Track current session
        self.session_id = database.new_session_id()
        self.history = []   # list of (role, message) tuples for current session

        self.build_ui()
        self.refresh_sessions_list()

    # ── UI LAYOUT ─────────────────────────────────────────────────────────────

    def build_ui(self):
        # Main container split into sidebar (left) and chat area (right)
        main_frame = tk.Frame(self.root, bg="#1e1e1e")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # ── SIDEBAR (left) ──────────────────────────────────────────────────
        sidebar = tk.Frame(main_frame, bg="#252526", width=220)
        sidebar.pack(side=tk.LEFT, fill=tk.Y)

        title_label = tk.Label(
            sidebar, text="PRG 200 Chatbot",
            bg="#252526", fg="white",
            font=("Arial", 13, "bold"), pady=10
        )
        title_label.pack(fill=tk.X)

        new_chat_btn = tk.Button(
            sidebar, text="+ New Chat",
            command=self.start_new_chat,
            bg="#0e639c", fg="#000000",
            activebackground="#1177bb", activeforeground="#ffffff",
            relief=tk.FLAT, font=("Arial", 10, "bold"),
            cursor="hand2", pady=8, borderwidth=0
        )
        new_chat_btn.pack(fill=tk.X, padx=10, pady=(0, 10))

        history_label = tk.Label(
            sidebar, text="Past Sessions",
            bg="#252526", fg="#aaaaaa",
            font=("Arial", 9, "bold"), anchor="w"
        )
        history_label.pack(fill=tk.X, padx=10)

        # Scrollable list of past sessions
        self.sessions_listbox = tk.Listbox(
            sidebar, bg="#2d2d2d", fg="white",
            relief=tk.FLAT, font=("Arial", 9),
            selectbackground="#0e639c", highlightthickness=0
        )
        self.sessions_listbox.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        self.sessions_listbox.bind("<<ListboxSelect>>", self.load_selected_session)

        # ── CHAT AREA (right) ───────────────────────────────────────────────
        chat_frame = tk.Frame(main_frame, bg="#1e1e1e")
        chat_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        # Chat display (scrollable text area)
        self.chat_display = scrolledtext.ScrolledText(
            chat_frame, wrap=tk.WORD,
            bg="#1e1e1e", fg="#e8e8e8",
            font=("Arial", 12), state=tk.DISABLED,
            padx=16, pady=16, relief=tk.FLAT,
            borderwidth=0, highlightthickness=0
        )
        self.chat_display.pack(fill=tk.BOTH, expand=True, padx=10, pady=(10, 5))

        # Configure text colors for different speakers
        self.chat_display.tag_config("user", foreground="#4fc3f7", font=("Arial", 12, "bold"))
        self.chat_display.tag_config("bot", foreground="#81c784", font=("Arial", 12, "bold"))
        self.chat_display.tag_config("message", foreground="#e8e8e8", font=("Arial", 12))
        self.chat_display.tag_config("thinking", foreground="#888888", font=("Arial", 11, "italic"))

        # Input area (bottom)
        input_frame = tk.Frame(chat_frame, bg="#1e1e1e")
        input_frame.pack(fill=tk.X, padx=10, pady=(0, 10))

        self.input_box = tk.Entry(
            input_frame, font=("Arial", 12),
            bg="#2d2d2d", fg="#ffffff",
            relief=tk.FLAT, insertbackground="#ffffff",
            highlightthickness=1, highlightbackground="#3c3c3c",
            highlightcolor="#0e639c"
        )
        self.input_box.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=10, padx=(0, 8))
        self.input_box.bind("<Return>", lambda event: self.send_message())
        self.input_box.focus()

        send_btn = tk.Button(
            input_frame, text="Send",
            command=self.send_message,
            bg="#0e639c", fg="#000000",
            activebackground="#1177bb", activeforeground="#000000",
            relief=tk.FLAT, font=("Arial", 11, "bold"),
            cursor="hand2", padx=24, pady=8,
            borderwidth=0
        )
        send_btn.pack(side=tk.RIGHT, fill=tk.Y)

        # Welcome message
        self.append_message("bot", "Hi! I'm your PRG 200 assistant. Ask me anything about the course, assignments, deadlines, or Python concepts covered in class.")

    # ── DISPLAY A MESSAGE IN THE CHAT WINDOW ─────────────────────────────────

    def append_message(self, role, message):
        self.chat_display.config(state=tk.NORMAL)

        if role == "user":
            self.chat_display.insert(tk.END, "You: ", "user")
        else:
            self.chat_display.insert(tk.END, "Bot: ", "bot")

        self.chat_display.insert(tk.END, message + "\n\n", "message")
        self.chat_display.config(state=tk.DISABLED)
        self.chat_display.see(tk.END)   # auto-scroll to bottom

    # ── SEND MESSAGE ──────────────────────────────────────────────────────────

    def send_message(self):
        question = self.input_box.get().strip()
        if not question:
            return

        # Clear input box
        self.input_box.delete(0, tk.END)

        # Show user's message
        self.append_message("user", question)
        database.save_message(self.session_id, "user", question)
        self.history.append(("user", question))

        # Show "thinking" placeholder
        self.chat_display.config(state=tk.NORMAL)
        self.chat_display.insert(tk.END, "Bot is thinking...\n\n", "thinking")
        self.chat_display.config(state=tk.DISABLED)
        self.chat_display.see(tk.END)

        # Run the RAG call in a separate thread so the UI doesn't freeze
        threading.Thread(target=self.get_bot_response, args=(question,), daemon=True).start()

    # ── GET RESPONSE FROM RAG PIPELINE (runs in background thread) ──────────

    def get_bot_response(self, question):
        try:
            answer = rag.get_answer(question, history=self.history)
        except Exception as e:
            answer = f"Sorry, something went wrong: {e}"

        # Update UI back on the main thread
        self.root.after(0, self.show_bot_response, answer)

    def show_bot_response(self, answer):
        # Remove the "thinking" placeholder
        self.chat_display.config(state=tk.NORMAL)
        self.chat_display.delete("end-3l", "end-1l")
        self.chat_display.config(state=tk.DISABLED)

        # Show the real answer
        self.append_message("bot", answer)
        database.save_message(self.session_id, "assistant", answer)
        self.history.append(("assistant", answer))

        # Refresh sidebar in case this is a new session
        self.refresh_sessions_list()

    # ── SIDEBAR: REFRESH PAST SESSIONS LIST ──────────────────────────────────

    def refresh_sessions_list(self):
        self.sessions_listbox.delete(0, tk.END)
        self.session_ids_in_order = []

        for session_id, first_msg, timestamp in database.get_all_sessions():
            display_text = first_msg[:35] + ("..." if len(first_msg) > 35 else "")
            self.sessions_listbox.insert(tk.END, display_text)
            self.session_ids_in_order.append(session_id)

    # ── SIDEBAR: LOAD A PAST SESSION ─────────────────────────────────────────

    def load_selected_session(self, event):
        selection = self.sessions_listbox.curselection()
        if not selection:
            return

        index = selection[0]
        selected_session_id = self.session_ids_in_order[index]

        # Switch to this session
        self.session_id = selected_session_id
        self.history = []

        # Clear and reload chat display
        self.chat_display.config(state=tk.NORMAL)
        self.chat_display.delete(1.0, tk.END)
        self.chat_display.config(state=tk.DISABLED)

        for role, message, timestamp in database.get_history(selected_session_id):
            self.append_message("user" if role == "user" else "bot", message)
            self.history.append((role, message))

    # ── START A NEW CHAT SESSION ─────────────────────────────────────────────

    def start_new_chat(self):
        self.session_id = database.new_session_id()
        self.history = []

        self.chat_display.config(state=tk.NORMAL)
        self.chat_display.delete(1.0, tk.END)
        self.chat_display.config(state=tk.DISABLED)

        self.append_message("bot", "New chat started. Ask me anything about PRG 200!")


# ── RUN THE APP ────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    root = tk.Tk()
    app = ChatbotApp(root)
    root.mainloop()