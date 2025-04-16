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
    try:
        original_size = driver.execute_script("return [document.body.scrollWidth, document.body.scrollHeight];")
        driver.set_window_size(original_size[0], original_size[1])
        time.sleep(1)
        driver.find_element(By.TAG_NAME, "body").screenshot(file_path)
    except Exception as e:
        print(f"⚠️ Failed to capture full page screenshot: {e}")

def capture_website(url):
    session_id = str(uuid.uuid4())
    output_dir = f"screenshots_{session_id}"
    os.makedirs(output_dir, exist_ok=True)

    options = webdriver.ChromeOptions()
    options.binary_location = os.getenv("CHROME_BIN", "/usr/bin/google-chrome")
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

    driver.get(url)
    time.sleep(3)

    # DEBUG: Save initial homepage screenshot
    driver.save_screenshot("homepage_debug.png")
    print("📸 Saved homepage screenshot for inspection.")

    menu_items = driver.find_elements(By.CSS_SELECTOR, "header nav a")
    print("🔗 Menu links found:")
    links = []
    for item in menu_items:
        href = item.get_attribute("href")
        print(" -", href)
        if href and href.startswith(url) and href not in links:
            links.append(href)

    if not links:
        print("⚠️ No menu links found! Trying fallback selector for all page links.")
        all_links = driver.find_elements(By.CSS_SELECTOR, "a[href^='http']")
        for item in all_links:
            href = item.get_attribute("href")
            print(" -", href)
            if href and href.startswith(url) and href not in links:
                links.append(href)

    screenshot_paths = []
    for i, link in enumerate(links):
        try:
            driver.get(link)
            time.sleep(2)
            path = os.path.join(output_dir, f"page_{i+1}.png")
            fullpage_screenshot(driver, path)
            screenshot_paths.append(path)
        except Exception as e:
            print(f"❌ Failed to capture screenshot for {link}: {e}")

    driver.quit()

    if not screenshot_paths:
        raise Exception("No screenshots captured. Please check if the website structure is compatible.")

    output_pdf = f"{output_dir}.pdf"
    with open(output_pdf, "wb") as f:
    for img_path in screenshot_paths:
        try:
            with open(img_path, "rb") as img_file:
                f.write(img2pdf.convert(img_file))
        except Exception as e:
            print(f"❌ Skipping image {img_path} due to error: {e}")

    return output_pdf

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        url = request.form.get("website_url")
        if not url:
            return render_template("index.html", error="❗ Please enter a valid website URL.")
        try:
            pdf_path = capture_website(url)
            return send_file(pdf_path, as_attachment=True)
        except Exception as e:
            print(f"💥 Error: {e}")
            return render_template("index.html", error=f"❗ {str(e)}")
    return render_template("index.html")

if __name__ == "__main__":
    app.run(debug=True)
