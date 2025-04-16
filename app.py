
from flask import Flask, render_template, request, send_file
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import time
import os
import img2pdf
import uuid

app = Flask(__name__)

def fullpage_screenshot(driver, file_path):
    original_size = driver.execute_script("return [document.body.scrollWidth, document.body.scrollHeight];")
    driver.set_window_size(original_size[0], original_size[1])
    time.sleep(1)
    driver.find_element(By.TAG_NAME, "body").screenshot(file_path)

def capture_website(url):
    session_id = str(uuid.uuid4())
    output_dir = f"screenshots_{session_id}"
    os.makedirs(output_dir, exist_ok=True)

    options = webdriver.ChromeOptions()
    options.binary_location = os.getenv("CHROME_BIN", "/usr/bin/google-chrome")
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

    driver.get(url)
    time.sleep(3)

    # Try capturing the homepage visually
    driver.save_screenshot("homepage_debug.png")
    print("✔️ Saved homepage screenshot as homepage_debug.png")

    menu_items = driver.find_elements(By.CSS_SELECTOR, "header nav a")
    print("🔗 Menu links discovered:")
    links = []
    for item in menu_items:
        href = item.get_attribute("href")
        print(" -", href)
        if href and href.startswith(url) and href not in links:
            links.append(href)


    screenshot_paths = []
    for i, link in enumerate(links):
        driver.get(link)
        time.sleep(2)
        path = os.path.join(output_dir, f"page_{i+1}.png")
        fullpage_screenshot(driver, path)
        screenshot_paths.append(path)

    driver.quit()

    output_pdf = f"{output_dir}.pdf"
    with open(output_pdf, "wb") as f:
        if not screenshot_paths:
    raise Exception("No screenshots were captured. Unable to generate PDF.")

with open(output_pdf, "wb") as f:
    f.write(img2pdf.convert(screenshot_paths))

    return output_pdf

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        url = request.form.get("website_url")
        if not url:
            return render_template("index.html", error="Please enter a valid website URL.")
        try:
            pdf_path = capture_website(url)
            return send_file(pdf_path, as_attachment=True)
        except Exception as e:
            return render_template("index.html", error=f"Error: {str(e)}")
    return render_template("index.html")

if __name__ == "__main__":
    app.run(debug=True)
