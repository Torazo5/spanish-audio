# Importing required classes
from pypdf import PdfReader

# Creating a PDF reader object
pdf_path = './Booklet Ab 11  Unit 1 2024.pdf'  # Replace with your PDF file path
reader = PdfReader(pdf_path)

# Printing the number of pages in the PDF file
print(f'The PDF has {len(reader.pages)} pages.')

# Iterating through each page to extract and print the text
for page_number in range(len(reader.pages)):
    page = reader.pages[page_number]
    text = page.extract_text()  # Extracting text from the page
    print(f'--- Page {page_number + 1} ---')
    print(text)
    print()  # Print a newline for better readability
