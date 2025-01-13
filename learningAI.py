import tkinter as tk
from tkinter import ttk, filedialog, scrolledtext, messagebox, font
from ttkthemes import ThemedTk
import emoji
import fitz  # PyMuPDF for PDF handling
import google.generativeai as genai
from deep_translator import GoogleTranslator
import pytesseract
from PIL import Image,ImageTk
import io
import os
import sys

class StudentAIAssistant:
    #constructor
    def __init__(self, root):
        self.root = root
        #self.root = ThemedTk(theme="Equilux")
        self.root.title("AI Learning Assistance")
        self.root.geometry("1200x800")

        # Configure dark theme colors
        self.colors = {
            'bg': '#282c34',
            'fg': '#abb2bf',
            'accent': '#61afef',
            'darker': '#21252b',
            'lighter': '#333842'
        }
        
        # Configure Tesseract path for Windows
        if os.name == 'nt':  # Windows
            pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
        
        # Configure fonts
        self.default_font = font.nametofont("TkDefaultFont")
        self.default_font.configure(size=10)
        self.header_font = font.Font(family="Iskoola Pota", size=16, weight="bold")
        
        # Initialize Gemini API with environment variable
        genai.configure(api_key='AIzaSyATgL92t9qBCe4eqFX1cSfyfkzKMooQM48')
        
        # Configure Gemini model
        generation_config = {
            "temperature": 1,
            "top_p": 0.95,
            "top_k": 40,
            "max_output_tokens": 8192,
            "response_mime_type": "text/plain",
        }
        
        self.model = genai.GenerativeModel(
            model_name="gemini-2.0-flash-exp",
            generation_config=generation_config,
        )
        
        # Initialize chat session
        self.chat_session = self.model.start_chat(
            history=[
                {
                    "role": "user",
                    "parts": ["Hi"],
                },
                {
                    "role": "model",
                    "parts": [
                        "Hi there! Submit your PDF to me. Ask anything with it?\n",
                    ],
                },
            ]
        )
        
        # Initialize translator
        self.translator = GoogleTranslator(source='auto', target='en')
        
        # Storage for extracted text and questions
        self.current_text = ""
        self.questions = []
        self.current_file_path = None
        
        self.setup_ui()

    def setup_styles(self):
        """Configure dark theme styles"""
        style = ttk.Style()
        style.configure('Dark.TFrame', background=self.colors['bg'])
        style.configure('Dark.TLabel', background=self.colors['bg'], foreground=self.colors['fg'])
        style.configure('Dark.TButton', background=self.colors['accent'], foreground='white')
        style.configure('Dark.TPanedwindow', background=self.colors['bg'])
        style.configure('Dark.TCombobox', background=self.colors['darker'], fieldbackground=self.colors['darker'],
                       foreground=self.colors['fg'], arrowcolor=self.colors['fg'])
        
        # Configure root background
        self.root.configure(bg=self.colors['bg'])
    
    def setup_ui(self):
        # Header
        self.header_frame = ttk.Frame(self.root)
        self.header_frame.pack(fill=tk.X, padx=5, pady=5)
        header_label = ttk.Label(self.header_frame, text=" 🤖 AI Learning Assistance 🤖", font=self.header_font)
        header_label.pack(anchor=tk.CENTER)
        
        # Create main container
        self.main_container = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        self.main_container.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Left panel for document display
        self.left_frame = ttk.Frame(self.main_container)
        self.main_container.add(self.left_frame)
        
        # Document viewer with Unicode support
        self.doc_viewer = scrolledtext.ScrolledText(self.left_frame, font=("Iskoola Pota", 10))
        self.doc_viewer.pack(fill=tk.BOTH, expand=True)
        
        # Right panel for interaction
        self.right_frame = ttk.Frame(self.main_container)
        self.main_container.add(self.right_frame)
        
        # Controls
        self.setup_controls()
        
        # Chat/QA area with Unicode support
        # self.chat_area = scrolledtext.ScrolledText(self.right_frame, height=20, font=("Iskoola Pota", 10))
        # self.chat_area.pack(fill=tk.BOTH, expand=True)

        self.setup_chat_area()
        
        # Input area
        self.input_frame = ttk.Frame(self.right_frame)
        self.input_frame.pack(fill=tk.X, pady=5)
        
        self.input_field = ttk.Entry(self.input_frame, font=("Iskoola Pota", 10))
        self.input_field.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        self.send_button = ttk.Button(self.input_frame, text="Send 📤", command=self.handle_input)
        self.send_button.pack(side=tk.RIGHT)
        
        # Clear buttons frame
        self.clear_buttons_frame = ttk.Frame(self.right_frame)
        self.clear_buttons_frame.pack(fill=tk.X, pady=5)
        
        self.clear_chat_btn = ttk.Button(self.clear_buttons_frame, text="🗑️ Clear Chat", command=self.clear_chat)
        self.clear_chat_btn.pack(side=tk.LEFT, padx=5)
        
        self.clear_doc_btn = ttk.Button(self.clear_buttons_frame, text="📄 Clear Document", command=self.clear_document)
        self.clear_doc_btn.pack(side=tk.LEFT, padx=5)
        
        # Footer
        self.footer_frame = ttk.Frame(self.root)
        self.footer_frame.pack(fill=tk.X, padx=5, pady=5)
        footer_label = ttk.Label(self.footer_frame, text="Copyright © 2025 SandaryAbey", font=("Arial", 8))
        footer_label.pack(anchor=tk.CENTER)
    
    def setup_chat_area(self):
        """Setup enhanced chat area with text decorations"""
        self.chat_area = scrolledtext.ScrolledText(
            self.right_frame,
            height=20,
            font=("Segoe UI", 10),
            bg=self.colors['darker'],
            fg=self.colors['fg'],
            wrap=tk.WORD,
            padx=10,
            pady=10
        )
        self.chat_area.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Configure tags for text decorations
        self.chat_area.tag_configure("bold", font=("Segoe UI", 10, "bold"))
        self.chat_area.tag_configure("italic", font=("Segoe UI", 10, "italic"))
        self.chat_area.tag_configure("underline", underline=1)
        self.chat_area.tag_configure("user", foreground="#4CAF50")
        self.chat_area.tag_configure("ai", foreground="#61afef")
        self.chat_area.tag_configure("code", font=("Consolas", 9), background="#1E1E1E", foreground="#D4D4D4")
        self.chat_area.tag_configure("timestamp", foreground="#808080", font=("Segoe UI", 8))
        self.chat_area.tag_configure("highlight", background=self.colors['accent'], foreground="white")

    def parse_formatting(self, text, base_tag=None):
        """Parse text formatting and return segments with their tags"""
        segments = []
        current_pos = 0
        
        # Regular expressions could be used here, but let's do it manually for clarity
        while current_pos < len(text):
            # Check for bold text (**text**)
            if text[current_pos:].startswith('**') and '**' in text[current_pos+2:]:
                end_pos = text.find('**', current_pos+2)
                if end_pos != -1:
                    bold_text = text[current_pos+2:end_pos]
                    segments.append((bold_text, ["bold"] + ([base_tag] if base_tag else [])))
                    current_pos = end_pos + 2
                    continue
                    
            # Check for italic text (*text*)
            if text[current_pos:].startswith('*') and '*' in text[current_pos+1:]:
                end_pos = text.find('*', current_pos+1)
                if end_pos != -1:
                    italic_text = text[current_pos+1:end_pos]
                    segments.append((italic_text, ["italic"] + ([base_tag] if base_tag else [])))
                    current_pos = end_pos + 1
                    continue
                    
            # Check for code blocks (`text`)
            if text[current_pos:].startswith('`') and '`' in text[current_pos+1:]:
                end_pos = text.find('`', current_pos+1)
                if end_pos != -1:
                    code_text = text[current_pos+1:end_pos]
                    segments.append((code_text, ["code"] + ([base_tag] if base_tag else [])))
                    current_pos = end_pos + 1
                    continue
            
            # Regular text
            next_special = float('inf')
            for marker in ['**', '*', '`']:
                pos = text.find(marker, current_pos)
                if pos != -1:
                    next_special = min(next_special, pos)
            
            if next_special == float('inf'):
                segments.append((text[current_pos:], [base_tag] if base_tag else []))
                break
            else:
                if next_special > current_pos:
                    segments.append((text[current_pos:next_special], [base_tag] if base_tag else []))
                current_pos = next_special
                
        return segments

    def insert_formatted_text(self, text, base_tag=None):
        """Insert text with formatting into chat area"""
        segments = self.parse_formatting(text, base_tag)
        
        for text, tags in segments:
            for tag in tags:
                if tag:
                    self.chat_area.insert(tk.END, text, tag)
                    break
            else:
                self.chat_area.insert(tk.END, text)

    def display_qa(self, question, answer):
            """Display Q&A with enhanced formatting"""
            timestamp = self.get_timestamp()
            self.chat_area.configure(state='normal')
            
            # Insert timestamp and question
            self.chat_area.insert(tk.END, f"\n{timestamp} ", "timestamp")
            self.chat_area.insert(tk.END, "You: ", "bold")
            self.insert_formatted_text(question, "user")
            self.chat_area.insert(tk.END, "\n")
            
            # Insert AI response
            self.chat_area.insert(tk.END, f"{timestamp} ", "timestamp")
            self.chat_area.insert(tk.END, "AI: ", "bold")
            self.insert_formatted_text(answer, "ai")
            self.chat_area.insert(tk.END, "\n")
            
            self.chat_area.configure(state='disabled')
            self.chat_area.see(tk.END)
        
    def setup_controls(self):
            control_frame = ttk.Frame(self.right_frame)
            control_frame.pack(fill=tk.X, pady=5)
            
            # Upload button
            self.upload_btn = ttk.Button(control_frame, text="Upload Document", command=self.upload_document)
            self.upload_btn.pack(side=tk.LEFT, padx=5)
            
            # Language selection
            self.language_var = tk.StringVar(value="English")
            self.language_select = ttk.Combobox(control_frame, 
                                            textvariable=self.language_var,
                                            values=["English", "සිංහල"])
            self.language_select.pack(side=tk.LEFT, padx=5)
            self.language_select.bind('<<ComboboxSelected>>', self.on_language_change)
        
    def clear_chat(self):
            self.chat_area.delete('1.0', tk.END)
        
    def clear_document(self):
            self.doc_viewer.delete('1.0', tk.END)
            self.current_text = ""
            self.current_file_path = None
        
    def extract_text_from_pdf(self, pdf_path):
            text = ""
            doc = fitz.open(pdf_path)
            
            for page_num in range(len(doc)):
                page = doc[page_num]
                
                # Extract text
                text += page.get_text()
                
                # Extract images and perform OCR
                image_list = page.get_images()
                for img_index, img in enumerate(image_list):
                    try:
                        xref = img[0]
                        base_image = doc.extract_image(xref)
                        image_bytes = base_image["image"]
                        
                        # Create PIL Image from bytes
                        image = Image.open(io.BytesIO(image_bytes))
                        
                        # Perform OCR on the image
                        img_text = pytesseract.image_to_string(image, lang='eng+sin')
                        text += "\n" + img_text
                    except Exception as e:
                        print(f"Error processing image {img_index} on page {page_num}: {str(e)}")
                        continue
            
            return text
    def get_timestamp(self):
        """Return current timestamp in HH:MM format"""
        from datetime import datetime
        return datetime.now().strftime("[%H:%M]")

    
    def on_language_change(self, event=None):
        if self.language_var.get() == "සිංහල":
            self.translator = GoogleTranslator(source='auto', target='si')
        else:
            self.translator = GoogleTranslator(source='auto', target='en')
    
    def upload_document(self):
        file_path = filedialog.askopenfilename(
            filetypes=[("PDF files", "*.pdf"), ("Text files", "*.txt"), 
                    ("Image files", "*.png *.jpg *.jpeg *.bmp *.gif")])
        if file_path:
            self.current_file_path = file_path
            self.load_document(file_path)
            # Display confirmation message
            if self.language_var.get() == "සිංහල":
                self.chat_area.insert(tk.END, "\nලේඛනය සාර්ථකව උඩුගත කර ඇත. ඔබට කැමති ප්‍රශ්නයක් අසන්න.\n")
            else:
                self.chat_area.insert(tk.END, "\nDocument successfully loaded. Feel free to ask any questions.\n")
            self.chat_area.see(tk.END)
    
    def load_document(self, file_path):
     try:
        if file_path.lower().endswith('.pdf'):
            self.current_text = self.extract_text_from_pdf(file_path)
            
            # Check if text was extracted properly
            if not self.current_text or self.current_text.isspace():
                raise Exception("No text could be extracted from the PDF")
                
            # Clean up any remaining encoding issues
            self.current_text = self.current_text.replace('�', '')
            
        elif file_path.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.gif')):
            # Extract text from image with Sinhala support
            self.current_text = pytesseract.image_to_string(
                Image.open(file_path), 
                lang='sin+eng'
            )
        else:
            # For text files, try multiple encodings
            encodings = ['utf-8', 'iso-8859-1', 'cp1252']
            for encoding in encodings:
                try:
                    with open(file_path, 'r', encoding=encoding) as file:
                        self.current_text = file.read()
                    break
                except UnicodeDecodeError:
                    continue
            
        if not self.current_text:
            raise Exception("Could not read the document with any supported encoding")
            
        self.doc_viewer.delete('1.0', tk.END)
        self.doc_viewer.insert(tk.END, self.current_text)
        
     except Exception as e:
        self.show_error(f"Error loading document: {str(e)}")
    
    def handle_input(self):
        question = self.input_field.get()
        if not question:
            return
        
        # Clear input field
        self.input_field.delete(0, tk.END)
        
        # Check if document is loaded
        if not self.current_text.strip():
            if self.language_var.get() == "සිංහල":
                response = "කරුණාකර පළමුව ලේඛනයක් උඩුගත කරන්න. මට උඩුගත කරන ලද ලේඛනයේ අන්තර්ගතය පිළිබඳ ප්‍රශ්න වලට පමණක් පිළිතුරු දිය හැක."
            else:
                response = "Hi Please upload a document first. I can only answer questions about the content of the uploaded document."
            self.display_qa(question, response)
            return
        
        self.process_question(question)
    
    def process_question(self, question):
        try:
            # Check if document is loaded
            if not self.current_text.strip():
                response = "Please upload a document first. I can only answer questions about the content of the uploaded document."
                self.display_qa(question, response)
                return
                
            # Translate to English if needed
            original_question = question
            if self.language_var.get() == "සිංහල":
                question = self.translator.translate(question)
            
            # Create context from current document
            prompt = f"""
            You are an AI assistant that answers questions based on the provided document content ,
            please answer the question. Be clear and educational in your response.If the user needs more information about something in that document content, search beyond the document.
            If the question is unrelated to the document contents, politely inform the user that
            you can only answer questions related to the document content.


            Context: {self.current_text}

            Question: {question}

            Remember:
            1. Only answer questions that can be answered using the document content
            2. If the question is not related to the document content, respond with:
            "I can only answer questions related to the provided document content. Your question appears to be outside the scope of the current document."
            3. Be clear and educational in your response
            4. If the user needs more information about something in that document content, search beyond the document.
            """
            
            # Get AI response using chat session
            response = self.chat_session.send_message(prompt)
            answer = response.text
            
            # Translate back to Sinhala if needed
            if self.language_var.get() == "සිංහල":
                self.translator = GoogleTranslator(source='auto', target='si')
                answer = self.translator.translate(answer)
            
            self.display_qa(original_question, answer)
            
        except Exception as e:
            if "429" in str(e):
                self.show_error("API quota exceeded. Please check your API key or try again later.")
            else:
                self.show_error(f"Error processing question: {str(e)}")

            
        except Exception as e:
            if "429" in str(e):
                self.show_error("API quota exceeded. Please check your API key or try again later.")
            else:
                self.show_error(f"Error processing question: {str(e)}")
    
    # def display_qa(self, question, answer):
    #     self.chat_area.insert(tk.END, f"\nQ: {question}\n")
    #     self.chat_area.insert(tk.END, f"A: {answer}\n")
    #     self.chat_area.see(tk.END)
    
    def show_error(self, message):
        messagebox.showerror("Error", message)

if __name__ == "__main__":
    root = tk.Tk()
    app = StudentAIAssistant(root)
    root.mainloop()