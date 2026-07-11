import time
import threading
from flask import Flask, render_template_string
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

app = Flask(__name__)

# --- CONFIGURATION ---
VIDEO_ID = "dcCyEXj1MCc"
# We use the main watch page instead of embed to allow JavaScript access to the video player
YOUTUBE_URL = f"https://www.youtube.com/watch?v={VIDEO_ID}"

# Shared data between the background browser and the web dashboard
video_state = {
    "status": "Initializing Browser...",
    "loop_count": 0,
    "current_time": 0.0
}

def run_browser():
    """Runs the headless Chrome browser in the background."""
    global video_state
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--autoplay-policy=no-user-gesture-required")
    chrome_options.add_argument("--mute-audio")

    driver = webdriver.Chrome(options=chrome_options)
    
    try:
        driver.get(YOUTUBE_URL)
        video_state["status"] = "Loading video page..."
        time.sleep(5) # Give YouTube time to load the DOM
        
        # Inject JavaScript to force the HTML5 player to mute, loop, and play
        setup_script = """
            var video = document.querySelector('video');
            if(video) {
                video.muted = true;
                video.loop = true;
                video.play();
                return true;
            }
            return false;
        """
        success = driver.execute_script(setup_script)
        
        if success:
            video_state["status"] = "Streaming"
        else:
            video_state["status"] = "Error: Could not find video player"
        
        last_time = 0.0
        
        # Infinite loop to monitor the video's progress
        while True:
            time.sleep(1)
            try:
                # Ask the browser for the video's current timestamp
                current_time = driver.execute_script("return document.querySelector('video').currentTime;")
                
                if current_time is not None:
                    video_state["current_time"] = round(current_time, 1)
                    
                    # If the time drops significantly, it means the video restarted (looped)
                    if current_time < last_time - 1:
                        video_state["loop_count"] += 1
                        
                    last_time = current_time
                    video_state["status"] = "Streaming"
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
        <title>Server Stream Tracker</title>
        <meta http-equiv="refresh" content="2">
        <style>
            body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; text-align: center; margin-top: 10vh; background-color: #0f0f0f; color: #f1f1f1; }
            .card { background: #212121; padding: 40px; border-radius: 15px; display: inline-block; box-shadow: 0 10px 20px rgba(0,0,0,0.5); border: 1px solid #3d3d3d; min-width: 300px; }
            h2 { margin-top: 0; color: #fff; font-size: 24px;}
            .status { color: #00e676; font-weight: bold; }
            .count-label { font-size: 14px; color: #aaa; text-transform: uppercase; letter-spacing: 1px; margin-top: 25px; }
            .count { font-size: 72px; margin: 0; color: #3ea6ff; font-weight: bold; }
            .time { color: #aaa; font-size: 14px; margin-top: 20px; }
        </style>
    </head>
    <body>
        <div class="card">
            <h2>Live Server Node</h2>
            <p>System Status: <span class="status">{{ state['status'] }}</span></p>
            
            <p class="count-label">Successful Loops</p>
            <div class="count">{{ state['loop_count'] }}</div>
            
            <p class="time">Current Video Timestamp: <strong>{{ state['current_time'] }}s</strong></p>
        </div>
    </body>
    </html>
    """
    return render_template_string(html_template, state=video_state)

if __name__ == "__main__":
    # 1. Start the headless browser on a separate thread so it doesn't block the web server
    browser_thread = threading.Thread(target=run_browser, daemon=True)
    browser_thread.start()
    
    # 2. Start the Flask server (Port 10000 is Render's default expected port)
    app.run(host="0.0.0.0", port=10000)
