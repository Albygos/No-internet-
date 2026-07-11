import time
import threading
from flask import Flask, render_template_string
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

app = Flask(__name__)

# --- CONFIGURATION ---
VIDEO_ID = "dcCyEXj1MCc"
NUM_TABS = 50  # WARNING: 50 tabs requires ~5-10GB of server RAM! Reduce to 3 on a free tier.
YOUTUBE_URL = f"https://www.youtube.com/watch?v={VIDEO_ID}"

# Shared data between the background browser and the web dashboard
video_state = {
    "status": "Initializing Browser...",
    "total_loop_count": 0,
    "active_tabs": 0
}

def run_browser():
    """Runs the headless Chrome browser and opens multiple tabs."""
    global video_state
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--autoplay-policy=no-user-gesture-required")
    chrome_options.add_argument("--mute-audio")
    
    # Extra flags to save as much memory as possible
    chrome_options.add_argument("--disable-extensions")
    chrome_options.add_argument("--disable-software-rasterizer")

    driver = webdriver.Chrome(options=chrome_options)
    
    try:
        video_state["status"] = f"Opening {NUM_TABS} tabs..."
        
        # Loop to open the required number of tabs
        for i in range(NUM_TABS):
            if i > 0:
                # Open a new tab and switch to it
                driver.switch_to.new_window('tab')
            
            driver.get(YOUTUBE_URL)
            
            # Wait 3 seconds between opening tabs so we don't crash the server's CPU
            time.sleep(3) 
            
            # Inject JavaScript to force the player to mute, loop, and play
            setup_script = """
                var video = document.querySelector('video');
                if(video) {
                    video.muted = true;
                    video.loop = true;
                    video.play();
                }
            """
            driver.execute_script(setup_script)
            video_state["active_tabs"] = i + 1
            
        video_state["status"] = "All tabs streaming!"
        
        # Switch back to the very first tab to monitor the loop progress
        driver.switch_to.window(driver.window_handles[0])
        last_time = 0.0
        
        # Infinite loop to keep the browser alive and track views
        while True:
            time.sleep(2)
            try:
                # Check the time of the first tab
                current_time = driver.execute_script("return document.querySelector('video').currentTime;")
                
                if current_time is not None:
                    # If the video restarts, add the number of active tabs to the total loop count
                    if current_time < last_time - 1:
                        video_state["total_loop_count"] += video_state["active_tabs"]
                        
                    last_time = current_time
                    video_state["status"] = "Streaming successfully"
            except Exception:
                video_state["status"] = "Buffering / Waiting..."
                
    except Exception as e:
        video_state["status"] = f"Crashed: {str(e)}"
    finally:
        driver.quit()

@app.route('/')
def dashboard():
    """Serves the live tracking dashboard."""
    html_template = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Multi-Tab Stream Tracker</title>
        <meta http-equiv="refresh" content="3">
        <style>
            body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; text-align: center; margin-top: 10vh; background-color: #0f0f0f; color: #f1f1f1; }
            .card { background: #212121; padding: 40px; border-radius: 15px; display: inline-block; box-shadow: 0 10px 20px rgba(0,0,0,0.5); border: 1px solid #3d3d3d; min-width: 350px; }
            h2 { margin-top: 0; color: #fff; font-size: 24px;}
            .status { color: #00e676; font-weight: bold; }
            .tabs { color: #ffeb3b; font-size: 18px; margin: 15px 0; }
            .count-label { font-size: 14px; color: #aaa; text-transform: uppercase; letter-spacing: 1px; margin-top: 25px; }
            .count { font-size: 72px; margin: 0; color: #3ea6ff; font-weight: bold; }
        </style>
    </head>
    <body>
        <div class="card">
            <h2>Multi-Tab Server Node</h2>
            <p>System Status: <span class="status">{{ state['status'] }}</span></p>
            
            <div class="tabs">Active Streaming Tabs: <strong>{{ state['active_tabs'] }} / 50</strong></div>
            
            <p class="count-label">Total Video Loops</p>
            <div class="count">{{ state['total_loop_count'] }}</div>
        </div>
    </body>
    </html>
    """
    return render_template_string(html_template, state=video_state)

if __name__ == "__main__":
    # 1. Start the headless browser on a background thread
    browser_thread = threading.Thread(target=run_browser, daemon=True)
    browser_thread.start()
    
    # 2. Start the Flask server
    app.run(host="0.0.0.0", port=10000)
