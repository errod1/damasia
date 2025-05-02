# checkers_ai.py

import random
import math
from checkers_logic import (
    Board,
    Move,
    P1_MAN,
    P1_KING,
    P2_MAN,
    P2_KING,
    EMPTY,
    P1_WINS,
    P2_WINS,
    ONGOING,
)

# --- Constantes para la evaluación ---
# Puedes ajustar estos pesos experimentando
PIECE_VALUE = 10  # Valor base de una pieza normal
KING_VALUE = 25  # Valor de una Dama (Rey)
BACK_ROW_BONUS = 4  # Bonificación por pieza en la fila trasera (más segura)
MIDDLE_BOX_BONUS = 3  # Bonificación por pieza en las 4 casillas centrales
MIDDLE_ROWS_BONUS = 1  # Bonificación por pieza en las filas centrales (no bordes)
WIN_SCORE = 10000
LOSS_SCORE = -10000


def evaluate_board(board: Board, player: int):
    """
    Función de evaluación heurística.
    Calcula una puntuación para el estado actual del tablero DESDE LA PERSPECTIVA DEL 'player'.
    Un puntaje positivo es bueno para 'player', negativo es malo.
    """
    p1_score = 0
    p2_score = 0

    # Definir quién es quién para la perspectiva
    my_man, my_king = (P1_MAN, P1_KING) if player == 1 else (P2_MAN, P2_KING)
    op_man, op_king = (P2_MAN, P2_KING) if player == 1 else (P1_MAN, P1_KING)

    # Recorrer el tablero y sumar puntos
    for r in range(board.rows):
        for c in range(board.cols):
            piece = board.board[r][c]
            current_piece_score = 0

            if piece == my_man:
                current_piece_score = PIECE_VALUE
                # Bonificación por estar en filas intermedias (más control)
                if 2 <= r <= board.rows - 3:
                    current_piece_score += MIDDLE_ROWS_BONUS
                # Bonificación defensiva (más difícil para el oponente coronar)
                if player == 1 and r == board.rows - 1:  # P1 en su fila trasera
                    current_piece_score += BACK_ROW_BONUS
                elif player == 2 and r == 0:  # P2 en su fila trasera
                    current_piece_score += BACK_ROW_BONUS
                # Bonificación por control central (4 casillas clave)
                if (r == board.rows // 2 - 1 or r == board.rows // 2) and (
                    c == board.cols // 2 - 1 or c == board.cols // 2
                ):
                    current_piece_score += MIDDLE_BOX_BONUS
                p1_score += current_piece_score  # Asume que el cálculo se hace desde la perspectiva de P1 siempre? No, se hace para 'player'

            elif piece == my_king:
                current_piece_score = KING_VALUE
                # Los reyes también obtienen bonificación por control central
                if (r == board.rows // 2 - 1 or r == board.rows // 2) and (
                    c == board.cols // 2 - 1 or c == board.cols // 2
                ):
                    current_piece_score += MIDDLE_BOX_BONUS
                p1_score += current_piece_score

            elif piece == op_man:
                current_piece_score = PIECE_VALUE
                if 2 <= r <= board.rows - 3:
                    current_piece_score += MIDDLE_ROWS_BONUS
                if (
                    player == 2 and r == board.rows - 1
                ):  # P1 en su fila trasera (vista desde P2)
                    current_piece_score += BACK_ROW_BONUS
                elif player == 1 and r == 0:  # P2 en su fila trasera (vista desde P1)
                    current_piece_score += BACK_ROW_BONUS
                if (r == board.rows // 2 - 1 or r == board.rows // 2) and (
                    c == board.cols // 2 - 1 or c == board.cols // 2
                ):
                    current_piece_score += MIDDLE_BOX_BONUS
                p2_score += current_piece_score

            elif piece == op_king:
                current_piece_score = KING_VALUE
                if (r == board.rows // 2 - 1 or r == board.rows // 2) and (
                    c == board.cols // 2 - 1 or c == board.cols // 2
                ):
                    current_piece_score += MIDDLE_BOX_BONUS
                p2_score += current_piece_score

    # Puntuación final es la diferencia
    return p1_score - p2_score


def minimax_alphabeta(board: Board, depth: int, alpha: float, beta: float, maximizing_player: bool, ai_player: int, current_moves_since_progress: int = 0, draw_limit: int = 80):
    """
    Algoritmo Minimax con poda Alfa-Beta.
    ¡OJO! Pasar el contador de movimientos sin progreso a través de la recursión
    es complejo y puede ser ineficiente. La comprobación de empate por movimientos
    se maneja mejor en la vista principal (make_move).
    Aquí solo necesitamos manejar el estado DRAW si es devuelto por check_game_over
    (que actualmente no lo hace, check_game_over solo detecta win/loss por movilidad).
    
    Por lo tanto, el cambio principal es manejar el estado DRAW si *ya está* en el tablero
    o si es devuelto por una hipotética versión futura de check_game_over.
    """
    
    # Check_game_over NO detecta empates por movimiento, solo por falta de movimientos.
    # El empate por movimientos se detecta en la VISTA.
    # Aquí, solo manejamos los estados que check_game_over SÍ devuelve.
    
    # --- CORRECCIÓN: No necesitamos pasar contadores aquí ---
    # --- La lógica de empate por contador está en la vista ---

    # Obtener el jugador cuyo turno evaluamos (para check_game_over)
    player_to_check = ai_player if maximizing_player else (3 - ai_player)
    game_state = board.check_game_over(player_to_check)

    # Casos base de la recursión
    if depth == 0 or game_state != ONGOING:
        # --- Manejo de estados finales ---
        if game_state == P1_WINS:
            return WIN_SCORE if ai_player == 1 else LOSS_SCORE
        elif game_state == P2_WINS:
            return WIN_SCORE if ai_player == 2 else LOSS_SCORE
        # --- Añadir manejo explícito de Empate si check_game_over lo devolviera ---
        # elif game_state == DRAW:
        #     return 0 # Empate es neutral
        else: # Profundidad 0 o estado inesperado (tratar como evaluación normal)
            return evaluate_board(board, ai_player)

    # --- Turno del Maximizador (IA) ---
    if maximizing_player:
        max_eval = -math.inf
        current_player_num = ai_player
        legal_moves = board.get_legal_moves(current_player_num)
        
        if not legal_moves: # Si maximizador no puede mover, pierde
             return LOSS_SCORE 

        for move in legal_moves:
            # ¡Importante! apply_move ahora devuelve una tupla
            new_board_obj, _ = board.apply_move(move) # Ignoramos progress_made aquí
            evaluation = minimax_alphabeta(new_board_obj, depth - 1, alpha, beta, False, ai_player) # Llamada recursiva
            max_eval = max(max_eval, evaluation)
            alpha = max(alpha, evaluation)
            if beta <= alpha:
                break
        return max_eval

    # --- Turno del Minimizador (Oponente) ---
    else: # minimizing_player
        min_eval = math.inf
        current_player_num = 3 - ai_player
        legal_moves = board.get_legal_moves(current_player_num)

        if not legal_moves: # Si minimizador no puede mover, IA gana
             return WIN_SCORE 

        for move in legal_moves:
            # ¡Importante! apply_move ahora devuelve una tupla
            new_board_obj, _ = board.apply_move(move) # Ignoramos progress_made aquí
            evaluation = minimax_alphabeta(new_board_obj, depth - 1, alpha, beta, True, ai_player) # Llamada recursiva
            min_eval = min(min_eval, evaluation)
            beta = min(beta, evaluation)
            if beta <= alpha:
                break
        return min_eval


def minimax_alphabeta_old(
    board: Board,
    depth: int,
    alpha: float,
    beta: float,
    maximizing_player: bool,
    ai_player: int,
):
    """
    Algoritmo Minimax con poda Alfa-Beta.
    Devuelve la evaluación del mejor movimiento encontrado desde este estado.
    """
    game_state = board.check_game_over(
        1 if maximizing_player else 2
    )  # Comprueba si el jugador *cuyo turno sería* puede moverse

    # Casos base de la recursión: profundidad alcanzada o juego terminado
    if depth == 0 or game_state != ONGOING:
        if game_state == P1_WINS:
            return WIN_SCORE if ai_player == 1 else LOSS_SCORE
        elif game_state == P2_WINS:
            return WIN_SCORE if ai_player == 2 else LOSS_SCORE
        # Podría haber empate aquí si se implementa
        else:  # Profundidad 0 o empate (si existe)
            # Evaluamos la posición actual desde la perspectiva de la IA que inició la búsqueda
            return evaluate_board(board, ai_player)

    # --- Turno del Maximizador (IA) ---
    if maximizing_player:
        max_eval = -math.inf
        current_player_num = ai_player  # El maximizador es la IA
        legal_moves = board.get_legal_moves(current_player_num)

        # Si no hay movimientos, el juego debería haber terminado (manejado arriba), pero por si acaso:
        if not legal_moves:
            return LOSS_SCORE  # Si IA no puede mover, pierde

        for move in legal_moves:
            new_board = board.apply_move(move)
            # Llamada recursiva para el oponente (minimizador)
            evaluation = minimax_alphabeta(
                new_board, depth - 1, alpha, beta, False, ai_player
            )
            max_eval = max(max_eval, evaluation)
            alpha = max(alpha, evaluation)
            # Poda Alfa-Beta
            if beta <= alpha:
                break  # Beta corta (el minimizador ya tiene una opción mejor en otra rama)
        return max_eval

    # --- Turno del Minimizador (Oponente) ---
    else:  # minimizing_player
        min_eval = math.inf
        current_player_num = 3 - ai_player  # El minimizador es el oponente
        legal_moves = board.get_legal_moves(current_player_num)

        # Si no hay movimientos, el juego debería haber terminado (manejado arriba), pero por si acaso:
        if not legal_moves:
            return WIN_SCORE  # Si oponente no puede mover, la IA gana

        for move in legal_moves:
            new_board = board.apply_move(move)
            # Llamada recursiva para la IA (maximizador)
            evaluation = minimax_alphabeta(
                new_board, depth - 1, alpha, beta, True, ai_player
            )
            min_eval = min(min_eval, evaluation)
            beta = min(beta, evaluation)
            # Poda Alfa-Beta
            if beta <= alpha:
                break  # Alfa corta (el maximizador ya tiene una opción mejor en otra rama)
        return min_eval


def find_best_move(board: Board, player: int, depth: int):
    """
    Encuentra el mejor movimiento para el jugador 'player' usando Minimax con Alfa-Beta.
    Devuelve el objeto Move óptimo encontrado.
    """
    best_move = None
    best_eval = -math.inf
    alpha = -math.inf
    beta = math.inf

    legal_moves = board.get_legal_moves(player)

    # Si no hay movimientos, no podemos hacer nada
    if not legal_moves:
        return None

    # Si solo hay un movimiento, tómalo (ahorra cómputo)
    if len(legal_moves) == 1:
        return legal_moves[0]

    # Iterar sobre los movimientos posibles en el primer nivel
    for move in legal_moves:
        #new_board = board.apply_move(move)
        # Llamamos a minimax para evaluar la posición *después* de nuestro movimiento.
        # La llamada es para el *oponente* (minimizador), por eso maximizing_player=False.
        # La profundidad se reduce en 1 porque ya hemos hecho el primer movimiento.
        #evaluation = minimax_alphabeta(new_board, depth - 1, alpha, beta, False, player)

        # Como buscamos el mejor movimiento para nosotros (maximizador),
        # queremos el movimiento que lleve a la evaluación más alta.

        new_board_obj, _ = board.apply_move(move) # Desempaqueta
        evaluation = minimax_alphabeta(new_board_obj, depth - 1, alpha, beta, False, player) # Pasa el objeto Board

        if evaluation > best_eval:
            best_eval = evaluation
            best_move = move

        # Actualizar alpha (importante para la poda en las llamadas recursivas, aunque aquí no pode directamente)
        alpha = max(alpha, evaluation)

    # Añadir algo de aleatoriedad si varios movimientos tienen la misma mejor evaluación (opcional)
    # Esto puede hacer que la IA sea menos predecible si hay varias opciones "óptimas"
    # best_moves = []
    # epsilon = 1e-4 # Pequeña tolerancia para puntos flotantes
    # for move in legal_moves:
    #    new_board = board.apply_move(move)
    #    evaluation = minimax_alphabeta(new_board, depth - 1, -math.inf, math.inf, False, player) # Recalcular o almacenar
    #    if abs(evaluation - best_eval) < epsilon:
    #        best_moves.append(move)
    # return random.choice(best_moves) if best_moves else None # Devolver uno al azar de los mejores

    if best_move is None and legal_moves:
        # Si por alguna razón no se encontró un 'best_move' pero había movimientos legales
        # (podría pasar con evaluaciones muy extrañas o errores), devuelve uno al azar.
        print(
            "Advertencia: No se encontró un 'best_move' claro, devolviendo uno aleatorio."
        )
        return random.choice(legal_moves)

    return best_move


# --- Ejemplo de uso (para probar la IA de forma aislada) ---
if __name__ == "__main__":
    board = Board()
    current_player = 1  # Empieza P1 (Humano en este ejemplo)
    ai_player = 2  # La IA será P2
    search_depth = 4  # Profundidad de búsqueda (¡ajusta según la potencia de tu PC!)
    # 3-4 es razonable para pruebas rápidas.
    # 5-6 empieza a ser más fuerte pero lento.
    # 7+ puede tardar mucho sin optimizaciones adicionales.

    game_state = ONGOING
    move_count = 0

    while game_state == ONGOING and move_count < 200:
        board.print_board()
        print(f"\nTurno del Jugador {current_player}")

        legal_moves = board.get_legal_moves(current_player)
        game_state = board.check_game_over(
            current_player
        )  # Verificar antes de pedir movimiento

        if game_state != ONGOING:
            break

        if not legal_moves:
            print(f"¡No hay movimientos legales para el Jugador {current_player}!")
            # El estado ya debería reflejar la victoria del oponente por check_game_over
            break

        chosen_move = None
        if current_player == ai_player:
            print(
                f"IA (Jugador {ai_player}) pensando con profundidad {search_depth}..."
            )
            chosen_move = find_best_move(board, ai_player, search_depth)
            if chosen_move:
                print(f"IA elige: {chosen_move}")
            else:
                print(
                    "IA no encontró movimiento (esto es inesperado si había legales)."
                )
                # Forzar fin o manejar error
                game_state = P1_WINS if ai_player == 2 else P2_WINS
                break

        else:  # Turno del "Humano" (entrada manual)
            print("Movimientos legales:")
            for i, move in enumerate(legal_moves):
                print(f"  {i}: {move}")

            valid_choice = False
            while not valid_choice:
                try:
                    choice = input(f"Elige un movimiento (0-{len(legal_moves)-1}): ")
                    chosen_move_index = int(choice)
                    if 0 <= chosen_move_index < len(legal_moves):
                        chosen_move = legal_moves[chosen_move_index]
                        valid_choice = True
                    else:
                        print("Número fuera de rango.")
                except ValueError:
                    print("Entrada inválida, introduce un número.")
                except (
                    EOFError
                ):  # Por si se ejecuta en un entorno sin input interactivo
                    print("EOF detectado, eligiendo movimiento 0.")
                    chosen_move = legal_moves[0]
                    valid_choice = True

        # Aplicar el movimiento elegido (sea de la IA o Humano)
        if chosen_move:
            board = board.apply_move(chosen_move)
            current_player = 3 - current_player  # Cambiar jugador (1 -> 2, 2 -> 1)
            move_count += 1
            print("-" * 30)
        else:
            # Esto podría pasar si find_best_move falla o no hay movimientos
            # aunque la lógica principal debería haberlo capturado antes.
            print("Error: No se pudo determinar un movimiento.")
            break

    # --- Fin del juego ---
    board.print_board()
    print("\n¡¡¡JUEGO TERMINADO!!!")
    if game_state == P1_WINS:
        print("Resultado: Gana el Jugador 1")
    elif game_state == P2_WINS:
        print("Resultado: Gana el Jugador 2")
    elif game_state == DRAW:  # Si implementas empates
        print("Resultado: Empate")
    else:  # Si se interrumpió
        print("Resultado: Juego interrumpido")
