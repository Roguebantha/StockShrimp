import chess
import time
def calculateMove(board,allowed_time):
	"Actually called to return the move to make"
	start_time = time.monotonic()
	future_boards = [board.copy(stack=False).push(move) for move in board.legal_moves]
	board_generators = [calculateValue(b) for b in future_boards]
	schedule_chances = [next(board_generator) for board_generator in board_generators]
	while (time.monotonic() - start_time) < allowed_time:
		schedule = []
		for i in range(len(schedule_chances)):
			for j in range(schedule_chances[i]):
				schedule.append(i)
		generator_index = schedule[random.randint(len(schedule))]
		schedule_chances[generator_index] = board_generators[generator_index].send(min(.1,allowed_time - (time.monotonic()-start_time)))
	return board.legal_moves[schedule_chances.index(max(schedules))]

def calculateValue(board):
	"Calculates board value somehow"
if __name__ == '__main__':
	chess_board = chess.Board()
	board.push_san("e4")
	board.push_san("e5")
	board.push_san("Qh5")
	board.push_san("Nc6")
	board.push_san("Bc4")
	board.push_san("Nf6")
	board.push_san(calculateMove(board))
	#board.push_san("Qxf7")
	"Test AI awesomeness."
