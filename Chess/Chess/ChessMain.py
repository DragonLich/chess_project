"""
Главный файл
Обработка ввода пользователя
Отображает текущий игровой статус
"""
import pygame as p
import ChessEngine
import sys

BOARD_WIDTH = BOARD_HEIGHT = 512 # разрешение доски
MOVE_LOG_PANEL_WIDTH = 250 # разрешение нотации
MOVE_LOG_PANEL_HEIGHT = BOARD_HEIGHT # разрешение нотации
DIMENSION = 8 # размерность
SQUARE_SIZE = BOARD_HEIGHT // DIMENSION # размер одного квадрата
MAX_FPS = 15
IMAGES = {} # изображения фигур


def loadImages():
    """
    Инициализация директории изображений фигур
    Функция вызывается единажды в main
    """
    pieces = ['wp', 'wR', 'wN', 'wB', 'wK', 'wQ', 'bp', 'bR', 'bN', 'bB', 'bK', 'bQ']
    for piece in pieces:
        IMAGES[piece] = p.transform.scale(p.image.load("images/" + piece + ".png"), (SQUARE_SIZE, SQUARE_SIZE))


def main():

    p.init()
    screen = p.display.set_mode((BOARD_WIDTH + MOVE_LOG_PANEL_WIDTH, BOARD_HEIGHT)) # экран
    clock = p.time.Clock()
    screen.fill(p.Color("white")) # заполняем экран белым цветом
    game_state = ChessEngine.GameState() # статус игры
    valid_moves = game_state.getValidMoves() # возможные ходы
    move_made = False # флаг сделанного хода
    animate = False # анимация
    loadImages()  # делаем это 1 раз перед while
    running = True # запуск программы
    square_selected = ()  # изначально не выбрана никакая клетка, тут будем отслеживать последнее нажатие мышкой
    player_clicks = []  # тут будем отслеживать клики игрока
    game_over = False # конец игры
    move_undone = False
    move_log_font = p.font.SysFont("Arial", 14, False, False) # шрифт нотации

    while running:
        for e in p.event.get():
            if e.type == p.QUIT: # если выходим
                p.quit()
                sys.exit()
            # нажатия мыши
            elif e.type == p.MOUSEBUTTONDOWN:
                if not game_over:
                    location = p.mouse.get_pos()  # (x, y) локация мышки
                    col = location[0] // SQUARE_SIZE
                    row = location[1] // SQUARE_SIZE
                    if square_selected == (row, col) or col >= 8:  # пользователь нажал дважды на один и тот же квадрат
                        square_selected = ()  # отменяем выбор
                        player_clicks = []  # чистим player_clicks
                    else:
                        square_selected = (row, col)
                        player_clicks.append(square_selected)  # добавить оба нажатия
                    if len(player_clicks) == 2:  # после 2го нажатия
                        move = ChessEngine.Move(player_clicks[0], player_clicks[1], game_state.board)
                        for i in range(len(valid_moves)):
                            if move == valid_moves[i]:
                                game_state.makeMove(valid_moves[i])
                                move_made = True
                                animate = True
                                square_selected = ()
                                player_clicks = []
                        if not move_made:
                            player_clicks = [square_selected]

            # нажатие клавиш
            elif e.type == p.KEYDOWN:
                if e.key == p.K_z:  # отмена хода при нажатии 'z'
                    game_state.undoMove()
                    move_made = True
                    animate = False
                    game_over = False
                    move_undone = True
                if e.key == p.K_r:  # перезапуск игры при нажатии 'r'
                    game_state = ChessEngine.GameState()
                    valid_moves = game_state.getValidMoves()
                    square_selected = ()
                    player_clicks = []
                    move_made = False
                    animate = False
                    game_over = False
                    move_undone = True

        if move_made:
            if animate:
                animateMove(game_state.move_log[-1], screen, game_state.board, clock)
            valid_moves = game_state.getValidMoves()
            move_made = False
            animate = False
            move_undone = False

        drawGameState(screen, game_state, valid_moves, square_selected)

        if not game_over:
            drawMoveLog(screen, game_state, move_log_font)

        if game_state.checkmate:
            game_over = True
            if game_state.white_to_move:
                drawEndGameText(screen, "Черные победили через мат")
            else:
                drawEndGameText(screen, "Белые победили через мат>")

        elif game_state.stalemate:
            game_over = True
            drawEndGameText(screen, "Пат")

        clock.tick(MAX_FPS)
        p.display.flip()


def drawGameState(screen, game_state, valid_moves, square_selected):
    """
    Этот блок ответственен за всю графику в текущем статусе игры
    """
    drawBoard(screen)  # рисует клетки на доске
    highlightSquares(screen, game_state, valid_moves, square_selected)
    drawPieces(screen, game_state.board)  # рисует фигуры поверх клеток


def drawBoard(screen):
    """
    Рисует клетки на столе
    """
    global colors
    colors = [p.Color("white"), p.Color("gray")]
    for row in range(DIMENSION):
        for column in range(DIMENSION):
            color = colors[((row + column) % 2)]
            p.draw.rect(screen, color, p.Rect(column * SQUARE_SIZE, row * SQUARE_SIZE, SQUARE_SIZE, SQUARE_SIZE))


def highlightSquares(screen, game_state, valid_moves, square_selected):
    """
    Подсветка клетки выбранной фигуры и её возможных ходов
    """
    if (len(game_state.move_log)) > 0:
        last_move = game_state.move_log[-1]
        s = p.Surface((SQUARE_SIZE, SQUARE_SIZE))
        s.set_alpha(100)
        s.fill(p.Color('green'))
        screen.blit(s, (last_move.end_col * SQUARE_SIZE, last_move.end_row * SQUARE_SIZE))
    if square_selected != ():
        row, col = square_selected
        if game_state.board[row][col][0] == (
                'w' if game_state.white_to_move else 'b'):  # square_selected фигура которая может быть сделать ход
            s = p.Surface((SQUARE_SIZE, SQUARE_SIZE))
            s.set_alpha(100)
            s.fill(p.Color('blue'))
            screen.blit(s, (col * SQUARE_SIZE, row * SQUARE_SIZE))
            s.fill(p.Color('yellow'))
            for move in valid_moves:
                if move.start_row == row and move.start_col == col:
                    screen.blit(s, (move.end_col * SQUARE_SIZE, move.end_row * SQUARE_SIZE))


def drawPieces(screen, board):
    """
    Рисует фигуры на доске используя текущий статус игры
    """
    for row in range(DIMENSION):
        for column in range(DIMENSION):
            piece = board[row][column]
            if piece != "--":
                screen.blit(IMAGES[piece], p.Rect(column * SQUARE_SIZE, row * SQUARE_SIZE, SQUARE_SIZE, SQUARE_SIZE))


def drawMoveLog(screen, game_state, font):
    """
    Рисует лог ходов
    """
    move_log_rect = p.Rect(BOARD_WIDTH, 0, MOVE_LOG_PANEL_WIDTH, MOVE_LOG_PANEL_HEIGHT)
    p.draw.rect(screen, p.Color('black'), move_log_rect)
    move_log = game_state.move_log
    move_texts = []
    for i in range(0, len(move_log), 2):
        move_string = str(i // 2 + 1) + '. ' + str(move_log[i]) + " "
        if i + 1 < len(move_log):
            move_string += str(move_log[i + 1]) + "  "
        move_texts.append(move_string)

    moves_per_row = 3
    padding = 5
    line_spacing = 2
    text_y = padding
    for i in range(0, len(move_texts), moves_per_row):
        text = ""
        for j in range(moves_per_row):
            if i + j < len(move_texts):
                text += move_texts[i + j]

        text_object = font.render(text, True, p.Color('white'))
        text_location = move_log_rect.move(padding, text_y)
        screen.blit(text_object, text_location)
        text_y += text_object.get_height() + line_spacing


def drawEndGameText(screen, text):
    font = p.font.SysFont("Helvetica", 32, True, False)
    text_object = font.render(text, False, p.Color("gray"))
    text_location = p.Rect(0, 0, BOARD_WIDTH, BOARD_HEIGHT).move(BOARD_WIDTH / 2 - text_object.get_width() / 2,
                                                                 BOARD_HEIGHT / 2 - text_object.get_height() / 2)
    screen.blit(text_object, text_location)
    text_object = font.render(text, False, p.Color('black'))
    screen.blit(text_object, text_location.move(2, 2))


def animateMove(move, screen, board, clock):
    """
    Анимация хода
    """
    global colors
    d_row = move.end_row - move.start_row
    d_col = move.end_col - move.start_col
    frames_per_square = 10
    frame_count = (abs(d_row) + abs(d_col)) * frames_per_square
    for frame in range(frame_count + 1):
        row, col = (move.start_row + d_row * frame / frame_count, move.start_col + d_col * frame / frame_count)
        drawBoard(screen)
        drawPieces(screen, board)
        color = colors[(move.end_row + move.end_col) % 2]
        end_square = p.Rect(move.end_col * SQUARE_SIZE, move.end_row * SQUARE_SIZE, SQUARE_SIZE, SQUARE_SIZE)
        p.draw.rect(screen, color, end_square)
        # рисует взятую фигуру на прямоугольнике
        if move.piece_captured != '--':
            if move.is_enpassant_move:
                enpassant_row = move.end_row + 1 if move.piece_captured[0] == 'b' else move.end_row - 1
                end_square = p.Rect(move.end_col * SQUARE_SIZE, enpassant_row * SQUARE_SIZE, SQUARE_SIZE, SQUARE_SIZE)
            screen.blit(IMAGES[move.piece_captured], end_square)
        # рисуем двигающийся объект
        screen.blit(IMAGES[move.piece_moved], p.Rect(col * SQUARE_SIZE, row * SQUARE_SIZE, SQUARE_SIZE, SQUARE_SIZE))
        p.display.flip()
        clock.tick(60)


if __name__ == "__main__":
    main()