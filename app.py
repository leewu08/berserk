from flask import Flask, request, render_template, jsonify, session,redirect
import requests
import json
import time
from collections import defaultdict

app = Flask(__name__)
app.secret_key = 'dev-secret-key'
TOKEN = "lip_jdtYXFicH6O5yaA5FUnc"

def timestamp_to_date(timestamp):
    return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(timestamp / 1000))

app.jinja_env.filters['timestamp_to_date'] = timestamp_to_date

def fetch_analysis_public(username, max_games=20, since=None, until=None):
    url = f"https://lichess.org/api/games/user/{username}"
    params = {
        "max": max_games,
        "evals": "true",
        "opening": "true"
    }
    if since:
        params["since"] = since
    if until:
        params["until"] = until

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

def fetch_analysis_paginated(username, max_games=20, since=None, until=None):
    all_games = []
    max_per_request = 200  # Lichess API 최대 한도

    current_until = until

    while len(all_games) < max_games:
        remaining = max_games - len(all_games)
        fetch_count = min(max_per_request, remaining)

        games = fetch_analysis_public(username, max_games=fetch_count, since=since, until=current_until)
        if not games:
            break

        all_games.extend(games)

        oldest_game_time = games[-1].get('createdAt')
        if oldest_game_time is None:
            break

        # 중복 방지용으로 1 밀리초 빼기
        current_until = oldest_game_time - 1    

        # 요청한 수보다 적게 오면 더 이상 데이터 없음
        if len(games) < fetch_count:
            break

    return all_games[:max_games]

@app.route("/")
def index():
    
    username = request.form.get("username")
    session["username"] = username  # 세션 등록
    return render_template("index.html")

@app.route("/player", methods=["POST"])
def player():
    username = request.form.get("username")
    session['username'] = username
    max_games = int(request.form.get("max_games", 20))
    selected_color = request.form.get("color", "white").lower()  # 기본 흰색

    if not username:
        return "사용자명을 입력해주세요."

    # 사용자 정보 가져오기
    user_url = f"https://lichess.org/api/user/{username}"
    user_resp = requests.get(user_url, headers={"Authorization": f"Bearer {TOKEN}"})
    if user_resp.status_code != 200:
        return f"사용자 '{username}' 정보를 불러올 수 없습니다."
    user = user_resp.json()

    # 퍼포먼스 정렬 (게임 수 기준)
    perfs = user.get("perfs", {})
    sorted_perfs = sorted(
        [(mode, data) for mode, data in perfs.items() if data.get("games", 0) > 0],
        key=lambda item: item[1].get("games", 0),
        reverse=True
    )

    try:
        games = fetch_analysis_paginated(username, max_games)
    except Exception as e:
        return f"게임 데이터를 불러오는 중 오류가 발생했습니다: {str(e)}"

    uname = username.lower()
    wins = 0
    total = 0

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

    # 🔸 선택한 색상으로 플레이한 게임 수
    color_game_count = 0
    for game in games:
        player_name = game.get("players", {}).get(selected_color, {}).get("user", {}).get("name", "").lower()
        if player_name == uname:
            color_game_count += 1

    # 🔸 전체 색상별 플레이 게임 수 (white/black)
    color_counts = {"white": 0, "black": 0}
    for game in games:
        for color in ["white", "black"]:
            player = game.get("players", {}).get(color, {}).get("user", {}).get("name", "").lower()
            if player == uname:
                color_counts[color] += 1

    return render_template(
        "player.html",
        user=user,
        games=games,
        win_rate=win_rate,
        total=total,
        max_games=max_games,
        sorted_perfs=sorted_perfs,
        selected_color=selected_color,
        color_game_count=color_game_count,
        color_counts=color_counts
    )


@app.route("/api/games/<username>")
def api_games(username):
    end_type = request.args.get("endType", "").lower()
    color = request.args.get("color", "").lower()
    max_games = int(request.args.get("max_games", 20))
    since = request.args.get("since")
    until = request.args.get("until")

    since = int(since) if since else None
    until = int(until) if until else None

    try:
        raw_games = fetch_analysis_paginated(username, max_games=max_games, since=since, until=until)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

    filtered_games = raw_games

    if end_type and end_type != "all":
        filtered_games = [g for g in filtered_games if g.get("status", "").lower() == end_type]

    if color in ("white", "black"):
        uname = username.lower()
        filtered_games = [g for g in filtered_games if
                          g.get("players", {}).get(color, {}).get("user", {}).get("name", "").lower() == uname]

    filtered_games = filtered_games[:max_games]

    result = []
    for game in filtered_games:
        result.append({
            "id": game.get("id"),
            "createdAt": game.get("createdAt"),
            "status": game.get("status"),
            "winner": game.get("winner"),
            "players": game.get("players"),
            "opening": game.get("opening", {}),
            "moves": game.get("moves"),
            "is_analysed": game.get("is_analysed"),
        })

    return jsonify(result)

@app.route("/match")
def match():
    username = session.get("username")
    if not username:
        return redirect("/")

    return render_template("match.html", username=username)  # 🔹 템플릿에 전달

@app.route("/api/matches")
def api_matches():
    username = session.get("username")
    if not username:
        return jsonify({"error": "세션 없음"}), 403

    url = f"https://lichess.org/api/games/user/{username}"
    headers = {"Accept": "application/x-ndjson"}
    params = {"max": 200, "opening": "false"}

    try:
        resp = requests.get(url, headers=headers, params=params)
        games = [json.loads(line) for line in resp.text.strip().split("\n")]
    except Exception as e:
        return jsonify({"error": f"Lichess API 실패: {str(e)}"}), 500

    stats = defaultdict(lambda: {"games": 0, "wins": 0, "draws": 0, "losses": 0})

    for game in games:
        try:
            white = game["players"]["white"]["user"]["name"]
            black = game["players"]["black"]["user"]["name"]
        except KeyError:
            continue  # 이름 없는 게임 스킵

        winner = game.get("winner")
        is_white = username.lower() == white.lower()
        opponent = black if is_white else white

        stats[opponent]["games"] += 1
        if winner is None:
            stats[opponent]["draws"] += 1
        elif (winner == "white" and is_white) or (winner == "black" and not is_white):
            stats[opponent]["wins"] += 1
        else:
            stats[opponent]["losses"] += 1

    # 2회 이상만 필터링
    filtered = {op: stat for op, stat in stats.items() if stat["games"] >= 2}
    return jsonify({"username": username, "stats": filtered})

if __name__ == "__main__":
    app.run(host="0.0.0.0",debug=True, port=80)
