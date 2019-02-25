import chess,sys
from abc import abstractmethod

def log(*args,**kwargs):
    if 'str' in kwargs:
        sys.stderr.write('%s\n'%args[0])
    else:
        sys.stderr.write('%s\n'%','.join(map(repr,args)))

class UciClient:
    def __init__(self,name,author,debug=False):
        self.name=name
        self.author=author
        self.debug=debug
        self._new_game()
    @abstractmethod
    def new_game(self):
        raise NotImplemented()
    @abstractmethod
    def genmove(self,tokens):
        raise NotImplemented()
    @abstractmethod
    def move(self,move):
        raise NotImplemented()
    def game_finished(self,winner):
        pass
    def _new_game(self):
        self.last_position=[]
        self.new_game()
    def _is_continuation_of_game(self,tokens):
        return (len(tokens)==1 and len(self.last_position)==0) or\
            (len(tokens)>2 and tokens[1]=='moves' and tokens[2:2+len(self.last_position)]==self.last_position)
    def _position(self,tokens):
        if self.debug:log(tokens)
        if tokens[0]!='startpos':
            raise NotImplemented('When "position" command is given, I only understand the style that has arg0="startpos"')
        if self._is_continuation_of_game(tokens):
            if self.debug:log('is_continuation')
            new_moves=tokens[2+len(self.last_position):]
            self.last_position=tokens[2:]
        else:
            self._new_game()
            if len(tokens)==1:
                if self.debug:log('empty moves')
                new_moves=[]
                self.last_position=[]
            elif tokens[1]!='moves':
                raise NotImplemented('When "position" command is given, and len(argv)>1, I only understand the style that has arg1="moves"')
            else:
                if self.debug:log('not empty moves')
                new_moves=tokens[2:]
                self.last_position=tokens[2:]
        for move in new_moves:
            move=chess.Move.from_uci(move)
            self.move(move)
    def main_loop(self):
        while True:
            try:
                line=input()
            except EOFError:
                return
            if line.startswith('position '):
                self._position(line.split()[1:])
            elif line.startswith('go '):
                self.genmove(line.split()[1:])
            elif line.startswith('winner '):
                self.game_finished(line.split(' ',1)[1])
            elif line=='uci':
                print('id name',self.name)
                print('id author',self.author)
                print('uciok')
            elif line=='ucinewgame':
                self._new_game()
            elif line=='isready':
                print('readyok')
            else:
                sys.stderr.write('unrecognized command:%s\n'%repr(line))
                sys.exit(0)
