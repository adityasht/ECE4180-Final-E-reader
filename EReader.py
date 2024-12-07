import os
from PIL import Image, ImageDraw, ImageFont
import textwrap
import markdown
import epub
import PyPDF2
import html2text
import re

class EReader:
    def __init__(self, epd, resources_dir):
        self.epd = epd
        self.width = epd.width  # 648
        self.height = epd.height  # 480
        self.books_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'Books')
        self.current_book = None
        self.current_page = 0
        self.book_content = []
        self.selection_index = 0
        self.in_book = False
        
        # Initialize fonts
        self.font_large = ImageFont.truetype(os.path.join(resources_dir, 'Font.ttc'), 36)
        self.font_medium = ImageFont.truetype(os.path.join(resources_dir, 'Font.ttc'), 24)
        self.font_small = ImageFont.truetype(os.path.join(resources_dir, 'Font.ttc'), 18)
        
        # HTML to text converter
        self.html_converter = html2text.HTML2Text()
        self.html_converter.ignore_links = True
        self.html_converter.ignore_images = True
        
        # Create Books directory if it doesn't exist
        if not os.path.exists(self.books_dir):
            os.makedirs(self.books_dir)

    def get_available_books(self):
        """Get list of supported book files in Books directory"""
        if not os.path.exists(self.books_dir):
            return []
        supported_extensions = ('.txt', '.md', '.epub', '.pdf', '.html', '.htm')
        return [f for f in os.listdir(self.books_dir) if f.lower().endswith(supported_extensions)]

    def load_book(self, book_name):
        """Load and paginate book content"""
        try:
            file_path = os.path.join(self.books_dir, book_name)
            content = self.read_book_content(file_path)
            if content is None:
                return False

            # Clean up the content
            content = self.clean_text(content)
            
            # Calculate layout parameters
            char_width = self.font_medium.getsize('x')[0]
            chars_per_line = (self.width - 60) // char_width
            lines_per_page = (self.height - 80) // (self.font_medium.getsize('x')[1] + 5)
            
            # Paginate content
            self.book_content = self.paginate_content(content, chars_per_line, lines_per_page)
            
            self.current_book = book_name
            self.current_page = 0
            self.in_book = True
            return True
            
        except Exception as e:
            print(f"Error loading book: {e}")
            return False

    def read_book_content(self, file_path):
        """Read content from different file formats"""
        extension = os.path.splitext(file_path)[1].lower()
        
        try:
            if extension == '.txt':
                with open(file_path, 'r', encoding='utf-8') as file:
                    return file.read()
                    
            elif extension == '.md':
                with open(file_path, 'r', encoding='utf-8') as file:
                    md_content = file.read()
                    # Convert markdown to HTML, then to plain text
                    html_content = markdown.markdown(md_content)
                    return self.html_converter.handle(html_content)
                    
            elif extension == '.epub':
                book = epub.read_epub(file_path)
                content = []
                for item in book.get_items():
                    if item.get_type() == epub.ITEM_DOCUMENT:
                        content.append(self.html_converter.handle(item.get_content().decode('utf-8')))
                return '\n\n'.join(content)
                
            elif extension == '.pdf':
                content = []
                with open(file_path, 'rb') as file:
                    pdf_reader = PyPDF2.PdfReader(file)
                    for page in pdf_reader.pages:
                        content.append(page.extract_text())
                return '\n\n'.join(content)
                
            elif extension in ['.html', '.htm']:
                with open(file_path, 'r', encoding='utf-8') as file:
                    html_content = file.read()
                    return self.html_converter.handle(html_content)
                    
            else:
                raise ValueError(f"Unsupported file format: {extension}")
                
        except Exception as e:
            print(f"Error reading file {file_path}: {e}")
            return None

    def clean_text(self, text):
        """Clean up text content"""
        if not text:
            return ""
            
        # Replace multiple newlines with double newline
        text = re.sub(r'\n\s*\n', '\n\n', text)
        
        # Remove extra whitespace
        text = re.sub(r' +', ' ', text)
        
        # Remove special characters while preserving basic punctuation
        text = re.sub(r'[^\w\s\.,!?;:\'"-]', '', text)
        
        # Normalize quotes and dashes
        text = text.replace('"', '"').replace('"', '"')
        text = text.replace('--', '—')
        
        return text.strip()

    def paginate_content(self, content, chars_per_line, lines_per_page):
        """Split content into pages"""
        pages = []
        paragraphs = content.split('\n\n')
        
        current_page = []
        current_lines = 0
        
        for paragraph in paragraphs:
            # Wrap paragraph text
            wrapped_lines = textwrap.fill(paragraph, width=chars_per_line).split('\n')
            
            # Check if we need to start a new page
            if current_lines + len(wrapped_lines) + 1 > lines_per_page:
                if current_page:
                    pages.append('\n'.join(current_page))
                current_page = wrapped_lines
                current_lines = len(wrapped_lines)
            else:
                if current_page:
                    current_page.append('')  # Add space between paragraphs
                    current_lines += 1
                current_page.extend(wrapped_lines)
                current_lines += len(wrapped_lines)
        
        # Add the last page if it has content
        if current_page:
            pages.append('\n'.join(current_page))
        
        return pages
    def load_book(self, book_name):
        """Load and paginate book content"""
        try:
            with open(os.path.join(self.books_dir, book_name), 'r', encoding='utf-8') as file:
                content = file.read()
                
            # Calculate characters per line and lines per page
            char_width = self.font_medium.getsize('x')[0]  # Average character width
            chars_per_line = (self.width - 60) // char_width  # Leave margins
            lines_per_page = (self.height - 80) // (self.font_medium.getsize('x')[1] + 5)  # Leave margins
            
            # Wrap text into lines
            wrapped_lines = []
            for paragraph in content.split('\n\n'):
                wrapped_lines.extend(textwrap.fill(paragraph, width=chars_per_line).split('\n'))
                wrapped_lines.append('')  # Add space between paragraphs
            
            # Split lines into pages
            self.book_content = []
            current_page = []
            
            for line in wrapped_lines:
                if len(current_page) >= lines_per_page:
                    self.book_content.append('\n'.join(current_page))
                    current_page = []
                current_page.append(line)
            
            if current_page:
                self.book_content.append('\n'.join(current_page))
            
            self.current_book = book_name
            self.current_page = 0
            self.in_book = True
            return True
            
        except Exception as e:
            print(f"Error loading book: {e}")
            return False

    def draw_book_selection(self):
        """Draw book selection screen"""
        image = Image.new('1', (self.width, self.height), 255)
        draw = ImageDraw.Draw(image)
        
        # Draw header
        draw.text((20, 20), "Available Books", font=self.font_large, fill=0)
        draw.line((10, 70, self.width-10, 70), fill=0)
        
        # Get available books
        books = self.get_available_books()
        if not books:
            draw.text((20, 100), "No books found in Books directory", font=self.font_medium, fill=0)
            draw.text((20, 140), "Place .txt or .md files in the Books folder", font=self.font_medium, fill=0)
        else:
            # Display books in a grid
            start_y = 100
            for i, book in enumerate(books):
                if i == self.selection_index:
                    # Draw selection box
                    text_width = self.font_medium.getsize(book)[0]
                    draw.rectangle((15, start_y-5, 25+text_width, start_y+35), outline=0)
                
                draw.text((20, start_y), book, font=self.font_medium, fill=0)
                start_y += 50
        
        # Draw navigation help
        draw.text((20, self.height-40), "Use 'left'/'right' to navigate, 'select' to choose", 
                 font=self.font_small, fill=0)
        
        return image

    def draw_book_page(self):
        """Draw current book page"""
        image = Image.new('1', (self.width, self.height), 255)
        draw = ImageDraw.Draw(image)
        
        # Draw header with book title
        title = self.current_book[:50] + "..." if len(self.current_book) > 50 else self.current_book
        draw.text((20, 20), title, font=self.font_medium, fill=0)
        draw.line((10, 60, self.width-10, 60), fill=0)
        
        # Draw page content
        if self.current_page < len(self.book_content):
            draw.text((30, 80), self.book_content[self.current_page], font=self.font_medium, fill=0)
        
        # Draw progress
        progress = f"Page {self.current_page + 1} of {len(self.book_content)}"
        progress_width = self.font_small.getsize(progress)[0]
        draw.text((self.width - progress_width - 20, self.height - 30), 
                 progress, font=self.font_small, fill=0)
        
        # Draw navigation help
        draw.text((20, self.height-30), "← Previous | Next → | Select to exit", 
                 font=self.font_small, fill=0)
        
        return image

    def handle_command(self, command):
        """Handle navigation commands"""
        if not self.in_book:
            # Book selection mode
            books = self.get_available_books()
            if command == 'right' and self.selection_index < len(books) - 1:
                self.selection_index += 1
            elif command == 'left' and self.selection_index > 0:
                self.selection_index -= 1
            elif command == 'select' and books:
                self.load_book(books[self.selection_index])
        else:
            # Reading mode
            if command == 'right' and self.current_page < len(self.book_content) - 1:
                self.current_page += 1
            elif command == 'left' and self.current_page > 0:
                self.current_page -= 1
            elif command == 'select':
                self.in_book = False
                self.current_book = None
                self.book_content = []
                self.current_page = 0

    def update_display(self):
        """Update the e-paper display"""
        try:
            print(self.epd, '<<<<readerclass')
            self.epd.init()
            print('after intit')
            if self.in_book:
                image = self.draw_book_page()
            else:
                image = self.draw_book_selection()
            self.epd.display(self.epd.getbuffer(image))
        except Exception as e:
            print(f"Error updating display: {e}")