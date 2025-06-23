import cv2
import numpy as np
from PIL import Image
from pdf2image import convert_from_path

# ==== Contrast Enhancement Function ====
def increase_contrast(img):
    lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)
    l, a, b = cv2.split(lab)
    clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
    cl = clahe.apply(l)
    merged = cv2.merge((cl, a, b))
    return cv2.cvtColor(merged, cv2.COLOR_LAB2BGR)

# ==== Preprocessing Function ====
def preprocess_image(pil_img):
    img = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)
    img = increase_contrast(img)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    denoised = cv2.fastNlMeansDenoising(gray, h=30)
    blurred = cv2.GaussianBlur(denoised, (5, 5), 0)
    binary = cv2.adaptiveThreshold(
        blurred, 255,
        cv2.ADAPTIVE_THRESH_MEAN_C,
        cv2.THRESH_BINARY,
        15, 10
    )
    return binary

# ==== Main Function ====
def main():
    pdf_path = r"C:\Users\Syamimi Suhaimi\Documents\VSCode\static\uploads\Assignment_Handwritten_5.pdf"
    poppler_path = r"C:\poppler\poppler-24.08.0\Library\bin"  # Replace with your Poppler bin path

    # Convert PDF to list of images (PIL format)
    pages = convert_from_path(pdf_path, dpi=300, poppler_path=poppler_path)

    # Process each page
    for i, page in enumerate(pages):
        print(f"Processing page {i + 1}...")
        processed_img = preprocess_image(page)

        # Convert original page to OpenCV format
        original_cv = cv2.cvtColor(np.array(page), cv2.COLOR_RGB2BGR)

        # Resize images for display
        display_width = 800
        h1, w1 = original_cv.shape[:2]
        h2, w2 = processed_img.shape[:2]
        scale1 = display_width / w1
        scale2 = display_width / w2
        original_resized = cv2.resize(original_cv, (int(w1 * scale1), int(h1 * scale1)))
        processed_resized = cv2.resize(processed_img, (int(w2 * scale2), int(h2 * scale2)))

        # Show images
        cv2.imshow(f"Original Page {i + 1}", original_resized)
        cv2.imshow(f"Processed Page {i + 1}", processed_resized)

        cv2.waitKey(0)
        cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
