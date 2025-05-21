from flask import Flask, request, render_template, jsonify
from flask_cors import CORS
import requests
import json
import time

app = Flask(__name__)
CORS(app)  # CORS 활성화

TOKEN = "lip_gF4TfbXijclL9xmlktO1"

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

    user_url = f"https://lichess.org/api/user/{username}"
    user_resp = requests.get(user_url, headers={"Authorization": f"Bearer {TOKEN}"})
    if user_resp.status_code != 200:
        return f"사용자 '{username}' 정보를 불러올 수 없습니다."
    user = user_resp.json()

    perfs = user.get("perfs", {})
    sorted_perfs = sorted(
        [(mode, data) for mode, data in perfs.items() if data.get("games", 0) > 0],
        key=lambda item: item[1].get("games", 0),
        reverse=True
    )

    try:
        games = fetch_analysis_public(username, max_games)
    except Exception as e:
        return f"게임 데이터를 불러오는 중 오류가 발생했습니다: {str(e)}"

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

    return render_template(
        "player.html",
        user=user,
        games=games,
        win_rate=win_rate,
        total=total,
        max_games=max_games,
        sorted_perfs=sorted_perfs
    )

@app.route("/api/games/<username>")
def api_games(username):
    end_type = request.args.get("endType", "").lower()
    max_games = int(request.args.get("max_games", 20))

    try:
        games = fetch_analysis_public(username, max_games)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

    if end_type and end_type != "all":
        games = [g for g in games if g.get("status", "").lower() == end_type]

    result = []
    for game in games:
        result.append({
            "id": game.get("id"),
            "createdAt": game.get("createdAt"),
            "status": game.get("status"),
            "winner": game.get("winner"),
            "players": game.get("players"),
            "opening": game.get("opening", {}).get("name", "알 수 없음"),
            "moves": game.get("moves"),
            "is_analysed": game.get("is_analysed"),
        })

    return jsonify(result)

if __name__ == "__main__":
    app.run(debug=True, port=5002)
