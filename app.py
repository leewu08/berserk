from flask import Flask, request, render_template
import requests
import json
import time

app = Flask(__name__)

TOKEN = "lip_fbGgHXuGvdCE3i3ESA4O"

# Jinja2 필터 등록: timestamp를 읽기 쉬운 날짜로
def timestamp_to_date(timestamp):
    return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(timestamp / 1000))
app.jinja_env.filters['timestamp_to_date'] = timestamp_to_date

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/player", methods=["POST"])
def player():
    username = request.form.get("username")
    max_games = int(request.form.get("max_games", 20))  # 기본 20

    if not username:
        return "사용자명을 입력해주세요."

    headers = {
        "Authorization": f"Bearer {TOKEN}",
        "Accept": "application/x-ndjson"  # 이 헤더 추가
    }

    # 사용자 정보 요청
    user_url = f"https://lichess.org/api/user/{username}"
    user_resp = requests.get(user_url, headers=headers)
    if user_resp.status_code != 200:
        return f"사용자 '{username}' 정보를 불러올 수 없습니다."
    user = user_resp.json()

    # 게임 정보 요청 (NDJSON)
    games_url = f"https://lichess.org/api/games/user/{username}"
    params = {"max": max_games, "analysed": "true"}
    games_resp = requests.get(games_url, headers=headers, params=params, stream=True)

    games = []
    wins = 0
    total = 0

    for line in games_resp.iter_lines():
        if not line:
            continue
        try:
            game = json.loads(line.decode('utf-8'))
        except json.JSONDecodeError:
            continue

        games.append(game)
        total += 1

        # 승리 판별
        winner = game.get("winner")
        if not winner:
            continue

        white = game["players"].get("white", {}).get("user", {}).get("name", "").lower()
        black = game["players"].get("black", {}).get("user", {}).get("name", "").lower()
        uname = username.lower()

        if (winner == "white" and white == uname) or (winner == "black" and black == uname):
            wins += 1

    win_rate = round((wins / total) * 100, 2) if total else 0

    return render_template("player.html", user=user, games=games, win_rate=win_rate, total=total, max_games=max_games)

if __name__ == "__main__":
    app.run(debug=True)
