import socket

import Config
import Utils


"""

HIT     : X
MISS    : -
SHIP    : 1
NOTHING : 0 / UNSEEN

"""

class Client(object):
    def __init__(self, board, host=False):
        # host is a boolean value for if you're a host
        self.host = host
        self.board = board
        self.config = Config.load()
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1) # debug

    def play(self):
        if self.host:
            self.take_turn()

        while not gameover:
            self.wait_response()
            if not gameover:
                self.take_turn()

    def take_turn(self):
        self.board.print(side_by_side=True)
        print("Take a shot at your opponent! e.g. '4 5' for a shot at (4, 5)")
        x = 0
        y = 0
        valid = False
        while not valid:
            choice = input("> ")
            split_choice = choice.strip().split(" ")
            if len(split_choice) == 2 and split_choice[0].isnumeric() and split_choice[1].isnumeric():
                x = int(split_choice[0])
                y = int(split_choice[1])
                if x in range(grid_size) and y in range(grid_size):
                    valid = True

        message = { 'coordinates': {'x': x, 'y': y } }
        print("Firing on ({0}, {1})!".format(x,y))
        self.send_data(Utils.jsencode(message))
        response = Utils.jsdecode(self.recv_data(1024))
        if response['response'] == 'HIT':
            print("HIT!")
            self.board.boards[1][y][x] = 'H'
        else:
            print("MISS!")
            self.board.boards[1][y][x] = '-'

    def send_data(self, message):
        if self.host:
            self.connection.send(message)

        else:
            self.sock.send(message)

    def recv_data(self, buffer=1024):
        if self.host:
            return self.connection.recv(buffer)
        else:
            return self.sock.recv(buffer)

    def wait_response(self):
        print("Waiting for your opponent to finish their turn!")
        data = self.recv_data(1024)
        response = Utils.jsdecode(data)
        coordinates = response['coordinates']
        x = coordinates['x']
        y = coordinates['y']
        if self.board.take_shot(x,y):
            hit_response = {'response': 'HIT'}
        else:
            hit_response = {'response': 'MISS'}
        self.send_data(Utils.jsencode(hit_response))

    def open_connection(self):
        self.sock.bind((self.config['address'], self.config['port']))
        print("Listening at {0} on port {1}".format(self.config['address'], self.config['port']))
        self.sock.listen(5)
        self.connection, self.address = self.sock.accept()
        print("User Connected from {0}".format(self.address))

    def connect_to_host(self, host, port):
        self.sock.connect((host, port))


class Board(object):
    def __init__(self, size):
        self.size = size
        self.boards = []
        self.ships = []
        board = []
        for _ in range(size):
            row = []
            for _ in range(size):
                row.append('0')
            board.append(row)
        self.boards.append(board) ## yours

        oppBoard = []
        for _ in range(size):
            row = []
            for _ in range(size):
                row.append('0')
            oppBoard.append(row)
        self.boards.append(oppBoard) ## your record of opponents

    def take_shot(self,x,y):
        if self.boards[0][y][x] == '1':
            self.boards[0][y][x] = 'H'
            return True
        else:
            self.boards[0][y][x] = '-'
            return False

    def place_ships(self):
        ships_to_place = [5,4,3,2,2,1,1] # lengths
        help = """Time to place your ships!
        Ships can be placed in the format
        x y length direction e,g. '5 4 4 N'
        where direction is either S or E in respect to compass directions
        This help can be displayed at any point during setup by typing '/help'"""
        print(help)
        while len(ships_to_place) > 0:
            print('*'*20)
            print("Ships left to place: {0}\n".format(','.join([str(x) for x in ships_to_place])))
            self.print()
            entry = input('> ')
            entry = entry.strip().split(' ')
            if entry[0] == '/help':
                print(help)
            elif len(entry) == 4 and (entry[0].isnumeric()  # X
                                 and  entry[1].isnumeric()  # Y
                                 and  entry[2].isnumeric()  # LENGTH
                                 and  entry[3].upper() in "SE")\
                                 and int(entry[2]) in ships_to_place: ## S OR E
                entry = (int(entry[0]), int(entry[1]), int(entry[2]), entry[3].upper())
                if self.check_placement(entry): # if valid
                    self.place_ship(entry)
                    ships_to_place.remove(entry[2])
                    print("Ship placed with coordinates: (".format("->".join([str(s) for s in self.ships])))
                else:
                    print("Invalid placement, Collision detected!")
            else:
                if int(entry[2]) not in ships_to_place:
                    print("You don't have any ships of this length to place!")
                else:
                    print("Invalid placement formatting!")

    def print(self, side_by_side=False):
        y = 0
        lines = []
        lines.append("  Your grid:" + (" "*((grid_size*2)-12)))
        lines.append("  " + " ".join([str(x) for x in range(grid_size)]))
        for row in self.boards[0]:
            lines.append(str(y) + " " + " ".join(row))
            y += 1
	y = 0
        if side_by_side:
            opponent = []
            opponent.append("  Opponent grid:" + (" "*((grid_size*2)-16)))
            opponent.append("  " + " ".join([str(x) for x in range(grid_size)]))
            for row in self.boards[1]:
                opponent.append(str(y) + " " + " ".join(row))
                y += 1
            lines = Utils.myJoin(opponent, lines, " "*10)
        print("\n")
        print("\n".join(lines))

    def place_ship(self, placement):
        x,y,length,direction = placement
        length = int(length)

        if direction == 'S':
            for ship_y in range(y,y+length):
                self.ships.append((x,ship_y))
                self.boards[0][ship_y][x] = '1'
        else:
            for ship_x in range(x, x + length):
                self.ships.append((ship_x, y))
                self.boards[0][y][ship_x] = '1'


    def check_placement(self, placement):
        x,y,length,direction = placement
        ## check the placement is valid
        counter = 0
        if direction == 'S':
            valid = y + length <= self.size and x < self.size
        else:
            valid = x + length <= self.size and y < self.size

        while valid and counter < length:
            if direction == 'S':
                valid = self.boards[0][y + counter][x] == '0'
            else:
                valid = self.boards[0][y][x + counter] == '0'
            counter += 1
        return valid






# ------------------------------ INIT ----------------------------- #
grid_size = 10

gameover = False

def setup_board():
    board = Board(grid_size)
    board.place_ships()
    return board

def setup_client(board):
    is_host = False
    choice = ""
    while choice is None or choice == "":
        choice = input("Do you want to host? ([y]/n): ")
        if choice is None or choice == "":
            is_host = True
            break

    if choice.lower() == 'y':
        is_host = True
    client = Client(board, is_host)
    ##  ------------------------------- INITAL CONNECTIONS -----------------------------------
    if not is_host:
        connected = False
        while not connected:
            host_ip   = input("Host IP: ")
            host_port = int(input("Port: "))

            try:
                client.connect_to_host(host_ip, host_port)
                connected = True
            except:
                print("An error occurred during the connection process!")
    else:
        print("Waiting for opponent...")
        client.open_connection()
    return client
    ## ----------------------------------- CONNECTED -------------------------------------------



 # -------------------------------------  GAME RUN AREA ---------------------------------------------
try:

    print("Welcome to Battleships!")
    board = setup_board()
    client = setup_client(board)
    client.play()

except KeyboardInterrupt:
    print("\nThanks for playing!")

