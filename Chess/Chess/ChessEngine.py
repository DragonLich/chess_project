"""
Хранение всей информации о текущем статусе игры
Определение возможных ходов
"""


class GameState:
    def __init__(self):
        """
        Доска - 8 на 8 двумерный массив, каждый элемент в котором состоит из двух букв.
        Первая буква отвечает за цвет, где b - black, w - white.
        Вторая буква отвечает за фигуру, R - Rook (ладья), N - Knight (конь), B - Bishop (слон),
        Q - Queen (ферзь), K - King (король).
        "--" обозначает пустую клетку.
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
        self.moveFunctions = {"p": self.getPawnMoves, "R": self.getRookMoves, "N": self.getKnightMoves,
                              "B": self.getBishopMoves, "Q": self.getQueenMoves, "K": self.getKingMoves}
        self.white_to_move = True # флаг, отвечающий за цвет текущего хода
        self.move_log = [] # сюда записываем ходы
        self.white_king_location = (7, 4) # локация белого короля
        self.black_king_location = (0, 4) # локация черного короля
        self.checkmate = False # мат
        self.stalemate = False # пат
        self.in_check = False # шах
        self.pins = [] # связки
        self.checks = [] # шахи
        self.enpassant_possible = ()  # координаты, где enpassant (взятие на проходе) возможен
        self.enpassant_possible_log = [self.enpassant_possible] # лог координат
        self.current_castling_rights = CastleRights(True, True, True, True) # права на рокировку
        self.castle_rights_log = [CastleRights(self.current_castling_rights.wks, self.current_castling_rights.bks,
                                               self.current_castling_rights.wqs, self.current_castling_rights.bqs)] # лог рокировок

    def makeMove(self, move):
        """
        Функция, отвечающая за ходы в игре
        """
        self.board[move.start_row][move.start_col] = "--"
        self.board[move.end_row][move.end_col] = move.piece_moved
        self.move_log.append(move)  # запоминаем ход, чтобы была возможность позже отменить его
        self.white_to_move = not self.white_to_move  # смена хода
        # обновление локации короля, если она изменилась
        if move.piece_moved == "wK":
            self.white_king_location = (move.end_row, move.end_col)
        elif move.piece_moved == "bK":
            self.black_king_location = (move.end_row, move.end_col)

        # превращение пешки (пока что только в ферзя)
        if move.is_pawn_promotion:
            self.board[move.end_row][move.end_col] = move.piece_moved[0] + "Q"

        # enpassant
        if move.is_enpassant_move:
            self.board[move.start_row][move.end_col] = "--"  # съесть пешку

        # обновление enpassant_possible
        if move.piece_moved[1] == "p" and abs(move.start_row - move.end_row) == 2:  # только если пешка прошла 2 клетки
            self.enpassant_possible = ((move.start_row + move.end_row) // 2, move.start_col)
        else:
            self.enpassant_possible = ()

        # рокировка (castling)
        if move.is_castle_move:
            if move.end_col - move.start_col == 2:  # сторона короля
                self.board[move.end_row][move.end_col - 1] = self.board[move.end_row][
                    move.end_col + 1]  # перемещает ладью на новую клетку
                self.board[move.end_row][move.end_col + 1] = '--'  # удаляем ладью
            else:  # сторона ферзя
                self.board[move.end_row][move.end_col + 1] = self.board[move.end_row][
                    move.end_col - 2]  # перемещает ладью на новую клетку
                self.board[move.end_row][move.end_col - 2] = '--'  # удаляем ладью

        self.enpassant_possible_log.append(self.enpassant_possible)

        # обновление возможности рокировки, если это ход короля или ладьи
        self.updateCastleRights(move)
        self.castle_rights_log.append(CastleRights(self.current_castling_rights.wks, self.current_castling_rights.bks,
                                                   self.current_castling_rights.wqs, self.current_castling_rights.bqs))

    def undoMove(self):
        """
        Отмена последнего хода
        """
        if len(self.move_log) != 0:  # удостоверимся, что есть ход, который можно отменить
            move = self.move_log.pop()
            self.board[move.start_row][move.start_col] = move.piece_moved
            self.board[move.end_row][move.end_col] = move.piece_captured
            self.white_to_move = not self.white_to_move  # смена игроков
            #
            if move.piece_moved == "wK":
                self.white_king_location = (move.start_row, move.start_col)
            elif move.piece_moved == "bK":
                self.black_king_location = (move.start_row, move.start_col)
            # отмена enpassant
            if move.is_enpassant_move:
                self.board[move.end_row][move.end_col] = "--"
                self.board[move.start_row][move.end_col] = move.piece_captured

            self.enpassant_possible_log.pop()
            self.enpassant_possible = self.enpassant_possible_log[-1]

            self.castle_rights_log.pop()  # убираем обновление статуса рокировки хода, который мы отменяем
            self.current_castling_rights = self.castle_rights_log[
                -1]  # возвращение статуса предыдущего хода
            # отмена рокировки
            if move.is_castle_move:
                if move.end_col - move.start_col == 2:  # сторона короля
                    self.board[move.end_row][move.end_col + 1] = self.board[move.end_row][move.end_col - 1]
                    self.board[move.end_row][move.end_col - 1] = '--'
                else:  # сторона ферзя
                    self.board[move.end_row][move.end_col - 2] = self.board[move.end_row][move.end_col + 1]
                    self.board[move.end_row][move.end_col + 1] = '--'
            self.checkmate = False
            self.stalemate = False

    def updateCastleRights(self, move):
        """
        Обновление статуса возможности рокировки
        """
        if move.piece_captured == "wR":
            if move.end_col == 0:  # левая лаья
                self.current_castling_rights.wqs = False
            elif move.end_col == 7:  # правая ладья
                self.current_castling_rights.wks = False
        elif move.piece_captured == "bR":
            if move.end_col == 0:  # левая ладья
                self.current_castling_rights.bqs = False
            elif move.end_col == 7:  # правая ладья
                self.current_castling_rights.bks = False

        if move.piece_moved == 'wK':
            self.current_castling_rights.wqs = False
            self.current_castling_rights.wks = False
        elif move.piece_moved == 'bK':
            self.current_castling_rights.bqs = False
            self.current_castling_rights.bks = False
        elif move.piece_moved == 'wR':
            if move.start_row == 7:
                if move.start_col == 0:  # левая ладья
                    self.current_castling_rights.wqs = False
                elif move.start_col == 7:  # правая ладья
                    self.current_castling_rights.wks = False
        elif move.piece_moved == 'bR':
            if move.start_row == 0:
                if move.start_col == 0:  # левая ладья
                    self.current_castling_rights.bqs = False
                elif move.start_col == 7:  # правая ладья
                    self.current_castling_rights.bks = False

    def getValidMoves(self):
        """
        Все ходы учитывая шах
        """
        temp_castle_rights = CastleRights(self.current_castling_rights.wks, self.current_castling_rights.bks,
                                          self.current_castling_rights.wqs, self.current_castling_rights.bqs)
        moves = []
        self.in_check, self.pins, self.checks = self.checkForPinsAndChecks()

        if self.white_to_move:
            king_row = self.white_king_location[0]
            king_col = self.white_king_location[1]
        else:
            king_row = self.black_king_location[0]
            king_col = self.black_king_location[1]
        if self.in_check:
            if len(self.checks) == 1:  # только 1 шах, блокировка или избегание
                moves = self.getAllPossibleMoves()
                # чтобы заблокировать шах, нужно поместить фигуру между ними
                check = self.checks[0]  # информация по шахам
                check_row = check[0]
                check_col = check[1]
                piece_checking = self.board[check_row][check_col]
                valid_squares = []  # squares that pieces can move to
                # если конь, то его нужно съесть либо увести фигуру
                if piece_checking[1] == "N":
                    valid_squares = [(check_row, check_col)]
                else:
                    for i in range(1, 8):
                        valid_square = (king_row + check[2] * i,
                                        king_col + check[3] * i)  # check[2] и check[3] направление шаха
                        valid_squares.append(valid_square)
                        if valid_square[0] == check_row and valid_square[
                            1] == check_col: # когда ты доходишь до фигуры и ставишь шах
                            break
                # избавляемся от всех ходов, что не убирают шах
                for i in range(len(moves) - 1, -1, -1):
                    if moves[i].piece_moved[1] != "K":  # если ходит не король, то это либо блок, либо съесть фигуру, которая ставит шах
                        if not (moves[i].end_row,
                                moves[i].end_col) in valid_squares:  # ход не блокирует или ест фигуру
                            moves.remove(moves[i])
            else:  # двойная проверка, король должен ходить
                self.getKingMoves(king_row, king_col, moves)
        else:  # нет шаха - все ходы в порядке
            moves = self.getAllPossibleMoves()
            if self.white_to_move:
                self.getCastleMoves(self.white_king_location[0], self.white_king_location[1], moves)
            else:
                self.getCastleMoves(self.black_king_location[0], self.black_king_location[1], moves)

        if len(moves) == 0:
            if self.inCheck():
                self.checkmate = True
            else:
                self.stalemate = True
        else:
            self.checkmate = False
            self.stalemate = False

        self.current_castling_rights = temp_castle_rights
        return moves

    def inCheck(self):
        """
        Проверка на то, есть ли шах у текущего игрока
        """
        if self.white_to_move:
            return self.squareUnderAttack(self.white_king_location[0], self.white_king_location[1])
        else:
            return self.squareUnderAttack(self.black_king_location[0], self.black_king_location[1])

    def squareUnderAttack(self, row, col):
        """
        Проверка на то, может ли атаковать эту клетку противник
        """
        self.white_to_move = not self.white_to_move  # смена на pov противника
        opponents_moves = self.getAllPossibleMoves()
        self.white_to_move = not self.white_to_move
        for move in opponents_moves:
            if move.end_row == row and move.end_col == col:  # клетка под атакой
                return True
        return False

    def getAllPossibleMoves(self):
        """
        Все ходы не учитывая шах
        """
        moves = []
        for row in range(len(self.board)):
            for col in range(len(self.board[row])):
                turn = self.board[row][col][0]
                if (turn == "w" and self.white_to_move) or (turn == "b" and not self.white_to_move):
                    piece = self.board[row][col][1]
                    self.moveFunctions[piece](row, col, moves)  # вызывает нужную функцию в зависимости от фигуры
        return moves

    def checkForPinsAndChecks(self):
        # pin - связка нападение дальнобойной фигуры (ферзя, ладьи, слона) на неприятельскую фигуру (или пешку)
        # за которой на линии нападения (линии связки) расположена другая неприятельская фигура
        # (равнозначная либо более ценная) или какой-либо важный пункт.
        pins = []
        checks = []
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
        directions = ((-1, 0), (0, -1), (1, 0), (0, 1), (-1, -1), (-1, 1), (1, -1), (1, 1))
        for j in range(len(directions)):
            direction = directions[j]
            possible_pin = ()  # обнуление возможных связок
            for i in range(1, 8):
                end_row = start_row + direction[0] * i
                end_col = start_col + direction[1] * i
                if 0 <= end_row <= 7 and 0 <= end_col <= 7:
                    end_piece = self.board[end_row][end_col]
                    if end_piece[0] == ally_color and end_piece[1] != "K":
                        if possible_pin == ():  # первая союзная фигура может быть в связке
                            possible_pin = (end_row, end_col, direction[0], direction[1])
                        else:  # 2я союзная фигура - нет связки или шаха
                            break
                    elif end_piece[0] == enemy_color:
                        enemy_type = end_piece[1]
                        # 5 возможных ситуация
                        # 1) горизонтально от короля и это ладья
                        # 2) диагонально от короля и это ферзь или слон
                        # 3) диагонально на 1 клетке от короле и это пешка
                        # 4) любое направление и фигура это ферзь
                        # 5) любое направление в радиусе 1 клетки и фигура это король
                        if (0 <= j <= 3 and enemy_type == "R") or (4 <= j <= 7 and enemy_type == "B") or (
                                i == 1 and enemy_type == "p" and (
                                (enemy_color == "w" and 6 <= j <= 7) or (enemy_color == "b" and 4 <= j <= 5))) or (
                                enemy_type == "Q") or (i == 1 and enemy_type == "K"):
                            if possible_pin == ():  # нет блокирующей фигуры, поэтому шах
                                in_check = True
                                checks.append((end_row, end_col, direction[0], direction[1]))
                                break
                            else:  # если есть фигура, то связка
                                pins.append(possible_pin)
                                break
                        else:  # вражеская фигура не ставит шах
                            break
                else:
                    break  # вне поля
        # проверка на шах от коня
        knight_moves = ((-2, -1), (-2, 1), (-1, 2), (1, 2), (2, -1), (2, 1), (-1, -2), (1, -2))
        for move in knight_moves:
            end_row = start_row + move[0]
            end_col = start_col + move[1]
            if 0 <= end_row <= 7 and 0 <= end_col <= 7:
                end_piece = self.board[end_row][end_col]
                if end_piece[0] == enemy_color and end_piece[1] == "N":  # вражеский конь атакует короля
                    in_check = True
                    checks.append((end_row, end_col, move[0], move[1]))
        return in_check, pins, checks

    def getPawnMoves(self, row, col, moves):
        """
        Получение всех ходов пешки
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

        if self.board[row + move_amount][col] == "--":
            if not piece_pinned or pin_direction == (move_amount, 0):
                moves.append(Move((row, col), (row + move_amount, col), self.board))
                if row == start_row and self.board[row + 2 * move_amount][col] == "--":
                    moves.append(Move((row, col), (row + 2 * move_amount, col), self.board))
        if col - 1 >= 0:  # съесть слева
            if not piece_pinned or pin_direction == (move_amount, -1):
                if self.board[row + move_amount][col - 1][0] == enemy_color:
                    moves.append(Move((row, col), (row + move_amount, col - 1), self.board))
                if (row + move_amount, col - 1) == self.enpassant_possible:
                    attacking_piece = blocking_piece = False
                    if king_row == row:
                        if king_col < col:  # король слева от пешки
                            # inside: между королем и пешкой
                            # outside: между королем и границей
                            inside_range = range(king_col + 1, col - 1)
                            outside_range = range(col + 1, 8)
                        else:  # король справа от пешки
                            inside_range = range(king_col - 1, col, -1)
                            outside_range = range(col - 2, -1, -1)
                        for i in inside_range:
                            if self.board[row][i] != "--":
                                blocking_piece = True
                        for i in outside_range:
                            square = self.board[row][i]
                            if square[0] == enemy_color and (square[1] == "R" or square[1] == "Q"):
                                attacking_piece = True
                            elif square != "--":
                                blocking_piece = True
                    if not attacking_piece or blocking_piece:
                        moves.append(Move((row, col), (row + move_amount, col - 1), self.board, is_enpassant_move=True))
        if col + 1 <= 7:  # съесть справа
            if not piece_pinned or pin_direction == (move_amount, +1):
                if self.board[row + move_amount][col + 1][0] == enemy_color:
                    moves.append(Move((row, col), (row + move_amount, col + 1), self.board))
                if (row + move_amount, col + 1) == self.enpassant_possible:
                    attacking_piece = blocking_piece = False
                    if king_row == row:
                        if king_col < col:
                            inside_range = range(king_col + 1, col)
                            outside_range = range(col + 2, 8)
                        else:
                            inside_range = range(king_col - 1, col + 1, -1)
                            outside_range = range(col - 1, -1, -1)
                        for i in inside_range:
                            if self.board[row][i] != "--":
                                blocking_piece = True
                        for i in outside_range:
                            square = self.board[row][i]
                            if square[0] == enemy_color and (square[1] == "R" or square[1] == "Q"):
                                attacking_piece = True
                            elif square != "--":
                                blocking_piece = True
                    if not attacking_piece or blocking_piece:
                        moves.append(Move((row, col), (row + move_amount, col + 1), self.board, is_enpassant_move=True))

    def getRookMoves(self, row, col, moves):
        """
        Получение всех ходов ладьи и добавление их в лист
        """
        piece_pinned = False
        pin_direction = ()
        for i in range(len(self.pins) - 1, -1, -1):
            if self.pins[i][0] == row and self.pins[i][1] == col:
                piece_pinned = True
                pin_direction = (self.pins[i][2], self.pins[i][3])
                if self.board[row][col][
                    1] != "Q":  # нельзя убрать ферзя из связки на ходах ладьи, можно убрать только на ходах слона
                    self.pins.remove(self.pins[i])
                break

        directions = ((-1, 0), (0, -1), (1, 0), (0, 1))
        enemy_color = "b" if self.white_to_move else "w"
        for direction in directions:
            for i in range(1, 8):
                end_row = row + direction[0] * i
                end_col = col + direction[1] * i
                if 0 <= end_row <= 7 and 0 <= end_col <= 7:
                    if not piece_pinned or pin_direction == direction or pin_direction == (
                            -direction[0], -direction[1]):
                        end_piece = self.board[end_row][end_col]
                        if end_piece == "--":  # пустая клетка считается "хорошей"
                            moves.append(Move((row, col), (end_row, end_col), self.board))
                        elif end_piece[0] == enemy_color:  # съесть вражескую фигуру
                            moves.append(Move((row, col), (end_row, end_col), self.board))
                            break
                        else:  # союзная фигура
                            break
                else:  # вне доски
                    break

    def getKnightMoves(self, row, col, moves):
        """
        Получение всех ходов коня и добавление их в лист возможных ходов
        """
        piece_pinned = False
        for i in range(len(self.pins) - 1, -1, -1):
            if self.pins[i][0] == row and self.pins[i][1] == col:
                piece_pinned = True
                self.pins.remove(self.pins[i])
                break

        knight_moves = ((-2, -1), (-2, 1), (-1, 2), (1, 2), (2, -1), (2, 1), (-1, -2),
                        (1, -2))
        ally_color = "w" if self.white_to_move else "b"
        for move in knight_moves:
            end_row = row + move[0]
            end_col = col + move[1]
            if 0 <= end_row <= 7 and 0 <= end_col <= 7:
                if not piece_pinned:
                    end_piece = self.board[end_row][end_col]
                    if end_piece[0] != ally_color:  # т.е. это либо пустая клетка, либо вражеская фигура
                        moves.append(Move((row, col), (end_row, end_col), self.board))

    def getBishopMoves(self, row, col, moves):
        """
        Получение всех ходов слона
        """
        piece_pinned = False
        pin_direction = ()
        for i in range(len(self.pins) - 1, -1, -1):
            if self.pins[i][0] == row and self.pins[i][1] == col:
                piece_pinned = True
                pin_direction = (self.pins[i][2], self.pins[i][3])
                self.pins.remove(self.pins[i])
                break

        directions = ((-1, -1), (-1, 1), (1, 1), (1, -1))
        enemy_color = "b" if self.white_to_move else "w"
        for direction in directions:
            for i in range(1, 8):
                end_row = row + direction[0] * i
                end_col = col + direction[1] * i
                if 0 <= end_row <= 7 and 0 <= end_col <= 7:  # проверка если ход есть на доске
                    if not piece_pinned or pin_direction == direction or pin_direction == (
                            -direction[0], -direction[1]):
                        end_piece = self.board[end_row][end_col]
                        if end_piece == "--":  # пустые клетки подходят
                            moves.append(Move((row, col), (end_row, end_col), self.board))
                        elif end_piece[0] == enemy_color:  # съесть фигуру
                            moves.append(Move((row, col), (end_row, end_col), self.board))
                            break
                        else:  # friendly piece
                            break
                else:  # вне доски
                    break

    def getQueenMoves(self, row, col, moves):
        """
        Получение всех ходов ферзя
        """
        self.getBishopMoves(row, col, moves)
        self.getRookMoves(row, col, moves)

    def getKingMoves(self, row, col, moves):
        """
        Получение всех ходов короля и добавление их в лист
        """
        row_moves = (-1, -1, -1, 0, 0, 1, 1, 1)
        col_moves = (-1, 0, 1, -1, 1, -1, 0, 1)
        ally_color = "w" if self.white_to_move else "b"
        for i in range(8):
            end_row = row + row_moves[i]
            end_col = col + col_moves[i]
            if 0 <= end_row <= 7 and 0 <= end_col <= 7:
                end_piece = self.board[end_row][end_col]
                if end_piece[0] != ally_color:  # если не союзная фигура - пусто или враг
                    # помещение короля и проверка на шах
                    if ally_color == "w":
                        self.white_king_location = (end_row, end_col)
                    else:
                        self.black_king_location = (end_row, end_col)
                    in_check, pins, checks = self.checkForPinsAndChecks()
                    if not in_check:
                        moves.append(Move((row, col), (end_row, end_col), self.board))
                    # возвращение короля в изначальную позицию
                    if ally_color == "w":
                        self.white_king_location = (row, col)
                    else:
                        self.black_king_location = (row, col)

    def getCastleMoves(self, row, col, moves):
        """
        Создаёт все допустимые ходы рокировки для короля и добавляет их в список ходов
        """
        if self.squareUnderAttack(row, col):
            return  # если королю стоит шах, то рокировка невозможна
        if (self.white_to_move and self.current_castling_rights.wks) or (
                not self.white_to_move and self.current_castling_rights.bks):
            self.getKingsideCastleMoves(row, col, moves)
        if (self.white_to_move and self.current_castling_rights.wqs) or (
                not self.white_to_move and self.current_castling_rights.bqs):
            self.getQueensideCastleMoves(row, col, moves)

    def getKingsideCastleMoves(self, row, col, moves):
        if self.board[row][col + 1] == '--' and self.board[row][col + 2] == '--':
            if not self.squareUnderAttack(row, col + 1) and not self.squareUnderAttack(row, col + 2):
                moves.append(Move((row, col), (row, col + 2), self.board, is_castle_move=True))

    def getQueensideCastleMoves(self, row, col, moves):
        if self.board[row][col - 1] == '--' and self.board[row][col - 2] == '--' and self.board[row][col - 3] == '--':
            if not self.squareUnderAttack(row, col - 1) and not self.squareUnderAttack(row, col - 2):
                moves.append(Move((row, col), (row, col - 2), self.board, is_castle_move=True))


class CastleRights:
    def __init__(self, wks, bks, wqs, bqs):
        self.wks = wks
        self.bks = bks
        self.wqs = wqs
        self.bqs = bqs


class Move:
    # В шахматах поля на доске описываются 2 символами, один из них - цифра 1-8, а вторая - буква a-f
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
        # превращение пешки
        self.is_pawn_promotion = (self.piece_moved == "wp" and self.end_row == 0) or (
                self.piece_moved == "bp" and self.end_row == 7)
        # en passant
        self.is_enpassant_move = is_enpassant_move
        if self.is_enpassant_move:
            self.piece_captured = "wp" if self.piece_moved == "bp" else "bp"
        # рокировка
        self.is_castle_move = is_castle_move

        self.is_capture = self.piece_captured != "--"
        self.moveID = self.start_row * 1000 + self.start_col * 100 + self.end_row * 10 + self.end_col

    def __eq__(self, other):
        if isinstance(other, Move):
            return self.moveID == other.moveID
        return False

    def getChessNotation(self):
        if self.is_pawn_promotion:
            return self.getRankFile(self.end_row, self.end_col) + "Q"
        if self.is_castle_move:
            if self.end_col == 1:
                return "0-0-0"
            else:
                return "0-0"
        if self.is_enpassant_move:
            return self.getRankFile(self.start_row, self.start_col)[0] + "x" + self.getRankFile(self.end_row,
                                                                                                self.end_col) + " e.p."
        if self.piece_captured != "--":
            if self.piece_moved[1] == "p":
                return self.getRankFile(self.start_row, self.start_col)[0] + "x" + self.getRankFile(self.end_row,
                                                                                                    self.end_col)
            else:
                return self.piece_moved[1] + "x" + self.getRankFile(self.end_row, self.end_col)
        else:
            if self.piece_moved[1] == "p":
                return self.getRankFile(self.end_row, self.end_col)
            else:
                return self.piece_moved[1] + self.getRankFile(self.end_row, self.end_col)


    def getRankFile(self, row, col):
        return self.cols_to_files[col] + self.rows_to_ranks[row]

    def __str__(self):
        if self.is_castle_move:
            return "0-0" if self.end_col == 6 else "0-0-0"

        end_square = self.getRankFile(self.end_row, self.end_col)

        if self.piece_moved[1] == "p":
            if self.is_capture:
                return self.cols_to_files[self.start_col] + "x" + end_square
            else:
                return end_square + "Q" if self.is_pawn_promotion else end_square

        move_string = self.piece_moved[1]
        if self.is_capture:
            move_string += "x"
        return move_string + end_square