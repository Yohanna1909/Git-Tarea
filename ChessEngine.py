"""
Almacenar toda la información sobre el estado actual del juego de ajedrez.
Determinar movimientos válidos en el estado actual.
Mantendrá el registro de movimientos.
"""


class GameState:
    def __init__(self):
        """
        El tablero es una lista 2d de 8x8, cada elemento de la lista tiene 2 caracteres.
         El primer carácter representa el color de la pieza: 'b' o 'w'.
         El segundo carácter representa el tipo de pieza: 'R', 'N', 'B', 'Q', 'K' o 'p'.
         "--" representa un espacio vacío sin pieza.
        """
        self.board = [
            ["bR", "bN", "bB", "bQ", "bK", "bB", "bN", "bR"],
            ["bp", "bp", "bp", "bp", "bp", "bp", "bp", "bp"],
            ["--", "--", "--", "--", "--", "--", "--", "--"],
            ["--", "--", "--", "--", "--", "--", "--", "--"],
            ["--", "--", "--", "--", "--", "--", "--", "--"],
            ["--", "--", "--", "--", "--", "--", "--", "--"],
            ["wp", "wp", "wp", "wp", "wp", "wp", "wp", "wp"],
            ["wR", "wN", "wB", "wQ", "wK", "wB", "wN", "wR"]]
        self.moveFunctions = {"p": self.getPeonMoves, "R": self.getTorreMoves, "N": self.getCaballoMoves,
                              "B": self.getAlfilMoves, "Q": self.getReinaMovimientos, "K": self.getReyMovimientos}
        self.white_to_move = True
        self.move_log = []
        self.white_king_location = (7, 4)
        self.black_king_location = (0, 4)
        self.checkmate = False
        self.stalemate = False
        self.in_check = False
        self.pins = []
        self.checks = []
        self.enpassant_possible = ()  # coordenadas de la plaza donde es posible la captura al pasar
        self.enpassant_possible_log = [self.enpassant_possible]
        self.current_castling_rights = Enroque(True, True, True, True)
        self.castle_rights_log = [Enroque(self.current_castling_rights.wks, self.current_castling_rights.bks,
                                               self.current_castling_rights.wqs, self.current_castling_rights.bqs)]

    def makeMove(self, move):
        """
        Toma un Movovimiento como parámetro y lo ejecuta.
        (esto no funcionará para enroque, promoción de peón y al paso)
        """
        self.board[move.start_row][move.start_col] = "--"
        self.board[move.end_row][move.end_col] = move.piece_moved
        self.move_log.append(move)  # registrar el movimiento para que podamos deshacerlo más tarde
        self.white_to_move = not self.white_to_move  # cambiar jugadores
        # actualizar la ubicación del rey si se mueve
        if move.piece_moved == "wK":
            self.white_king_location = (move.end_row, move.end_col)
        elif move.piece_moved == "bK":
            self.black_king_location = (move.end_row, move.end_col)

        # promoción de empeño
        if move.is_pawn_promotion:
            # if not is_AI:
            #    promoted_piece = input("Promote to Q, R, B, or N:") #take this to UI later
            #    self.board[move.end_row][move.end_col] = move.piece_moved[0] + promoted_piece
            # else:
            self.board[move.end_row][move.end_col] = move.piece_moved[0] + "Q"

        # movimiento de paso
        if move.is_enpassant_move:
            self.board[move.start_row][move.end_col] = "--"  # capturando el peón

        # actualizar al paso posible variable
        if move.piece_moved[1] == "p" and abs(move.start_row - move.end_row) == 2:  # solo en avance de peón de 2 casillas
            self.enpassant_possible = ((move.start_row + move.end_row) // 2, move.start_col)
        else:
            self.enpassant_possible = ()

        # movimiento del castillo
        if move.is_castle_move:
            if move.end_col - move.start_col == 2:  # movimiento del castillo del lado del rey
                self.board[move.end_row][move.end_col - 1] = self.board[move.end_row][
                    move.end_col + 1]  # mueve la torre a su nueva casilla
                self.board[move.end_row][move.end_col + 1] = '--'  # borrar torre vieja
            else:  # movimiento del castillo del lado de la dama
                self.board[move.end_row][move.end_col + 1] = self.board[move.end_row][
                    move.end_col - 2]  # mueve la torre a su nueva casilla
                self.board[move.end_row][move.end_col - 2] = '--'  # borrar torre vieja

        self.enpassant_possible_log.append(self.enpassant_possible)

        # actualizar los derechos de enroque - siempre que sea un movimiento de torre y rey
        self.updateCastleRights(move)
        self.castle_rights_log.append(Enroque(self.current_castling_rights.wks, self.current_castling_rights.bks,
                                                   self.current_castling_rights.wqs, self.current_castling_rights.bqs))

    def undoMove(self):
        """
       Deshacer el último movimiento
        """
        if len(self.move_log) != 0:  # asegúrese de que haya un movimiento para deshacer
            move = self.move_log.pop()
            self.board[move.start_row][move.start_col] = move.piece_moved
            self.board[move.end_row][move.end_col] = move.piece_captured
            self.white_to_move = not self.white_to_move  # Intercambiar jugadores
            # actualizar la posición del rey si es necesario
            if move.piece_moved == "wK":
                self.white_king_location = (move.start_row, move.start_col)
            elif move.piece_moved == "bK":
                self.black_king_location = (move.start_row, move.start_col)
            # deshacer movimiento al paso
            if move.is_enpassant_move:
                self.board[move.end_row][move.end_col] = "--"  # dejar el recuadro de aterrizaje en blanco
                self.board[move.start_row][move.end_col] = move.piece_captured

            self.enpassant_possible_log.pop()
            self.enpassant_possible = self.enpassant_possible_log[-1]

            # deshacer los derechos del castillo
            self.castle_rights_log.pop()  # deshacerse de los derechos del nuevo castillo del movimiento que estamos deshaciendo
            self.current_castling_rights = self.castle_rights_log[
                -1]  # establecer los derechos actuales del castillo al último de la lista
            # deshacer el movimiento del castillo
            if move.is_castle_move:
                if move.end_col - move.start_col == 2:  # lado rey
                    self.board[move.end_row][move.end_col + 1] = self.board[move.end_row][move.end_col - 1]
                    self.board[move.end_row][move.end_col - 1] = '--'
                else:  # lado reina
                    self.board[move.end_row][move.end_col - 2] = self.board[move.end_row][move.end_col + 1]
                    self.board[move.end_row][move.end_col + 1] = '--'
            self.checkmate = False
            self.stalemate = False

    def updateCastleRights(self, move):
        """
        Update the castle rights given the move
        """
        if move.piece_captured == "wR":
            if move.end_col == 0:  # torre izquierda
                self.current_castling_rights.wqs = False
            elif move.end_col == 7:  # right rook
                self.current_castling_rights.wks = False
        elif move.piece_captured == "bR":
            if move.end_col == 0:  # torre izquierda
                self.current_castling_rights.bqs = False
            elif move.end_col == 7:  # torre derecha
                self.current_castling_rights.bks = False

        if move.piece_moved == 'wK':
            self.current_castling_rights.wqs = False
            self.current_castling_rights.wks = False
        elif move.piece_moved == 'bK':
            self.current_castling_rights.bqs = False
            self.current_castling_rights.bks = False
        elif move.piece_moved == 'wR':
            if move.start_row == 7:
                if move.start_col == 0:  # torre izquierda
                    self.current_castling_rights.wqs = False
                elif move.start_col == 7:  # torre derecha
                    self.current_castling_rights.wks = False
        elif move.piece_moved == 'bR':
            if move.start_row == 0:
                if move.start_col == 0:  # torre izquierda
                    self.current_castling_rights.bqs = False
                elif move.start_col == 7:  # torre derecha
                    self.current_castling_rights.bks = False

    def getValidMoves(self):
        """
        All moves considering checks.
        """
        temp_castle_rights = Enroque(self.current_castling_rights.wks, self.current_castling_rights.bks,
                                          self.current_castling_rights.wqs, self.current_castling_rights.bqs)
        # algoritmo avanzado
        moves = []
        self.in_check, self.pins, self.checks = self.checkForPinsAndChecks()

        if self.white_to_move:
            king_row = self.white_king_location[0]
            king_col = self.white_king_location[1]
        else:
            king_row = self.black_king_location[0]
            king_col = self.black_king_location[1]
        if self.in_check:
            if len(self.checks) == 1:  # solo 1 jaque, bloquee el jaque o mueva el rey
                moves = self.getTodosPosiblesMovimientos()
                # para bloquear el jaque debes poner una pieza en una de las casillas entre la pieza enemiga y tu rey
                check = self.checks[0]  # comprobar información
                check_row = check[0]
                check_col = check[1]
                piece_checking = self.board[check_row][check_col]
                valid_squares = []  # casillas a las que se pueden mover las piezas
                # si es caballo, debe capturar el caballo o mover su rey, otras piezas pueden ser bloqueadas
                if piece_checking[1] == "N":
                    valid_squares = [(check_row, check_col)]
                else:
                    for i in range(1, 8):
                        valid_square = (king_row + check[2] * i,
                                        king_col + check[3] * i)  # check[2] y check[3] son ​​las direcciones de verificación
                        valid_squares.append(valid_square)
                        if valid_square[0] == check_row and valid_square[
                            1] == check_col:  # una vez que llegas a la pieza y compruebas
                            break
                # deshazte de cualquier movimiento que no bloquee el jaque o mueva al rey
                for i in range(len(moves) - 1, -1, -1):  # iterar a través de la lista hacia atrás al eliminar elementos
                    if moves[i].piece_moved[1] != "K":  # mover no mueve al rey, por lo que debe bloquear o capturar
                        if not (moves[i].end_row,
                                moves[i].end_col) in valid_squares:  # el movimiento no bloquea ni captura la pieza
                            moves.remove(moves[i])
            else:  # verifica dos veces, el rey tiene que moverse
                self.getReyMovimientos(king_row, king_col, moves)
        else:  # no bajo control - todos los movimientos están bien
            moves = self.getTodosPosiblesMovimientos()
            if self.white_to_move:
                self.getCastleMoves(self.white_king_location[0], self.white_king_location[1], moves)
            else:
                self.getCastleMoves(self.black_king_location[0], self.black_king_location[1], moves)

        if len(moves) == 0:
            if self.inCheck():
                self.checkmate = True
            else:
                # TODO estancamiento en movimientos repetidos
                self.stalemate = True
        else:
            self.checkmate = False
            self.stalemate = False

        self.current_castling_rights = temp_castle_rights
        return moves

    def inCheck(self):
        """
        Determinar si un jugador actual está en jaque
        """
        if self.white_to_move:
            return self.PiezaBajoAtaque(self.white_king_location[0], self.white_king_location[1])
        else:
            return self.PiezaBajoAtaque(self.black_king_location[0], self.black_king_location[1])

    def PiezaBajoAtaque(self, row, col):
        """
        Determina las casillas atacadas por el enemigo
        """
        self.white_to_move = not self.white_to_move  # cambiar al punto de vista del oponente
        opponents_moves = self.getTodosPosiblesMovimientos()
        self.white_to_move = not self.white_to_move
        for move in opponents_moves:
            if move.end_row == row and move.end_col == col:  # la plaza está bajo ataque
                return True
        return False

    def getTodosPosiblesMovimientos(self):
        """
        Muestra los posibles movimientos a realizar
        """
        moves = []
        for row in range(len(self.board)):
            for col in range(len(self.board[row])):
                turn = self.board[row][col][0]
                if (turn == "w" and self.white_to_move) or (turn == "b" and not self.white_to_move):
                    piece = self.board[row][col][1]
                    self.moveFunctions[piece](row, col, moves)  # llama a la función de movimiento apropiada según el tipo de pieza
        return moves

    def checkForPinsAndChecks(self):
        pins = []  # cuadrados anclados y la dirección desde la que están anclados
        checks = []  # cuadrados anclados y la dirección desde la que están anclados
        in_check = False
        if self.white_to_move:
            enemy_color = "b"
            ally_color = "w"
            start_row = self.white_king_location[0]
            start_col = self.white_king_location[1]
        else:
            enemy_color = "w"
            ally_color = "b"
            start_row = self.black_king_location[0]
            start_col = self.black_king_location[1]
        # busque pines y cheques hacia afuera del rey, realice un seguimiento de los pines
        directions = ((-1, 0), (0, -1), (1, 0), (0, 1), (-1, -1), (-1, 1), (1, -1), (1, 1))
        for j in range(len(directions)):
            direction = directions[j]
            possible_pin = ()  # restablecer posibles pines
            for i in range(1, 8):
                end_row = start_row + direction[0] * i
                end_col = start_col + direction[1] * i
                if 0 <= end_row <= 7 and 0 <= end_col <= 7:
                    end_piece = self.board[end_row][end_col]
                    if end_piece[0] == ally_color and end_piece[1] != "K":
                        if possible_pin == ():  # la primera pieza aliada podría ser clavada
                            possible_pin = (end_row, end_col, direction[0], direction[1])
                        else:  # 2da pieza aliada - sin cheque ni alfiler desde esta dirección
                            break
                    elif end_piece[0] == enemy_color:
                        enemy_type = end_piece[1]
                        #5 posibilidades en este condicional complejo
                        # 1.) ortogonalmente lejos del rey y la pieza es una torre
                        # 2.) en diagonal lejos del rey y la pieza es un alfil
                        # 3.) 1 casilla de distancia en diagonal desde el rey y la pieza es un peón
                        # 4.) cualquier dirección y pieza es una reina
                        # 5.) cualquier dirección a 1 casilla de distancia y la pieza es un rey
                        if (0 <= j <= 3 and enemy_type == "R") or (4 <= j <= 7 and enemy_type == "B") or (
                                i == 1 and enemy_type == "p" and (
                                (enemy_color == "w" and 6 <= j <= 7) or (enemy_color == "b" and 4 <= j <= 5))) or (
                                enemy_type == "Q") or (i == 1 and enemy_type == "K"):
                            if possible_pin == ():  # sin bloqueo de piezas, así que comprueba
                                in_check = True
                                checks.append((end_row, end_col, direction[0], direction[1]))
                                break
                            else:  # pieza de bloqueo para pin
                                pins.append(possible_pin)
                                break
                        else:  # pieza enemiga que no aplica jaques
                            break
                else:
                    break  # fuera de borda
        # verifique los cheques de caballero
        knight_moves = ((-2, -1), (-2, 1), (-1, 2), (1, 2), (2, -1), (2, 1), (-1, -2), (1, -2))
        for move in knight_moves:
            end_row = start_row + move[0]
            end_col = start_col + move[1]
            if 0 <= end_row <= 7 and 0 <= end_col <= 7:
                end_piece = self.board[end_row][end_col]
                if end_piece[0] == enemy_color and end_piece[1] == "N":  # caballero enemigo atacando a un rey
                    in_check = True
                    checks.append((end_row, end_col, move[0], move[1]))
        return in_check, pins, checks

    def getPeonMoves(self, row, col, moves):
        """
        Obtenga todos los movimientos de peón para el peón ubicado en fila, columna y agregue los movimientos a la lista.
        """
        piece_pinned = False
        pin_direction = ()
        for i in range(len(self.pins) - 1, -1, -1):
            if self.pins[i][0] == row and self.pins[i][1] == col:
                piece_pinned = True
                pin_direction = (self.pins[i][2], self.pins[i][3])
                self.pins.remove(self.pins[i])
                break

        if self.white_to_move:
            move_amount = -1
            start_row = 6
            enemy_color = "b"
            king_row, king_col = self.white_king_location
        else:
            move_amount = 1
            start_row = 1
            enemy_color = "w"
            king_row, king_col = self.black_king_location

        if self.board[row + move_amount][col] == "--":  # 1 avance de peón cuadrado
            if not piece_pinned or pin_direction == (move_amount, 0):
                moves.append(Movimientos((row, col), (row + move_amount, col), self.board))
                if row == start_row and self.board[row + 2 * move_amount][col] == "--":  # 2 avance de peón cuadrado
                    moves.append(Movimientos((row, col), (row + 2 * move_amount, col), self.board))
        if col - 1 >= 0:  # capturar a la izquierda
            if not piece_pinned or pin_direction == (move_amount, -1):
                if self.board[row + move_amount][col - 1][0] == enemy_color:
                    moves.append(Movimientos((row, col), (row + move_amount, col - 1), self.board))
                if (row + move_amount, col - 1) == self.enpassant_possible:
                    attacking_piece = blocking_piece = False
                    if king_row == row:
                        if king_col < col:  # el rey queda del peón
                            # adentro: entre el rey y el peón;
                            # exterior: entre peón y borde;
                            inside_range = range(king_col + 1, col - 1)
                            outside_range = range(col + 1, 8)
                        else:  # rey a la derecha del peón
                            inside_range = range(king_col - 1, col, -1)
                            outside_range = range(col - 2, -1, -1)
                        for i in inside_range:
                            if self.board[row][i] != "--":  # alguna pieza al lado de bloques de peón al paso
                                blocking_piece = True
                        for i in outside_range:
                            square = self.board[row][i]
                            if square[0] == enemy_color and (square[1] == "R" or square[1] == "Q"):
                                attacking_piece = True
                            elif square != "--":
                                blocking_piece = True
                    if not attacking_piece or blocking_piece:
                        moves.append(Movimientos((row, col), (row + move_amount, col - 1), self.board, is_enpassant_move=True))
        if col + 1 <= 7:  # capturar a la derecha
            if not piece_pinned or pin_direction == (move_amount, +1):
                if self.board[row + move_amount][col + 1][0] == enemy_color:
                    moves.append(Movimientos((row, col), (row + move_amount, col + 1), self.board))
                if (row + move_amount, col + 1) == self.enpassant_possible:
                    attacking_piece = blocking_piece = False
                    if king_row == row:
                        if king_col < col:  # el rey queda del peón
                            # adentro: entre el rey y el peón;
                            # exterior: entre peón y borde;
                            inside_range = range(king_col + 1, col)
                            outside_range = range(col + 2, 8)
                        else:  # king right of the pawn
                            inside_range = range(king_col - 1, col + 1, -1)
                            outside_range = range(col - 1, -1, -1)
                        for i in inside_range:
                            if self.board[row][i] != "--":  # alguna pieza al lado de bloques de peón al paso
                                blocking_piece = True
                        for i in outside_range:
                            square = self.board[row][i]
                            if square[0] == enemy_color and (square[1] == "R" or square[1] == "Q"):
                                attacking_piece = True
                            elif square != "--":
                                blocking_piece = True
                    if not attacking_piece or blocking_piece:
                        moves.append(Movimientos((row, col), (row + move_amount, col + 1), self.board, is_enpassant_move=True))

    def getTorreMoves(self, row, col, moves):
        """
        Obtenga todos los movimientos de torre para la torre ubicada en fila, columna y agregue los movimientos a la lista.
        """
        piece_pinned = False
        pin_direction = ()
        for i in range(len(self.pins) - 1, -1, -1):
            if self.pins[i][0] == row and self.pins[i][1] == col:
                piece_pinned = True
                pin_direction = (self.pins[i][2], self.pins[i][3])
                if self.board[row][col][
                    1] != "Q":  # no se puede quitar la dama de la clavada en los movimientos de la torre, solo se puede quitar en los movimientos del alfil
                    self.pins.remove(self.pins[i])
                break

        directions = ((-1, 0), (0, -1), (1, 0), (0, 1))  # arriba, izquierda, abajo, derecha
        enemy_color = "b" if self.white_to_move else "w"
        for direction in directions:
            for i in range(1, 8):
                end_row = row + direction[0] * i
                end_col = col + direction[1] * i
                if 0 <= end_row <= 7 and 0 <= end_col <= 7:  # verificar posibles movimientos solo en los límites del tablero
                    if not piece_pinned or pin_direction == direction or pin_direction == (
                            -direction[0], -direction[1]):
                        end_piece = self.board[end_row][end_col]
                        if end_piece == "--":  # el espacio vacio es valido
                            moves.append(Movimientos((row, col), (end_row, end_col), self.board))
                        elif end_piece[0] == enemy_color:  # capturar pieza enemiga
                            moves.append(Movimientos((row, col), (end_row, end_col), self.board))
                            break
                        else:  # pieza amistosa
                            break
                else:  # fuera de borda
                    break

    def getCaballoMoves(self, row, col, moves):
        """
        Obtenga todos los movimientos de caballo para el caballo ubicado en la fila col y agregue los movimientos a la lista.
        """
        piece_pinned = False
        for i in range(len(self.pins) - 1, -1, -1):
            if self.pins[i][0] == row and self.pins[i][1] == col:
                piece_pinned = True
                self.pins.remove(self.pins[i])
                break

        knight_moves = ((-2, -1), (-2, 1), (-1, 2), (1, 2), (2, -1), (2, 1), (-1, -2),
                        (1, -2))  # up/left up/right right/up right/down down/left down/right left/up left/down
        ally_color = "w" if self.white_to_move else "b"
        for move in knight_moves:
            end_row = row + move[0]
            end_col = col + move[1]
            if 0 <= end_row <= 7 and 0 <= end_col <= 7:
                if not piece_pinned:
                    end_piece = self.board[end_row][end_col]
                    if end_piece[0] != ally_color:  # entonces es una pieza enemiga o un cuadrado vacío
                        moves.append(Movimientos((row, col), (end_row, end_col), self.board))

    def getAlfilMoves(self, row, col, moves):
        """
        Obtenga todos los movimientos de alfil para el alfil ubicado en la fila col y agregue los movimientos a la lista.
        """
        piece_pinned = False
        pin_direction = ()
        for i in range(len(self.pins) - 1, -1, -1):
            if self.pins[i][0] == row and self.pins[i][1] == col:
                piece_pinned = True
                pin_direction = (self.pins[i][2], self.pins[i][3])
                self.pins.remove(self.pins[i])
                break

        directions = ((-1, -1), (-1, 1), (1, 1), (1, -1))  # diagonales: up/left up/right down/right down/left
        enemy_color = "b" if self.white_to_move else "w"
        for direction in directions:
            for i in range(1, 8):
                end_row = row + direction[0] * i
                end_col = col + direction[1] * i
                if 0 <= end_row <= 7 and 0 <= end_col <= 7:  # comprobar si el movimiento está a bordo
                    if not piece_pinned or pin_direction == direction or pin_direction == (
                            -direction[0], -direction[1]):
                        end_piece = self.board[end_row][end_col]
                        if end_piece == "--":  # el espacio vacio es valido
                            moves.append(Movimientos((row, col), (end_row, end_col), self.board))
                        elif end_piece[0] == enemy_color:  # capturar pieza enemiga
                            moves.append(Movimientos((row, col), (end_row, end_col), self.board))
                            break
                        else:  # pieza amistosa
                            break
                else:  # fuera de borda
                    break

    def getReinaMovimientos(self, row, col, moves):
        """
        Los movimientos de la reina es una convinacion de los alifiles y las torres
        """
        self.getAlfilMoves(row, col, moves)
        self.getTorreMoves(row, col, moves)

    def getReyMovimientos(self, row, col, moves):
        """
        Obtenga todos los movimientos del rey para el rey ubicado en la fila col y agregue los movimientos a la lista.
        """
        row_moves = (-1, -1, -1, 0, 0, 1, 1, 1)
        col_moves = (-1, 0, 1, -1, 1, -1, 0, 1)
        ally_color = "w" if self.white_to_move else "b"
        for i in range(8):
            end_row = row + row_moves[i]
            end_col = col + col_moves[i]
            if 0 <= end_row <= 7 and 0 <= end_col <= 7:
                end_piece = self.board[end_row][end_col]
                if end_piece[0] != ally_color:  # no es una pieza aliada - vacía o enemiga
                    # coloque el rey en el cuadrado final y verifique si hay cheques
                    if ally_color == "w":
                        self.white_king_location = (end_row, end_col)
                    else:
                        self.black_king_location = (end_row, end_col)
                    in_check, pins, checks = self.checkForPinsAndChecks()
                    if not in_check:
                        moves.append(Movimientos((row, col), (end_row, end_col), self.board))
                    # coloque el rey de nuevo en la ubicación original
                    if ally_color == "w":
                        self.white_king_location = (row, col)
                    else:
                        self.black_king_location = (row, col)

    def getCastleMoves(self, row, col, moves):
        """
        Genere todos los movimientos de castillo válidos para el rey en (fila, columna) y agréguelos a la lista de movimientos.
        """
        if self.PiezaBajoAtaque(row, col):
            return  # no se puede enrocar mientras está en jaque
        if (self.white_to_move and self.current_castling_rights.wks) or (
                not self.white_to_move and self.current_castling_rights.bks):
            self.getKingsideCastleMoves(row, col, moves)
        if (self.white_to_move and self.current_castling_rights.wqs) or (
                not self.white_to_move and self.current_castling_rights.bqs):
            self.getQueensideCastleMoves(row, col, moves)

    def getKingsideCastleMoves(self, row, col, moves):
        if self.board[row][col + 1] == '--' and self.board[row][col + 2] == '--':
            if not self.PiezaBajoAtaque(row, col + 1) and not self.PiezaBajoAtaque(row, col + 2):
                moves.append(Movimientos((row, col), (row, col + 2), self.board, is_castle_move=True))

    def getQueensideCastleMoves(self, row, col, moves):
        if self.board[row][col - 1] == '--' and self.board[row][col - 2] == '--' and self.board[row][col - 3] == '--':
            if not self.PiezaBajoAtaque(row, col - 1) and not self.PiezaBajoAtaque(row, col - 2):
                moves.append(Movimientos((row, col), (row, col - 2), self.board, is_castle_move=True))


class Enroque:
    def __init__(self, wks, bks, wqs, bqs):
        self.wks = wks
        self.bks = bks
        self.wqs = wqs
        self.bqs = bqs


class Movimientos:
    # en el ajedrez, los campos en el tablero se describen con dos símbolos, uno de ellos es un número entre 1-8 (que corresponde a las filas)
     # y la segunda es una letra entre a-f (correspondiente a las columnas), para usar esta notación necesitamos mapear nuestras coordenadas [row][col]
     # para que coincida con los utilizados en el juego de ajedrez original
    ranks_to_rows = {"1": 7, "2": 6, "3": 5, "4": 4,
                     "5": 3, "6": 2, "7": 1, "8": 0}
    rows_to_ranks = {v: k for k, v in ranks_to_rows.items()}
    files_to_cols = {"a": 0, "b": 1, "c": 2, "d": 3,
                     "e": 4, "f": 5, "g": 6, "h": 7}
    cols_to_files = {v: k for k, v in files_to_cols.items()}

    def __init__(self, start_square, end_square, board, is_enpassant_move=False, is_castle_move=False):
        self.start_row = start_square[0]
        self.start_col = start_square[1]
        self.end_row = end_square[0]
        self.end_col = end_square[1]
        self.piece_moved = board[self.start_row][self.start_col]
        self.piece_captured = board[self.end_row][self.end_col]
        # promoción de empeño
        self.is_pawn_promotion = (self.piece_moved == "wp" and self.end_row == 0) or (
                self.piece_moved == "bp" and self.end_row == 7)
        # de paso
        self.is_enpassant_move = is_enpassant_move
        if self.is_enpassant_move:
            self.piece_captured = "wp" if self.piece_moved == "bp" else "bp"
        # movimiento del castillo
        self.is_castle_move = is_castle_move

        self.is_capture = self.piece_captured != "--"
        self.moveID = self.start_row * 1000 + self.start_col * 100 + self.end_row * 10 + self.end_col

    def __eq__(self, other):
        """
        Anulando el método de igualdad.
        """
        if isinstance(other, Movimientos):
            return self.moveID == other.moveID
        return False

    def SistemaAnotarJugadas(self):
        if self.is_pawn_promotion:
            return self.PosicionPieza(self.end_row, self.end_col) + "Q"
        if self.is_castle_move:
            if self.end_col == 1:
                return "0-0-0"
            else:
                return "0-0"
        if self.is_enpassant_move:
            return self.PosicionPieza(self.start_row, self.start_col)[0] + "x" + self.PosicionPieza(self.end_row,
                                                                                                self.end_col) + " e.p."
        if self.piece_captured != "--":
            if self.piece_moved[1] == "p":
                return self.PosicionPieza(self.start_row, self.start_col)[0] + "x" + self.PosicionPieza(self.end_row,
                                                                                                    self.end_col)
            else:
                return self.piece_moved[1] + "x" + self.PosicionPieza(self.end_row, self.end_col)
        else:
            if self.piece_moved[1] == "p":
                return self.PosicionPieza(self.end_row, self.end_col)
            else:
                return self.piece_moved[1] + self.PosicionPieza(self.end_row, self.end_col)

        # TODO Eliminación de ambigüedades

    """
    El método "PosicionPieza" utiliza dos diccionarios previamente definidos
    ("cols_to_files" y "rows_to_ranks") para realizar la conversión de
    la posición de fila y columna a la Posicionde la pieza.
    """
    def PosicionPieza(self, row, col):
        return self.cols_to_files[col] + self.rows_to_ranks[row]

    def __str__(self):
        if self.is_castle_move:
            return "0-0" if self.end_col == 6 else "0-0-0"

        end_square = self.PosicionPieza(self.end_row, self.end_col)

        if self.piece_moved[1] == "p":
            if self.is_capture:
                return self.cols_to_files[self.start_col] + "x" + end_square
            else:
                return end_square + "Q" if self.is_pawn_promotion else end_square

        move_string = self.piece_moved[1]
        if self.is_capture:
            move_string += "x"
        return move_string + end_square
