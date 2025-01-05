import requests
import json
import os
import time

if not os.path.exists("token.txt"):
    print("Error: 'token.txt' not found. Please create this file and add your User Token. Refer to: https://youtu.be/b1SY4zTNnAE.")
    exit()
with open("token.txt", "r") as f:
    USER_TOKEN = f.read().strip()

if not os.path.exists("server.txt"):
    print("Error: 'server.txt' not found. Please create this file and add your Server ID. Refer to: https://youtu.be/NLWtSHWKbAI.")
    exit()
with open("server.txt", "r") as f:
    SERVER_ID = f.read().strip()

HEADERS = {
    "Authorization": USER_TOKEN,
    "Content-Type": "application/json"
}

EXCLUDED_CHANNELS = [
    "excluded-channel-beta",
    ""
]

TEMP_FILE = "server_backup_temp.json"

def save_temp_data(data):
    with open(TEMP_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def load_temp_data():
    if os.path.exists(TEMP_FILE):
        with open(TEMP_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def get_channels(server_id):
    url = f"https://discord.com/api/v9/guilds/{server_id}/channels"
    response = requests.get(url, headers=HEADERS)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error: Failed to fetch channels. Status Code: {response.status_code}. Response: {response.text}")
        return []

def get_messages(channel_id, last_message_id=None):
    url = f"https://discord.com/api/v9/channels/{channel_id}/messages"
    params = {"limit": 100}
    if last_message_id:
        params["before"] = last_message_id
    messages = []
    while True:
        response = requests.get(url, headers=HEADERS, params=params)
        if response.status_code == 200:
            data = response.json()
            if not data:
                break
            messages.extend(data)
            params["before"] = data[-1]["id"]
            time.sleep(1)
        else:
            print(f"Error: Failed to fetch messages from channel {channel_id}. Status Code: {response.status_code}. Response: {response.text}")
            break
    return messages

def scrape_server(server_id):
    channels = get_channels(server_id)
    server_data = load_temp_data()

    for channel in channels:
        if channel["name"] in EXCLUDED_CHANNELS or str(channel["id"]) in EXCLUDED_CHANNELS:
            continue

        if channel["type"] == 0:
            if channel["name"] not in server_data:
                server_data[channel["name"]] = []

            last_message_id = None
            if server_data[channel["name"]]:
                last_message_id = server_data[channel["name"]][-1]["id"]

            messages = get_messages(channel["id"], last_message_id)
            server_data[channel["name"]].extend([
                {
                    "id": msg["id"],
                    "author": msg["author"]["username"],
                    "content": msg["content"],
                    "timestamp": msg["timestamp"]
                }
                for msg in messages
            ])

            save_temp_data(server_data)

    return server_data

if __name__ == "__main__":
    print("Starting the scraping process...")
    data = scrape_server(SERVER_ID)
    with open("server.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
    print("All messages have been saved in 'server.json'.")

    if os.path.exists(TEMP_FILE):
        os.remove(TEMP_FILE)
