import chess
import time
import numpy

global base_case_board_value_funcs
base_case_board_value_funcs = []

global MAX_BOARD_VALUE
MAX_BOARD_VALUE = 1000

global known_boards
known_boards = {}

global created_boards
created_boards = 0
# Returns total material value
def materialValueHelper(board,turn):
	return 9 * len(board.pieces(chess.QUEEN,turn)) + \
		5 * len(board.pieces(chess.ROOK,turn)) + \
		3 * (len(board.pieces(chess.KNIGHT,turn)) + len(board.pieces(chess.BISHOP,turn))) + \
		1 * len(board.pieces(chess.PAWN,turn))
def calculateMaterialValue(board):
	my_value = materialValueHelper(board,board.turn)
	opponent_value = materialValueHelper(board, not board.turn)
	value =	500 + 500 * (my_value - opponent_value) / (my_value + opponent_value)
	#print(board, my_value, opponent_value,value)
	# In the edge case the opponent is ahead on value but cannot win, but I can (I have two pawns to one bishop) this code breaks.
	if board.has_insufficient_material((value > 500) ^ (not board.turn)):
		return 500
	return value

valuePerMove = MAX_BOARD_VALUE/218
def calculateSpaceValue(board):
	return valuePerMove * board.legal_moves.count() - 1
def calculatePawnDistanceValue(board):
	pass
def calculateCheckValue(board):
	pass
# Generate all immediate boards from possible moves.
def getBoardEvaluator(board,move):
	board = board.copy(stack=False)
	board.push(move)
	fen = board.fen()
	if fen in known_boards:
		return known_boards[fen]
	return BoardEvaluator(board,fen)

class BoardEvaluator:
	def __init__(self,board,fen):
		self.board = board
		self.fen = fen
		self.generator = self.calculateBoardValueRecurse();
		self.value = next(self.generator)
		self.time_since_last_update = 0
		known_boards[self.fen] = self
		global created_boards
		created_boards += 1
	def update(self,allowed_time):
		self.time_since_last_update = 0
		return self.generator.send(allowed_time)
	def generateFutureBoards(self):
		return [getBoardEvaluator(self.board,move) for move in self.board.legal_moves]
	# Updates the known boards with a new value. TODO should probably take existing value into consideration based on some set of params.
	def updateValue(self,value):
		# For now, assuming the new value is better than the old.
		self.value = value
		return value
	# Compute board value with literally no lookahead.
	def calculateBoardValueBaseCase(self):
		# Do we already have a value? It must be better or equal to what I can compute on my own.
		if self.fen in known_boards:
			return known_boards[self.fen].value
		# That's the worst case scenario. Return 0.
		if self.board.is_checkmate():
			return 0
		# It's somewhere in the middle, return half.
		if self.board.is_game_over():
			return MAX_BOARD_VALUE >> 1
		# Go through all base case functions and return a final value.
		# Different value computation functions can be of different importance to final board value.
		# Those weights get added to a pseudo cardinality to generate a pseudo average affecting how important different value computation functions are relative to each other.
		pseudo_cardinality = 0
		sum = 0
		for func,weight in base_case_board_value_funcs:
			sum += weight * func(self.board)
			pseudo_cardinality += weight
		return self.updateValue(sum / pseudo_cardinality)
	# Calculates a board value using lookahead to work towards base cases.
	def calculateBoardValueRecurse(self):
		# yield an "eyeing it" value. When we hit this line, we're calculating the "oppoonent's" board value. e.g. if the opponent is checkmated, then the board value is zero for the opponent.
		# Invert value to return actual value for the player who cares.
		allowed_time = yield (MAX_BOARD_VALUE - self.calculateBoardValueBaseCase())

		# We're interested in this move and want to know more. Let's do some more gooder calculation.

		# What time did we start?
		start_time = time.monotonic()
		future_boards = self.generateFutureBoards()
		schedule_chances = [b.value for b in future_boards]

		numPossibleMoves = len(future_boards)
		if numPossibleMoves == 0:
			while True:
				yield self.value
		while True:
			elapsed_time = time.monotonic()-start_time

			# How long should we analyze submoves? enough time to theoretically analyze all possible moves.
			max_allowed_time = allowed_time/numPossibleMoves

			while elapsed_time < allowed_time:
				#Choose a board.
				chosenBoardIndex = numpy.random.choice(range(numPossibleMoves),p=numpy.divide(schedule_chances,sum(schedule_chances)))
				# Update lottery registry by giving that board position some computation time to calculate a better value.
				schedule_chances[chosenBoardIndex] = future_boards[chosenBoardIndex].update(min(max_allowed_time,allowed_time - elapsed_time))
				elapsed_time = time.monotonic()-start_time
			# We're calculating value from the opponent's perspective, relative to the caller. So the lower the value, the better. Invert board value.
			allowed_time = yield (MAX_BOARD_VALUE - max(schedule_chances))
			start_time = time.monotonic()




# Returns a final move based on board.
def calculateMove(board,allowed_time):
	# What time did we start thinking about this?
	fen = board.fen()
	eval = None
	if fen in known_boards:
		eval = known_boards[fen]
	else:
		eval = BoardEvaluator(board,fen)
	start_time = time.monotonic()
	future_boards = eval.generateFutureBoards()
	# Get all future board generators
	numPossibleMoves = len(future_boards)
	# Update future boards lottery registry using "eyeing it" values. We don't need this, but keeping it in sync locally reduces amount of work for a refresh of chances.
	schedule_chances = [b.value for b in future_boards]
	# Keep doing this until we're out of time
	elapsed_time = time.monotonic()-start_time
	max_allowed_time = allowed_time/numPossibleMoves
	while elapsed_time < allowed_time:
		# This is likely the most expensive one-liner in the whole program.
		chosenBoardIndex = numpy.random.choice(range(numPossibleMoves),p=numpy.divide(schedule_chances,sum(schedule_chances)))
		# Update lottery registry by giving that board position some computation time to calculate a better value.
		schedule_chances[chosenBoardIndex] = future_boards[chosenBoardIndex].update(min(max_allowed_time,allowed_time - elapsed_time))
		elapsed_time = time.monotonic()-start_time
	#print(board.legal_moves)
	#print(schedule_chances)
	return [move for move in board.legal_moves][schedule_chances.index(max(schedule_chances))]



# Initialization stuff

# Assigning arbitrary weights to these functions based on guess work. If I felt like spending time making a harness along with some light
# machine learning work, I could customize these parameters programmatically to find just how valuable these different aspects of a board are relative to each other.
base_case_board_value_funcs.append((calculateMaterialValue,4))
base_case_board_value_funcs.append((calculateSpaceValue,2))


if __name__ == '__main__':
	board = chess.Board()
	board.push_san("e4")
	board.push_san("e5")
	board.push_san("Qh5")
	board.push_san("Nc6")
	board.push_san("Bc4")
	board.push_san("Nf6")
	start = time.monotonic()
	move = calculateMove(board,2)
	end = time.monotonic()
	print("Total time was ",end-start)
	board.push_uci(move.uci())
	if board.is_checkmate():
		print("Program succesfully checkmated")
	else:
		print("Program did not checkmate.")
	print(created_boards)
	#board.push_san("Qxf7")
	"Test AI awesomeness."
