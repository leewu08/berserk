from flask import Flask, request, render_template
import requests
import json
import time

app = Flask(__name__)

TOKEN = "lip_yyCrSqcVpQYkD6oLP9A3"  # 본인의 Lichess API Token 사용

# Jinja2 필터: Unix timestamp → 날짜 문자열
def timestamp_to_date(timestamp):
    return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(timestamp / 1000))
app.jinja_env.filters['timestamp_to_date'] = timestamp_to_date

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/player", methods=["POST"])
def player():
    username = request.form["username"]
    headers = {"Authorization": f"Bearer {TOKEN}"}

    # 유저 정보 확인
    user_resp = requests.get(f"https://lichess.org/api/user/{username}", headers=headers)
    if user_resp.status_code != 200:
        return f"사용자 '{username}' 정보를 불러올 수 없습니다."

    user = user_resp.json()

    # 최근 게임 NDJSON 가져오기
    games_resp = requests.get(
    f"https://lichess.org/api/games/user/{username}",
    headers={
        "Authorization": f"Bearer {TOKEN}",
        "Accept": "application/x-ndjson"
    },
    params={"max": 20},
    stream=True
)

    games = []

    for line in games_resp.iter_lines():
        if not line:
            continue
        try:
            game = json.loads(line.decode('utf-8'))
        except json.JSONDecodeError:
            continue

        # 내 색상 및 상대 정보
        white_user = game["players"].get("white", {}).get("user", {}).get("name", "")
        black_user = game["players"].get("black", {}).get("user", {}).get("name", "")
        winner = game.get("winner")  # "white", "black", or None

        if username.lower() == white_user.lower():
            color = "White"
            opponent = black_user
            result = "Win" if winner == "white" else "Loss" if winner == "black" else "Draw"
        elif username.lower() == black_user.lower():
            color = "Black"
            opponent = white_user
            result = "Win" if winner == "black" else "Loss" if winner == "white" else "Draw"
        else:
            continue  # 유저가 포함되지 않은 게임은 제외

        games.append({
            "date": game.get("createdAt"),
            "color": color,
            "opponent": opponent,
            "result": result
        })

    return render_template("player.html", user=user, games=games)

if __name__ == "__main__":
    app.run(debug=True)
