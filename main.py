import requests
import time
import os
from dotenv import load_dotenv

# --- MY SETUP ---
# I use .env to keep my API keys safe and off GitHub
load_dotenv()
TOKEN = os.getenv("TELEGRAM_TOKEN")
BASE_URL = f"https://api.telegram.org/bot{TOKEN}"

# --- MY LOCAL REGION ---
# I set this box to cover Kitchener, Waterloo, and Cambridge
KWC_REGION = {
    "name": "KWC Region",
    "lat_min": 43.3,
    "lat_max": 43.6,
    "lon_min": -80.6,
    "lon_max": -80.2
}

def fetch_my_local_cameras(region_config):
    """
    I connect to the Ontario 511 API and filter for cameras in my box.
    """
    api_url = "https://511on.ca/api/v2/get/cameras"
    
    print(f"🔍 I am searching for cameras in {region_config['name']}...")
    
    try:
        response = requests.get(api_url)
        all_cams = response.json()
        
        # I only keep cameras that fall inside my Lat/Lon boundaries
        my_cams = [
            cam for cam in all_cams
            if region_config["lat_min"] <= cam.get('Latitude', 0) <= region_config["lat_max"]
            and region_config["lon_min"] <= cam.get('Longitude', 0) <= region_config["lon_max"]
        ]
        
        return sorted(my_cams, key=lambda x: x.get('Location', ''))
    
    except Exception as e:
        print(f"❌ I couldn't reach the API: {e}")
        return []

def run_my_bot():
    """
    I designed this loop to listen for commands and send back live images.
    """
    offset = 0
    print(f"✅ My VigneMap service is live! I'm ready for your 'map' command.")
    
    while True:
        try:
            # I check for new messages every 30 seconds
            poll_url = f"{BASE_URL}/getUpdates?offset={offset}&timeout=30"
            updates = requests.get(poll_url).json().get('result', [])
            
            for update in updates:
                offset = update['update_id'] + 1
                if 'message' not in update: continue
                
                chat_id = update['message']['chat']['id']
                user_text = update['message'].get('text', '').lower()

                if user_text == "map":
                    cams = fetch_my_local_cameras(KWC_REGION)
                    
                    header = f"📍 *{KWC_REGION['name']} Road Watch*\nI found these cameras. Pick a number:"
                    menu = "\n".join([f"{i} | {c.get('Location')}" for i, c in enumerate(cams[:25])])
                    
                    requests.post(f"{BASE_URL}/sendMessage", data={
                        "chat_id": chat_id, 
                        "text": f"{header}\n{menu}", 
                        "parse_mode": "Markdown"
                    })

                elif user_text.isdigit():
                    cams = fetch_my_local_cameras(KWC_REGION)
                    choice = int(user_text)
                    
                    if 0 <= choice < len(cams):
                        selected_cam = cams[choice]
                        image_url = selected_cam.get('Views', [{}])[0].get('Url')
                        
                        if image_url:
                            print(f"📸 I am sending the live image for: {selected_cam.get('Location')}")
                            img_bytes = requests.get(image_url).content
                            
                            requests.post(f"{BASE_URL}/sendPhoto", 
                                data={"chat_id": chat_id, "caption": f"✅ {selected_cam.get('Location')}"},
                                files={"photo": ('traffic.jpg', img_bytes)}
                            )
            
            time.sleep(1) 
            
        except KeyboardInterrupt:
            print("\n👋 I am shutting down the service. Drive safe!")
            break
        except Exception as e:
            print(f"🔄 I hit a connection blip: {e}. I'll retry in 10 seconds...")
            time.sleep(10)

if __name__ == "__main__":
    if not TOKEN:
        print("❌ I can't find the TELEGRAM_TOKEN. Please check your .env file!")
    else:
        run_my_bot()
