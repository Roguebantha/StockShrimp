#!/usr/bin/env python3
#MIT license from https://github.com/rajpurkar/chess-deep-rl/blob/581c9cba6a4688ecbdaa776dac11c84bc1704d76/play.py
#Minor improvements and bugfixes by by jeffguy

import chess
import chess.uci
import chess.pgn
import argparse,datetime,os,sys

def get_filename(log_folder,round_num):
    return '%s/%06d.pgn'%(log_folder,round_num)

WHITE=0
BLACK=1

def configure_engines(*engine_paths):
    print(engine_paths)
    # Load engines
    engines=[chess.uci.popen_engine(path.split()) for path in engine_paths]
    for e,p in zip(engines,engine_paths):
        e.path=p
    plural='s' if len(engines)>1 else ''
    print('Loaded engine%s'%plural)

    # Initialize engines
    commands=[e.uci(async_callback=True) for e in engines]
    for c in commands:
        c.result()
    print('Initialized engine%s'%plural)

    for engine in engines:
        if engine.path=='stockfish':
            engine.setoption({'Skill Level':'0'},async_callback=True).result()
    print('Options given')
    return engines

def main(engine_w, engine_b, log_folder, move_time, num_games, verbose):
    if not os.path.exists(log_folder):
        os.makedirs(log_folder)
    if engine_w is engine_b:
        engines=[engine_w]
    else:
        engines=[engine_w,engine_b]
    for round_num in range(num_games):
        # Create new game
        commands=[e.ucinewgame(async_callback=True) for e in engines]
        for c in commands:
            c.result()

        board=chess.Board()
        moves=[]
        #moves=('e2e3', 'g7g6', 'f1d3', 'b8a6', 'd3a6', 'c7c5', 'd1f3', 'g8f6')#mate coming
        #moves=('g1f3', 'e7e6', 'f3d4', 'd8g5', 'd4f3', 'g5d2', 'c1d2', 'b8a6', 'f3e5', 'b7b5', 'd2a5', 'f8e7', 'h1g1', 'd7d5', 'd1d4', 'e7f6', 'a5c3', 'f6e5', 'd4e5', 'f7f5', 'e5g7', 'g8f6', 'g7h8', 'f6g8', 'h8g8', 'e8d7', 'g8h7', 'd7e8', 'h7h5', 'e8e7', 'h5f3', 'c7c6', 'f3d3', 'b5b4', 'c3e5', 'e7e8', 'e5d4', 'a8b8', 'd4a7', 'b8b7', 'd3a6', 'b7a7', 'a6a7', 'e8d8', 'a7b6', 'd8e8', 'b6c6', 'c8d7', 'c6b7', 'e8d8', 'b7b4', 'f5f4', 'b4f4', 'd7e8', 'f4d6', 'd8c8', 'd6e6', 'c8d8', 'e6d5', 'e8d7', 'd5c4', 'd8e8', 'c4c7', 'd7f5', 'c7e5', 'e8f8')#draw coming
        #moves=('g1f3', 'e7e6', 'f3d4', 'd8g5', 'd4f3', 'g5d2', 'c1d2', 'b8a6', 'f3e5', 'b7b5', 'd2a5', 'f8e7', 'h1g1', 'd7d5', 'd1d4', 'e7f6', 'a5c3', 'f6e5', 'd4e5', 'f7f5', 'e5g7', 'g8f6', 'g7h8', 'f6g8', 'h8g8', 'e8d7', 'g8h7', 'd7e8', 'h7h5', 'e8e7', 'h5f3', 'c7c6', 'f3d3', 'b5b4', 'c3e5', 'e7e8', 'e5d4', 'a8b8', 'd4a7', 'b8b7', 'd3a6', 'b7a7', 'a6a7', 'e8d8', 'a7b6', 'd8e8', 'b6c6', 'c8d7', 'c6b7', 'e8d8', 'b7b4', 'f5f4', 'b4f4', 'd7e8', 'f4d6', 'd8c8', 'd6e6', 'c8d8', 'e6d5', 'e8d7', 'd5c4', 'd8e8', 'c4c7', 'd7f5', 'c7e5', 'e8f8', 'e5f5','f8e7','f5c8','e7d6','c8h8','d6e6','h8g8','e6f5','g8h8','f5g5','h8g8','g6h4')#forced mate
        #moves=('g1f3', 'e7e6', 'f3d4', 'd8g5', 'd4f3', 'g5d2', 'c1d2', 'b8a6', 'f3e5', 'b7b5', 'd2a5', 'f8e7', 'h1g1', 'd7d5', 'd1d4', 'e7f6', 'a5c3', 'f6e5', 'd4e5', 'f7f5', 'e5g7', 'g8f6', 'g7h8', 'f6g8', 'h8g8', 'e8d7', 'g8h7', 'd7e8', 'h7h5', 'e8e7', 'h5f3', 'c7c6', 'f3d3', 'b5b4', 'c3e5', 'e7e8', 'e5d4', 'a8b8', 'd4a7', 'b8b7', 'd3a6', 'b7a7', 'a6a7', 'e8d8', 'a7b6', 'd8e8', 'b6c6', 'c8d7', 'c6b7', 'e8d8', 'b7b4', 'f5f4', 'b4f4', 'd7e8', 'f4d6', 'd8c8', 'd6e6', 'c8d8', 'e6d5', 'e8d7', 'd5c4', 'd8e8', 'c4c7', 'd7f5', 'c7e5', 'e8f8', 'e5f5', 'f8e7', 'f5c8', 'e7d6', 'c8h8', 'd6e6', 'h8g8', 'e6f5', 'g8h8', 'f5g5', 'h8g8', 'g6h4', 'g8h8', 'g5f4', 'h8g8', 'f4e4', 'g8h8', 'e4f5', 'h8g8', 'f5e5', 'g8h8', 'e5d5', 'h8g8', 'd5c6', 'g8h8', 'c6c5', 'h8g8', 'c5b6', 'g8h8', 'b6a5', 'h8g8', 'a5b6', 'g8h8', 'b6a7', 'h8g8', 'a7a6', 'g8h8', 'a6a5', 'h8g8', 'a5b5', 'g8h8', 'b5c5', 'h8g8', 'c5b4', 'g8h8', 'b4a5', 'h8g8', 'a5b6', 'g8h8', 'b6b7', 'h8g8', 'b7a6', 'g8h8', 'a6a5', 'h8g8', 'a5b4')#draw?
        for move in moves:
            board.push(chess.Move.from_uci(move))
        num_moves=0
        result=None
        while True:
            # Play white
            try:
                command_w=engine_w.position(board, async_callback=True)
                command_w.result()
                command_w=engine_w.go(movetime=move_time, async_callback=True)
                move=command_w.result().bestmove
                if verbose:print('White %s'%move)
            except chess._engine.EngineTerminatedException:
                print('White terminated')
                sys.exit(1)
            if move is None:
                winner='Black'
                print('\nBlack wins by resignation!')
                result='0-1'
                break
            board.push(move)
            result=board.result()
            if result != '*':
                if result == '1/2-1/2':
                    winner='Draw'
                    print('\nDraw')
                else:
                    winner='White'
                    print('\nWhite wins!')
                break
            #TODO: Send command_w the position command so it knows the move was made.

            # Play black
            try:
                command_b=engine_b.position(board, async_callback=True)
                command_b.result()
                command_b=engine_b.go(movetime=move_time, async_callback=True)
                move=command_b.result().bestmove
                if verbose:print('Black %s'%move)
            except chess._engine.EngineTerminatedException:
                print('Black terminated')
                sys.exit(1)
            if move is None:
                winner='White'
                print('\nWhite wins by resignation!')
                result='1-0'
                break
            board.push(move)
            result=board.result()
            if result != '*':
                if result == '1/2-1/2':
                    winner='Draw'
                    print('\nDraw')
                else:
                    winner='Black'
                    print('\nBlack wins!')
                break

            num_moves += 1

            if verbose:
                print()
                print(board)

        if verbose:
            print()
            print(board)

        if log_folder!='/dev/null':
            try:
                pgn=chess.pgn.Game.from_board(board)
                pgn.headers['White']=engine_w.path
                pgn.headers['Black']=engine_b.path
                pgn.headers['Date']=datetime.datetime.now().strftime('%Y.%m.%d %H:%M:%S')
                pgn.headers['Round']=str(round_num)
                if result is not None:
                    pgn.headers['Result']=result
                with open(get_filename(log_folder,round_num),'w',encoding='utf-8') as f:
                    pgn.accept(chess.pgn.FileExporter(f))
            except RecursionError:
                move_list=[]
                try:
                    while True:
                        move_list.append(board.pop())
                except IndexError:
                    pass
                move_list=move_list[::-1]
                with open(get_filename(log_folder,round_num),'w',encoding='utf-8') as f:
                    for move in move_list:
                        f.write(repr(move)+'\n')
        print('Number of moves: %d' % num_moves)
        sys.stdout.flush()
        for engine in engines:
            with engine.semaphore:
                engine.send_line("winner "+winner)

if __name__ == '__main__':
    parser=argparse.ArgumentParser(usage='''usage: server.py [-h] [-t T] [-n N] [-v V] [--self-play] --white white_engine_command --black [black_engine_command]

Example:
./server.py -t 100 -n 1 --white './random_bot.py --exhibition' --black './material_value_bot.py --exhibition'
./server.py -t 100 -n 1 --self-play './random_bot.py --exhibition'

Error:''')
    parser.add_argument('--white')
    parser.add_argument('--black')
    parser.add_argument('--self-play')
    parser.add_argument('--log-folder', type=str, default='/dev/null')
    parser.add_argument('-t', type=int, default=20, help='Time to move in milliseconds. Default: 20ms')
    parser.add_argument('-n', type=int, default=1, help='Number of games to play. Default: 1')
    parser.add_argument('-v', type=int, default=0, help='Verbosity level')
    args=parser.parse_args()
    if os.path.exists(get_filename(args.log_folder,args.n-1)):
        print('Those game records already exist. To generate new ones, point at a different folder, rename the old folder, or delete the old game records.')
        sys.exit(1)
    if args.self_play:
        if args.black is not None or args.white is not None:
            print('In self-play, cannot specify --white or --black.')
            sys.exit(1)
        engine=configure_engines(args.self_play)[0]
        main(engine, engine, args.log_folder, args.t, args.n, args.v)
    elif args.black is None or args.white is None:
        print("If you don't use --self-play, you must specify both --white and --black")
        sys.exit(1)
    else:
        white_engine,black_engine=configure_engines(args.white,args.black)
        main(white_engine, black_engine, args.log_folder, args.t, args.n, args.v)
