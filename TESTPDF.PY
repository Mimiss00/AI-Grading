from pdf2image import convert_from_path

pdf_path = r"C:\Users\Syamimi Suhaimi\VSCode\templates\C++ assignment\C++ Handwritten_4.pdf"
poppler_path = r"C:\poppler\poppler-24.08.0\Library\bin"  # ← update this

pages = convert_from_path(pdf_path, dpi=300, poppler_path=poppler_path)
print("✅ Pages loaded:", len(pages))
