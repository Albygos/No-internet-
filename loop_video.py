import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

# --- CONFIGURATION ---
# Replace with the characters after 'v=' in your YouTube link
VIDEO_ID = "dQw4w9WgXcQ" 

# We use the embed URL with autoplay, loop, and playlist parameters forced on
YOUTUBE_URL = f"https://www.youtube.com/embed/{VIDEO_ID}?autoplay=1&loop=1&playlist={VIDEO_ID}"

def run_headless_player():
    # Set up headless Chrome options for a server environment
    chrome_options = Options()
    chrome_options.add_argument("--headless") # Runs without a visual UI (the "frame")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox") # Crucial for Linux servers like Render
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--autoplay-policy=no-user-gesture-required") # Forces autoplay
    chrome_options.add_argument("--mute-audio") # Often required by browsers to allow autoplay

    print(f"Starting server-side streaming for video ID: {VIDEO_ID}")

    # Initialize the Chrome driver
    driver = webdriver.Chrome(options=chrome_options)

    try:
        # Load the YouTube video
        driver.get(YOUTUBE_URL)
        print("Video successfully loaded. Now streaming and consuming server bandwidth...")
        
        # Keep the script alive infinitely to maintain the stream
        while True:
            # Pings the console every 10 minutes so Render logs show it's active
            time.sleep(600) 
            print("Still looping the video in the background...")
            
    except KeyboardInterrupt:
        print("Manual interruption received. Stopping the stream.")
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        # Clean up resources if the script crashes
        driver.quit()
        print("Browser closed.")

if __name__ == "__main__":
    run_headless_player()
