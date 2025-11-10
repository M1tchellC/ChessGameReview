import requests
import chess
import chess.engine
import chess.pgn
import io
import chess.polyglot
import plotly.graph_objs as go
from plotly.subplots import make_subplots

#Function to check if opening moves are 'book'
def in_book(board):
    
    with chess.polyglot.open_reader(r"C:\Users\mitch\Downloads\gm2001.bin") as reader:
        try:
            entry = reader.find(board)
            return entry is not None
        except IndexError:
            return False

    return True


username = "possiblyai"  # Replace with your Chess.com username
url = f"https://api.chess.com/pub/player/{username}/games/archives"

headers = { #User tag to allow API access
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/120.0.0.0 Safari/537.36"
}

response = requests.get(url, headers = headers)

print("Status code:", response.status_code)
print("Response text:", response.text[:500])

data = response.json()  #Check if access to API is valid
print(data)


engine_path = r"C:\Users\mitch\OneDrive\Desktop\AIMLProject\stockfish-windows-x86-64-avx2\stockfish\stockfish-windows-x86-64-avx2.exe" #importing stockfish locally

#Obtain latest game
archives = requests.get(f"https://api.chess.com/pub/player/{username}/games/archives", headers=headers).json()["archives"]
latest_month_url = archives[-1]
games = requests.get(latest_month_url, headers=headers).json()["games"]
latest_game_pgn = games[-1]["pgn"]

#Turn PGN into string
pgn = io.StringIO(latest_game_pgn)
game = chess.pgn.read_game(pgn)

#Initialize Chess Engine
engine = chess.engine.SimpleEngine.popen_uci(engine_path)
board = game.board()

#Iterate through game and analyze moves (With stockfish)
prev_eval = 0
eval_cp = 0
white_player = game.headers["White"].lower()
black_player = game.headers["Black"].lower()
your_username = "possiblyai"
if white_player == your_username:
    your_color = chess.WHITE
    colr = "white"
    print("You played as White")
else:
    your_color = chess.BLACK
    colr = "black"
    print("You played as Black")
mvcount = 0
prev_eval_white = 0.0
prev_eval_black = 0.0
total_loss_white = 0.0
total_loss_black = 0.0
evaluations = []
for node in game.mainline():
    mvcount += 1
    move = node.move
    board.push(move)

    color_to_move = not board.turn  # because we pushed already
    info = engine.analyse(board, chess.engine.Limit(depth=15))
    score_obj = info["score"].pov(color_to_move)

    if score_obj.is_mate():
        eval_cp = 1000 if score_obj.mate() >= 0 else -1000 #Eval if mate
    else:
        eval_cp = score_obj.score() / 100  #convert centipawns to pawns

    loss = abs(prev_eval - eval_cp)
    evaluations.append(eval_cp)
    if color_to_move == chess.WHITE:
        total_loss_white += loss
    else:
        total_loss_black += loss
    
    if color_to_move == chess.WHITE:
        diff = prev_eval_white - eval_cp
    else:
        diff = prev_eval_black - eval_cp

    #Move labeling
    if (mvcount <= 8 and in_book(board)):
        label = "Book"
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

    #Brilliant move detection - sacrifical moves that benefit in the long run
    if board.is_capture(move):
        piece = board.piece_at(move.from_square)
        captured = board.piece_at(move.to_square)
        if captured and piece and captured.piece_type > piece.piece_type:
            if eval_cp > prev_eval + 0.5:
                label = "Brilliant!"

    node.comment = f"Eval: {eval_cp:.2f} ({label})"
    if color_to_move == chess.WHITE:
        prev_eval_white = eval_cp
    else:
        prev_eval_black = eval_cp

engine.quit()

#Dictionary to contain player move totals
moves_made = {"btotGood" : 0, "wtotGood" : 0, "btotGreat" : 0, "wtotGreat" : 0,
              "btotExcellent" : 0, "wtotExcellent" : 0, "btotBest" : 0, "wtotBest" : 0,
              "btotBook" : 0, "wtotBook" : 0, "btotBlunder" : 0, "wtotBlunder" : 0,
              "btotMistake" : 0, "wtotMistake" : 0, "btotInaccuracy" : 0, "wtotInaccuracy" : 0,
              "btotBrilliant" : 0, "wtotBrilliant" : 0}
count = 0
for node in game.mainline():
    #adding move labels
    if (count % 2 == 0): #White always goes first, odd turns
        print("White turn")
        print(node.comment)
        if "(Good)" in node.comment:
            moves_made["wtotGood"] += 1
        if "(Great)" in node.comment:
            moves_made["wtotGreat"] += 1
        if "(Excellent)" in node.comment:
            moves_made["wtotExcellent"] += 1
        if "(Best)" in node.comment:
            moves_made["wtotBest"] += 1
        if "(Brilliant)" in node.comment:
            moves_made["wtotBrilliant"] += 1
        if "(Inaccuracy)" in node.comment:
            moves_made["wtotInaccuracy"] += 1
        if "(Mistake)" in node.comment:
            moves_made["wtotMistake"] += 1
        if "(Blunder)" in node.comment:
            moves_made["wtotBlunder"] += 1
        if "(Book)" in node.comment:
            moves_made["wtotBook"] += 1
    else:
        print("Black turn")
        print(node.comment)
        if "(Good)" in node.comment:
            moves_made["btotGood"] += 1
        if "(Great)" in node.comment:
            moves_made["btotGreat"] += 1
        if "(Excellent)" in node.comment:
            moves_made["btotExcellent"] += 1
        if "(Best)" in node.comment:
            moves_made["btotBest"] += 1
        if "(Brilliant)" in node.comment:
            moves_made["btotBrilliant"] += 1
        if "(Inaccuracy)" in node.comment:
            moves_made["btotInaccuracy"] += 1
        if "(Mistake)" in node.comment:
            moves_made["btotMistake"] += 1
        if "(Blunder)" in node.comment:
            moves_made["btotBlunder"] += 1
        if "(Book)" in node.comment:
            moves_made["btotBook"] += 1
    count += 1

#ACPL -> Average Centipawn Loss
#Used to determine determine accuracy and game rating
acpl_white = (total_loss_white)/(mvcount/2)
acpl_black = (total_loss_black)/(mvcount/2)

def acpl_to_accuracy(acpl):
    #Based on prior data
    return max(0, min(100, 103 - 2.5 * (acpl ** 0.5)))
waccuracy = acpl_to_accuracy(acpl_white)
baccuracy = acpl_to_accuracy(acpl_black)

def acpl_to_rating(acpl): #Based off stockfish data
    return int(2500 / (1 + 0.02 * acpl))
wrating = acpl_to_rating(acpl_white)
brating = acpl_to_rating(acpl_black)

#Check move counts for debugging    
print(f"""White:\n Blunders: {moves_made['wtotBlunder']} Mistakes: {moves_made['wtotMistake']} Inaccuracies: {moves_made['wtotInaccuracy']}
      Book: {moves_made['wtotBook']} Good: {moves_made['wtotGood']} Great: {moves_made['wtotGreat']} Excellent: {moves_made['wtotExcellent']}
      Best: {moves_made['wtotBest']} Brilliant: {moves_made['wtotBrilliant']}""")
print(f"""Black:\n Blunders: {moves_made['btotBlunder']} Mistakes: {moves_made['btotMistake']} Inaccuracies: {moves_made['btotInaccuracy']}
      Book: {moves_made['btotBook']} Good: {moves_made['btotGood']} Great: {moves_made['btotGreat']} Excellent: {moves_made['btotExcellent']}
      Best: {moves_made['btotBest']} Brilliant: {moves_made['btotBrilliant']}""")
print(f"White played with an accuracy of {waccuracy:.2f}% and at a rating of {wrating}. Black played with an accuracy of {baccuracy:.2f}% and at a rating of {brating}")
#Creates a pgn file that can be opened on chess sites with updated move labels
with open("annotated_game.pgn", "w", encoding="utf-8") as f:
    print(game, file=f)

print(f"{mvcount} moves were made during the game")
print("Game analysis complete! Saved as 'annotated_game.pgn'")

try:
    engine.quit()
except chess.engine.EngineTerminatedError:
    print("Engine already shut down.")

#Setting up game evaluation scatter plot
move_labels = [str(i) for i in range(1, mvcount + 1)]
#Capping mate eval scores to avoid plotting outliers
clamped_evaluations = []
counter = 0
#Ensuring pawn evaluation for my player only is plotted (and capping outliers)
if (colr == "white"):
    while (counter < mvcount):
        if (counter % 2 == 0):
            clamped_evaluations.append(max(min(evaluations[counter], 10), -10))
        counter += 1
elif (colr == "black"):
    while (counter < mvcount):
        if (counter % 2 == 1):
            clamped_evaluations.append(max(min(evaluations[counter], 10), -10))
        counter += 1
        
eval_trace = go.Scatter(
    x=move_labels,
    y=clamped_evaluations,
    mode='lines+markers',
    name='Game Evaluation (pawns)',
    line=dict(color='blue')
)

#Bar chart containing player move totals
categories = ['Brilliant', 'Best', 'Excellent', 'Great', 'Good', 'Inaccuracy', 'Mistake', 'Blunder', 'Book']
white_counts = [
    moves_made['wtotBrilliant'],
    moves_made['wtotBest'],
    moves_made['wtotExcellent'],
    moves_made['wtotGreat'],
    moves_made['wtotGood'],
    moves_made['wtotInaccuracy'],
    moves_made['wtotMistake'],
    moves_made['wtotBlunder'],
    moves_made['wtotBook']
]
black_counts = [
    moves_made['btotBrilliant'],
    moves_made['btotBest'],
    moves_made['btotExcellent'],
    moves_made['btotGreat'],
    moves_made['btotGood'],
    moves_made['btotInaccuracy'],
    moves_made['btotMistake'],
    moves_made['btotBlunder'],
    moves_made['btotBook']
]

bar_white = go.Bar(
    x=categories,
    y=white_counts,
    name='White Move Breakdown',
    marker=dict(color='lightgray')
)

bar_black = go.Bar(
    x=categories,
    y=black_counts,
    name='Black Move Breakdown',
    marker=dict(color='black')
)

#Seperate into subplots
fig = make_subplots(
    rows=2, cols=1,
    row_heights=[0.7, 0.3],
    subplot_titles=("Game Evaluation", "Move Quality Breakdown")
)

fig.add_trace(eval_trace, row=1, col=1)
fig.add_trace(bar_white, row=2, col=1)
fig.add_trace(bar_black, row=2, col=1)


#Layout modifications
fig.update_layout(
    height=800,
    width=900,
    title_text=f"Chess Game Analysis ({colr.capitalize()})",
    xaxis_title="Move Number",
    yaxis_title="Evaluation (pawns)",
    barmode='group',
    legend=dict(x=0.02, y=0.98),
    template='plotly_dark'
)

#Extra statistics
fig.add_annotation(text=f"White Accuracy: {waccuracy:.1f}%", xref="paper", yref="paper", x=0.02, y=1.05, showarrow=False)
fig.add_annotation(text=f"White Game Rating: {wrating:.1f}", xref="paper", yref="paper", x=0.02, y=1.075, showarrow=False)
fig.add_annotation(text=f"White Accuracy: {baccuracy:.1f}%", xref="paper", yref="paper", x=0.4, y=1.05, showarrow=False)
fig.add_annotation(text=f"Black Game Rating: {brating:.1f}", xref="paper", yref="paper", x=0.4, y=1.075, showarrow=False)


#Display figure
fig.show()



