import os
from PIL import Image, ImageDraw, ImageFont
import textwrap
import markdown
import epub
import PyPDF2
import re
import gc
import os
from PIL import Image, ImageDraw, ImageFont
import textwrap
import codecs
import html2text
import io
import ebooklib
from ebooklib import epub
from PyPDF2 import PdfReader
import html


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
        self.html_converter.body_width = 0  # 
        
        # Create Books directory if it doesn't exist
        if not os.path.exists(self.books_dir):
            os.makedirs(self.books_dir)


    def get_available_books(self):
        """Get list of supported book files in Books directory"""
        if not os.path.exists(self.books_dir):
            return []
        return [f for f in os.listdir(self.books_dir) 
                if f.lower().endswith(('.txt', '.html', '.htm', '.epub', '.pdf'))]

    def read_book_content(self, file_path):
        """Read content from different file formats"""
        extension = os.path.splitext(file_path)[1].lower()
        
        try:
            if extension in ['.txt']:
                # Try multiple encodings for text files
                encodings = ['utf-8', 'latin-1', 'ascii', 'iso-8859-1']
                for encoding in encodings:
                    try:
                        with codecs.open(file_path, 'r', encoding=encoding) as file:
                            return file.read()
                    except UnicodeDecodeError:
                        continue
                raise ValueError(f"Could not decode file with any supported encoding")

            elif extension in ['.html', '.htm']:
                with open(file_path, 'r', encoding='utf-8') as file:
                    html_content = file.read()
                    return self.html_converter.handle(html_content)

            elif extension == '.epub':
                book = epub.read_epub(file_path)
                content_parts = []
                
                # Get all items that are documents
                for item in book.get_items():
                    if item.get_type() == ebooklib.ITEM_DOCUMENT:
                        try:
                            # Get content as bytes and decode
                            html_content = item.get_content().decode('utf-8', errors='ignore')
                            # Strip HTML tags and convert entities
                            text_content = html.unescape(self.html_converter.handle(html_content))
                            if text_content.strip():  # Only add non-empty content
                                content_parts.append(text_content)
                        except Exception as e:
                            print(f"Error processing EPUB section: {e}")
                            continue

                return '\n\n'.join(content_parts)

            elif extension == '.pdf':
                content_parts = []
                try:
                    reader = PdfReader(file_path)
                    for page in reader.pages:
                        try:
                            text = page.extract_text()
                            if text.strip():  # Only add non-empty pages
                                content_parts.append(text)
                        except Exception as e:
                            print(f"Error extracting PDF page: {e}")
                            continue
                    
                    return '\n\n'.join(content_parts)
                except Exception as e:
                    print(f"Error reading PDF file: {e}")
                    return None

            else:
                raise ValueError(f"Unsupported file format: {extension}")

        except Exception as e:
            print(f"Error reading file {file_path}: {e}")
            return None

    def clean_text(self, text):
        """Clean up text content"""
        if not text:
            return ""
        
        # Replace Windows-style line endings
        text = text.replace('\r\n', '\n')
        text = text.replace('\r', '\n')
        
        # Handle PDF-specific issues
        text = text.replace('•', '*')  # Replace bullets with asterisks
        
        # Remove form feeds and other special characters
        text = text.replace('\f', '\n')
        text = text.replace('\v', '\n')
        
        # Replace multiple spaces
        text = ' '.join(text.split())
        
        # Replace multiple newlines with double newline
        while '\n\n\n' in text:
            text = text.replace('\n\n\n', '\n\n')
        
        # Handle EPUB-specific issues
        text = text.replace('* * *', '\n\n')  # Common section break in epubs
        
        # Remove any remaining HTML entities
        text = html.unescape(text)
        
        return text.strip()



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
            file_path = os.path.join(self.books_dir, book_name)
            content = self.read_book_content(file_path)
            if content is None:
                return False

            # Calculate layout parameters
            char_width = self.font_medium.getsize('x')[0]
            chars_per_line = (self.width - 60) // char_width  # 30px margins on each side

            # Adjusted vertical space calculation
            top_margin = 80  # Space for header
            bottom_margin = 35  # Increased from 30
            line_height = self.font_medium.getsize('x')[1] + 5  # Height of line plus spacing
            lines_per_page = (self.height - top_margin - bottom_margin) // line_height

            # Split content into pages
            self.book_content = []
            current_page = []
            current_lines = 0

            # Split content into paragraphs
            paragraphs = content.split('\n\n')

            for paragraph in paragraphs:
                # Wrap the paragraph text
                wrapped_lines = textwrap.fill(paragraph.strip(), width=chars_per_line).split('\n')

                # Check if we need to start a new page
                if current_lines + len(wrapped_lines) + 1 > lines_per_page:
                    if current_page:
                        self.book_content.append('\n'.join(current_page))
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
            self.epd.init()
            if self.in_book:
                image = self.draw_book_page()
            else:
                image = self.draw_book_selection()
            self.epd.display(self.epd.getbuffer(image))
        except Exception as e:
            print(f"Error updating display: {e}")

    def cleanup(self):
        """Clean up resources when exiting reader mode"""
        self.current_book = None
        self.book_content = []
        self.current_page = 0
        self.in_book = False
        gc.collect()  