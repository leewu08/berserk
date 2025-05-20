from flask import Flask, request, render_template
import requests
import json
import time

app = Flask(__name__)

TOKEN = "lip_nW7Hl5a6Qras9d6EeeGB"

def timestamp_to_date(timestamp):
    return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(timestamp / 1000))
app.jinja_env.filters['timestamp_to_date'] = timestamp_to_date

def fetch_analysis_public(username, max_games=20):
    url = f"https://lichess.org/api/games/user/{username}"
    params = {
        "max": max_games,
        "evals": "true",
        "opening": "true"
    }
    headers = {
        "Accept": "application/x-ndjson"
    }

    response = requests.get(url, params=params, headers=headers, stream=True)
    response.raise_for_status()

    games = []
    for line in response.iter_lines(decode_unicode=True):
        if not line.strip():
            continue
        try:
            game = json.loads(line)
        except json.JSONDecodeError:
            continue
        
        is_analysed = bool(game.get("analysis")) or game.get("isAnalysed", False)
        game["is_analysed"] = is_analysed
        games.append(game)
    return games

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/player", methods=["POST"])
def player():
    username = request.form.get("username")
    max_games = int(request.form.get("max_games", 20))

    if not username:
        return "사용자명을 입력해주세요."

    # 1) 사용자 정보는 토큰 인증 필요
    user_url = f"https://lichess.org/api/user/{username}"
    user_resp = requests.get(user_url, headers={"Authorization": f"Bearer {TOKEN}"})
    if user_resp.status_code != 200:
        return f"사용자 '{username}' 정보를 불러올 수 없습니다."
    user = user_resp.json()

    # 2) 게임 리스트는 공개 API로 분석 데이터 가져오기 (토큰 없이)
    try:
        games = fetch_analysis_public(username, max_games)
    except Exception as e:
        return f"게임 데이터를 불러오는 중 오류가 발생했습니다: {str(e)}"

    # 승률 계산
    wins = 0
    total = 0
    uname = username.lower()
    for game in games:
        total += 1
        winner = game.get("winner")
        if not winner:
            continue
        white = game["players"].get("white", {}).get("user", {}).get("name", "").lower()
        black = game["players"].get("black", {}).get("user", {}).get("name", "").lower()

        if (winner == "white" and white == uname) or (winner == "black" and black == uname):
            wins += 1

    win_rate = round((wins / total) * 100, 2) if total else 0

    return render_template("player.html", user=user, games=games, win_rate=win_rate, total=total, max_games=max_games)

if __name__ == "__main__":
    app.run(debug=True, port=5002)
