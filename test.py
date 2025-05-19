import requests

TOKEN = "lip_fbGgHXuGvdCE3i3ESA4O"
username = "seojeong109"

headers = {
    "Authorization": f"Bearer {TOKEN}"
}

resp = requests.get(f"https://lichess.org/api/user/{username}", headers=headers)
print("Status code:", resp.status_code)
print("Response body:", resp.text)