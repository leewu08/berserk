from flask import Flask, request, render_template
import berserk

app = Flask(__name__)

# 토큰은 보통 환경변수로 관리하는 것이 좋지만 여기선 예시로 하드코딩
TOKEN = "YOUR_LICHESS_TOKEN"
session = berserk.TokenSession(TOKEN)
client = berserk.Client(session)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/player", methods=["POST"])
def player():
    username = request.form["username"]
    user = client.users.get(username)
    games = client.games.export_by_user(username, max=20)  # 최근 20게임
    game_list = list(games)  # generator → list
    
    # 간단한 승률 계산 예시
    wins = sum(1 for g in game_list if g.get("winner") == "white" and g["players"]["white"]["user"]["name"].lower() == username.lower() or
                                       g.get("winner") == "black" and g["players"]["black"]["user"]["name"].lower() == username.lower())
    total = len(game_list)
    win_rate = round(wins / total * 100, 2) if total else 0

    return render_template("player.html", user=user, win_rate=win_rate, total=total)

if __name__ == "__main__":
    app.run(debug=True)where python