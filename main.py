if __name__ == "__main__":
    import os
    import uvicorn

    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port)
from fastapi import FastAPI
from pydantic import BaseModel
import requests          
import io
import chess
import chess.engine
import chess.pgn

app = FastAPI()

class GameRequest(BaseModel):
    username: str

@app.post("/analyze")
def analyze_game(req: GameRequest):
    username = req.username
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/120.0.0.0 Safari/537.36"}
    archives = requests.get(
    f"https://api.chess.com/pub/player/{username}/games/archives",
    headers=headers
    ).json()["archives"]

    latest_month_url = archives[-1]
    games = requests.get(latest_month_url, headers=headers).json()["games"]
    latest_game_pgn = games[-1]["pgn"]

    pgn = io.StringIO(latest_game_pgn)
    game = chess.pgn.read_game(pgn)
    board = game.board()

    engine = chess.engine.SimpleEngine.popen_uci(engine_path)

    board = game.board()

    evaluations = []
    move_labels = []

    mvcount = 0
    prev_eval_white = 0.0
    prev_eval_black = 0.0
    total_loss_white = 0.0
    total_loss_black = 0.0

    your_username = req.username.lower()

    your_color = (
        chess.WHITE if game.headers["White"].lower() == your_username
        else chess.BLACK
    )

    moves_made = {
        "wtotGood": 0, "btotGood": 0,
        "wtotGreat": 0, "btotGreat": 0,
        "wtotExcellent": 0, "btotExcellent": 0,
        "wtotBest": 0, "btotBest": 0,
        "wtotBook": 0, "btotBook": 0,
        "wtotInaccuracy": 0, "btotInaccuracy": 0,
        "wtotMistake": 0, "btotMistake": 0,
        "wtotBlunder": 0, "btotBlunder": 0,
        "wtotBrilliant": 0, "btotBrilliant": 0
    }

    for node in game.mainline():
        mvcount += 1
        move = node.move

        # --- Evaluation BEFORE move ---
        pre_info = engine.analyse(
            board,
            chess.engine.Limit(depth=14),
            multipv=2
        )

        pre_scores = [
            entry["score"].pov(board.turn).score(mate_score=10000)
            for entry in pre_info
        ]

        best_pre = pre_scores[0]
        second_pre = pre_scores[1] if len(pre_scores) > 1 else best_pre

        # Did player play engine's top move?
        player_move_index = None
        for i, entry in enumerate(pre_info):
            if entry["pv"][0] == move:
                player_move_index = i
                break

        played_is_best = (player_move_index == 0)

        # Capture info (for brilliancy)
        is_capture = board.is_capture(move)
        moved_piece = board.piece_at(move.from_square)
        captured_piece = board.piece_at(move.to_square)

        # --- Push move ---
        board.push(move)
        color_just_moved = not board.turn

        # --- Evaluation AFTER move ---
        info = engine.analyse(board, chess.engine.Limit(depth=14))
        score_obj = info["score"].pov(color_just_moved)

        if score_obj.is_mate():
            eval_cp = 10.0 if score_obj.mate() >= 0 else -10.0
        else:
            eval_cp = score_obj.score() / 100.0

        evaluations.append(eval_cp)

        # --- ACPL tracking ---
        if color_just_moved == chess.WHITE:
            loss = abs(prev_eval_white - eval_cp)
            total_loss_white += loss
            diff = prev_eval_white - eval_cp
            prev_eval_white = eval_cp
            side = "w"
        else:
            loss = abs(prev_eval_black - eval_cp)
            total_loss_black += loss
            diff = prev_eval_black - eval_cp
            prev_eval_black = eval_cp
            side = "b"

        # --- Brilliancy detection ---
        brilliant = (
            played_is_best and
            is_capture and
            moved_piece and
            captured_piece and
            captured_piece.piece_type > moved_piece.piece_type and
            (best_pre - second_pre) > 80
        )

        # --- Move labeling ---
        if brilliant:
            label = "Brilliant"
        elif diff == 0:
            label = "Best"
        elif diff <= 0.2:
            label = "Excellent"
        elif diff <= 0.5:
            label = "Great"
        elif diff <= 1.0:
            label = "Good"
        elif diff <= 2.0:
            label = "Inaccuracy"
        elif diff <= 4.0:
            label = "Mistake"
        else:
            label = "Blunder"

        move_labels.append(label)

        moves_made[f"{side}tot{label}"] += 1


    acpl_white = total_loss_white / (mvcount / 2)
    acpl_black = total_loss_black / (mvcount / 2)

    waccuracy = acpl_to_accuracy(acpl_white)
    baccuracy = acpl_to_accuracy(acpl_black)

    wrating = acpl_to_rating(acpl_white)
    brating = acpl_to_rating(acpl_black)
    engine.quit()

    return {
    "meta": {
        "white": game.headers["White"],
        "black": game.headers["Black"],
        "moves": mvcount
    },
    "evaluations": evaluations,
    "move_labels": move_labels,
    "accuracy": {
        "white": waccuracy,
        "black": baccuracy
    },
    "estimated_rating": {
        "white": wrating,
        "black": brating
    },
    "move_breakdown": moves_made,
    "you": {
  "username": req.username,
  "color": "white" if your_color == chess.WHITE else "black"
    }
}