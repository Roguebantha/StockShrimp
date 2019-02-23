import chess
import time
global base_case_board_value_funcs = []
global MAX_BOARD_VALUE = 1000
global known_boards = {}
# Returns total material value
def calculateMaterialValue(board):
	pass
def calculateSpaceValue(board):
	pass
# Generate all immediate boards from possible moves.
def generateFutureBoards(board):
	future_boards = []
	for move in board.legal_moves:
		future_boards.append(board.copy(stack=False))
		future_boards[len(future_boards)-1].push(move)

# Updates the known boards with a new value. TODO should probably take existing value into consideration based on some set of params.
def updateValue(board,value):
	# For now, assuming the new value is better than the old.
	known_boards[board.fen()] = value
	return value

# Compute board value with literally no lookahead.
def calculateBoardValueBaseCase(board):
	# Do we already have a value? It must be better or equal to what I can compute on my own.
	try:
		return known_boards[board.fen()]
	except Exception as e:
		pass
	# Go through all base case functions and return a final value.
	sum = 0
	# Different value computation functions can be of different importance to final board value.
	# Those weights get added to a pseudo cardinality to generate a pseudo average affecting how important different value computation functions are relative to each other.
	pseudo_cardinality = 0
	for func,weight in base_case_board_value_funcs:
		sum += weight * func(board)
		psuedo_cardinality += weight
	return updateValue(board,sum / psuedo_cardinality)

# Returns a final move based on board.
def calculateMove(board,allowed_time):
	# What time did we start thinking about this?
	start_time = time.monotonic()
	future_boards = generateFutureBoards(board)
	# Get all future board generators
	board_generators = [calculateBoardValueRecurse(b) for b in future_boards]
	numPossibleMoves = len(board_generators)
	# Update future boards lottery registry using "eyeing it" values
	schedule_chances = [next(board_generator) for board_generator in board_generators]
	# Keep doing this until we're out of time
	while (time.monotonic() - start_time) < allowed_time:
		schedule = []
		# For all the different boards, add to the lottery pool the respective generator index multiple times based on registry.
		for i in range(numPossibleMoves):
			schedule.extend(schedule_chances[i]*i)
		# Play the lottery! Grab a random value from the schedule. That's the index for the generator we're testing this time.
		generator_index = schedule[random.randint(len(schedule))]
		# Update lottery registry by giving that board position some computation time to calculate a better value.
		schedule_chances[generator_index] = board_generators[generator_index].send(min(allowed_time/numPossibleMoves,allowed_time - (time.monotonic()-start_time)))
	return board.legal_moves[schedule_chances.index(max(schedule_chances))]

# Calculates a board value using lookahead to work towards base cases.
def calculateBoardValueRecurse(board):
	# yield an "eyeing it" value.
	allowed_time = yield calculateBoardValueBaseCase(board)

	# We're interested in this move and want to know more. Let's do some more gooder calculation.

	# What time did we start?
	start_time = time.monotonic()
	future_boards = generateFutureBoards(board)
	board_generators = [calculateBoardValueRecurse(b) for b in future_boards]
	numPossibleMoves = len(board_generators)
	schedule_chances = [next(board_generator) for board_generator in board_generators]
	bool isOpponentMove = False
	while True:
		# How long should we analyze submoves? enough time to theoretically analyze all possible moves.
		maxTimePerMove = allowed_time / numPossibleMoves
		isOpponentMove = not isOpponentMove
		# Cache end time for faster while loop condition operation
		end_time = start_time + allowed_time
		while time.monotonic() < end_time:
			# Prep the lottery!
			schedule = []
			for i in range(len(schedule_chances)):
				schedule.extend(schedule_chances[i]*i)
			generator_index = schedule[random.randint(len(schedule))]
			# Play the lottery and update
			schedule_chances[generator_index] = board_generators[generator_index].send(min(maxTimePerMove,allowed_time - (time.monotonic()-start_time)))
		# This is not quite right. Our board is now divorced from the original board generators. I don't think that's okay.
		#board.push(board.legal_moves[schedule_chances.index(max(schedule_chances))])
		allowed_time = (yield MAX_BOARD_VALUE - schedule_chances.index(max(schedule_chances))) if isOpponentMove else (yield schedule_chances.index(max(schedule_chances)))
		start_time = time.monotonic()
# Initialization stuff

# Assigning arbitrary weights to these functions based on guess work. If I felt like spending time making a harness along with some light
# machine learning work, I could customize these parameters programmatically to find just how valuable these different aspects of a board are relative to each other.
base_case_board_value_funcs.append((calculateMaterialValue,4))
base_case_board_value_funcs.append((calculateSpaceValue,2))


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
