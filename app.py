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
        # Use full height for the page (still controlled)
        total_height = driver.execute_script("return document.body.scrollHeight")
        driver.set_window_size(1280, min(total_height, 5000))  # cap height if needed
        time.sleep(1)
        driver.save_screenshot(file_path)
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

    try:
        driver.save_screenshot("homepage_debug.jpg")
        print("📸 Saved homepage screenshot.")
    except Exception as e:
        print("⚠️ Failed to save homepage screenshot:", e)

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
            path = os.path.join(output_dir, f"page_{i+1}.jpg")
            fullpage_screenshot(driver, path)
            screenshot_paths.append(path)
        except Exception as e:
            print(f"❌ Failed to capture {link}: {e}")

    driver.quit()

    if not screenshot_paths:
        raise Exception("No screenshots captured. Please verify the website layout or URL.")

    print(f"🧾 Converting {len(screenshot_paths)} JPEGs into PDF...")

    output_pdf = f"{output_dir}.pdf"
    with open(output_pdf, "wb") as f:
        for img_path in screenshot_paths:
            try:
                with open(img_path, "rb") as img_file:
                    f.write(img2pdf.convert(img_file))
            except Exception as e:
                print(f"❌ Failed converting {img_path}: {e}")

    print("✅ PDF generation complete.")
    return output_pdf

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        url = request.form.get("website_url")
        if not url:
            return render_template("index.html", error="❗ Please enter a website URL.")
        try:
            pdf_path = capture_website(url)
            return send_file(pdf_path, as_attachment=True)
        except Exception as e:
            print(f"💥 Error: {e}")
            return render_template("index.html", error=f"❗ {str(e)}")
    return render_template("index.html")

if __name__ == "__main__":
    app.run(debug=True)
