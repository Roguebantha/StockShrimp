#!/usr/bin/env python3
import chess
import chess.pgn
import time
import numpy
import random
import uci_client

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
def calculateMaterialValue(board,legal_moves):
	my_value = materialValueHelper(board,board.turn)
	opponent_value = materialValueHelper(board, not board.turn)
	value =	500 + 500 * (my_value - opponent_value) / (my_value + opponent_value)
	#print(board, my_value, opponent_value,value)
	# In the edge case the opponent is ahead on value but cannot win, but I can (I have two pawns to one bishop) this code breaks.
	if board.has_insufficient_material((value > 500) ^ (not board.turn)):
		return 500
	return value

valuePerMove = MAX_BOARD_VALUE/218
def calculateSpaceValue(board,pseudo_legal_moves):
	my_value = valuePerMove * len(pseudo_legal_moves)
	board.turn = not board.turn
	opponent_value = valuePerMove * len(list(board.generate_pseudo_legal_moves()))
	value =	500 + 500 * (my_value - opponent_value) / (my_value + opponent_value)
	board.turn = not board.turn
	return value
def calculatePawnDistanceValue(board):
	pass
def calculateCheckValue(board):
	pass
def calculateThreatsValue(board):
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
		self.pseudo_legal_moves = list(self.board.generate_pseudo_legal_moves())
		self.legal_moves = [move for move in self.pseudo_legal_moves if self.board.is_legal(move)]
		self.generator = self.calculateBoardValueRecurse();
		self.value = next(self.generator)
		self.time_since_last_update = 0
		self.runs = 0
		known_boards[self.fen] = self
		global created_boards
		created_boards += 1
	def update(self,allowed_time):
		self.time_since_last_update = 0
		self.runs += 1
		return self.generator.send(allowed_time)
	def generateFutureBoards(self):
		return [getBoardEvaluator(self.board,move) for move in self.legal_moves]
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
			sum += weight * func(self.board,self.pseudo_legal_moves)
			pseudo_cardinality += weight
		#print(sum,pseudo_cardinality)
		return self.updateValue(sum / pseudo_cardinality)
	# Calculates a board value using lookahead to work towards base cases.
	def calculateBoardValueRecurse(self):
		# yield an "eyeing it" value. When we hit this line, we're calculating the "oppoonent's" board value. e.g. if the opponent is checkmated, then the board value is zero for the opponent.
		# Invert value to return actual value for the player who cares.
		allowed_time = yield (MAX_BOARD_VALUE - self.calculateBoardValueBaseCase())
		#print(allowed_time)
		# We're interested in this move and want to know more. Let's do some more gooder calculation.

		# What time did we start?
		start_time = time.monotonic()
		future_boards = self.generateFutureBoards()
		schedule_chances = [b.value for b in future_boards]
		numPossibleMoves = len(future_boards)
		if numPossibleMoves == 0:
			while True:
				yield self.value
		#opportunities = 1
		while True:
			elapsed_time = time.monotonic()-start_time
			# How long should we analyze submoves? enough time to theoretically analyze all possible moves.
			max_allowed_time = allowed_time/(numPossibleMoves)
			while elapsed_time < allowed_time:
				#Choose a board.
				if sum(schedule_chances) == 0:
					break
				if random.random() > 0.5:
					chosenBoardIndex = numpy.random.choice(range(numPossibleMoves),p=numpy.divide(schedule_chances,sum(schedule_chances)))
				else:
					chosenBoardIndex = schedule_chances.index(max(schedule_chances))
				max_value = max(schedule_chances)
				#print("Highest value move is currently ",list(self.board.legal_moves)[schedule_chances.index(max_value)])
				#print("With a score of ",max_value)
				#print("Evaluating ",list(self.board.legal_moves)[chosenBoardIndex])
				#print("Which has calculated value ", schedule_chances[chosenBoardIndex])
				# Update lottery registry by giving that board position some computation time to calculate a better value.
				schedule_chances[chosenBoardIndex] = future_boards[chosenBoardIndex].update(min(max_allowed_time,allowed_time - elapsed_time))
				#print("Now has calculated value ", schedule_chances[chosenBoardIndex])
				elapsed_time = time.monotonic()-start_time
				#for i in range(len(schedule_chances)):
				#	print("Move: " + str(list(board.legal_moves)[i]) + "; Value: " + str(schedule_chances[i]) + "; Runs: ",future_boards[i].runs)
				#print("\n")
			# We're calculating value from the opponent's perspective, relative to the caller. So the lower the value, the better. Invert board value.
			allowed_time = yield (MAX_BOARD_VALUE - max(schedule_chances))
			#opportunities += 1
			start_time = time.monotonic()



def decay_evaluator(fen):
	known_boards[fen].time_since_last_update += 1
	if known_boards[fen].time_since_last_update == 3:
		del known_boards[fen]
		return True
	return False
def deprecate_evaluator(board,fen):
	if len(board.piece_map()) < len(known_boards[fen].board.piece_map()):
		known_boards[fen]
		return True
	return False
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
	visited = [0] * numPossibleMoves
	# Update future boards lottery registry using "eyeing it" values. We don't need this, but keeping it in sync locally reduces amount of work for a refresh of chances.
	schedule_chances = [b.value for b in future_boards]
	# Keep doing this until we're out of time
	elapsed_time = time.monotonic()-start_time
	max_allowed_time = allowed_time/(numPossibleMoves)
	while elapsed_time < allowed_time or schedule_chances.index(max(schedule_chances)) != visited.index(max(visited)):
	#while elapsed_time < allowed_time:
		# This is likely the most expensive one-liner in the whole program.
		if random.random() > 0.5:
			chosenBoardIndex = numpy.random.choice(range(numPossibleMoves),p=numpy.divide(schedule_chances,sum(schedule_chances)))
		else:
			chosenBoardIndex = schedule_chances.index(max(schedule_chances))
		max_value = max(schedule_chances)
		#print("Highest value move is currently ",list(board.legal_moves)[schedule_chances.index(max_value)])
		#print("With a score of ",max_value)
		#print("Evaluating ",list(board.legal_moves)[chosenBoardIndex])
		#print("Which has calculated value ", schedule_chances[chosenBoardIndex])
		# Update lottery registry by giving that board position some computation time to calculate a better value.
		visited[chosenBoardIndex] += 1
		schedule_chances[chosenBoardIndex] = future_boards[chosenBoardIndex].update(min(max_allowed_time,allowed_time - elapsed_time))
		#print("Now has calculated value ", schedule_chances[chosenBoardIndex])
		elapsed_time = time.monotonic()-start_time
	#for i in range(len(schedule_chances)):
	#	print("Move: " + str(list(board.legal_moves)[i]) + "; Value: " + str(schedule_chances[i]) + "; Runs: ",future_boards[i].runs)
	return list(board.legal_moves)[schedule_chances.index(max(schedule_chances))]



# Initialization stuff

# Assigning arbitrary weights to these functions based on guess work. If I felt like spending time making a harness along with some light
# machine learning work, I could customize these parameters programmatically to find just how valuable these different aspects of a board are relative to each other.
base_case_board_value_funcs.append((calculateMaterialValue,8))
base_case_board_value_funcs.append((calculateSpaceValue,1))

class StockShrimpUCI(uci_client.UciClient):
	def __init__(self):
		super().__init__(name='stockshrimp',author='roguebantha')
	def new_game(self):
		self.board = chess.Board()
		# Erase EVERYTHING.
		known_boards = {}
	def genmove(self,tokens):
		#print(tokens)
		start_time = time.monotonic()
		move = calculateMove(self.board,14)
		uci_client.log("Length of time was ", time.monotonic() - start_time)
		print("bestmove %s\n"%move)
	def move(self,move):
		self.board.push(move)
		keys = list(known_boards.keys())
		for key in keys:
			if not decay_evaluator(key):
				deprecate_evaluator(self.board,key)
if __name__ == '__main__':
	StockShrimpUCI().main_loop()
	board = chess.Board("r1b1kbnr/1pp1p3/2nq2pp/pB1pNp1Q/P7/2N1P3/1PPP1PPP/R1B1K2R w KQkq - 0 9")
	move = calculateMove(board,8)
	print(move)
