import chess
import chess.pgn
import io
import matplotlib.pyplot as plt
import seaborn as sns
from collections import Counter

def analyze_chess_moves(pgn_text):
    game = chess.pgn.read_game(io.StringIO(pgn_text))
    board = game.board()

    piece_development = []
    file_usage = []
    early_queen_deploy = False
    castling_done = False
    side_pawn_pushes = []
    move_count = 0

    for move in game.mainline_moves():
        move_count += 1
        board.push(move)
        uci = move.uci()
        from_sq, to_sq = uci[:2], uci[2:]
        piece = board.piece_at(chess.parse_square(to_sq))

        if piece:
            piece_name = piece.symbol().upper()
            if piece_name in ['N', 'B', 'Q']:
                piece_development.append((piece_name, move_count))

            if piece_name == 'Q' and move_count <= 6:
                early_queen_deploy = True

        file = to_sq[0]
        file_usage.append(file)

        if move == chess.Move.from_uci('e1g1') or move == chess.Move.from_uci('e1c1') or \
           move == chess.Move.from_uci('e8g8') or move == chess.Move.from_uci('e8c8'):
            castling_done = True

        if file in ['a', 'h'] and move_count <= 10:
            side_pawn_pushes.append((file, move_count))

    return {
        "development": piece_development,
        "file_usage": file_usage,
        "early_queen": early_queen_deploy,
        "castling": castling_done,
        "side_pawn_pushes": side_pawn_pushes
    }

def plot_file_usage(file_usage):
    file_counts = Counter(file_usage)
    files = sorted(file_counts.keys())
    values = [file_counts[f] for f in files]

    sns.barplot(x=files, y=values)
    plt.title("파일별 수 분포 (a~h)")
    plt.xlabel("파일(열)")
    plt.ylabel("수 빈도")
    plt.tight_layout()
    plt.show()

def print_summary(result):
    print("📊 체스 기보 구조적 분석 요약")
    print("-" * 40)

    dev = result["development"]
    print(f"🧩 기물 전개:")
    for piece, move in dev:
        print(f"  - {piece} 전개 (수 {move}에)")

    print(f"\n👑 조기 퀸 전개: {'Yes' if result['early_queen'] else 'No'}")
    print(f"🏰 캐슬링 여부: {'Yes' if result['castling'] else 'No'}")

    if result["side_pawn_pushes"]:
        print("\n🧨 이른 측면 폰 푸시:")
        for file, move in result["side_pawn_pushes"]:
            print(f"  - {file}-file에서 수 {move}에 푸시")

if __name__ == "__main__":
    # 예제 기보
    pgn_text = "1. e4 g6 2. Nf3 Bg7 3. d4 h5 4. h4 c6 5. Bc4 b5 6. Bb3 a5 7. Ng5 e6 8. Qf3"

    result = analyze_chess_moves(pgn_text)
    print_summary(result)
    plot_file_usage(result["file_usage"])
