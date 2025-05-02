import copy  # Necesario para crear copias independientes del tablero

# --- Constantes para representar las piezas y jugadores ---
EMPTY = 0
# Jugador 1 (por ejemplo, 'Negras' o 'Rojas', empieza abajo)
P1_MAN = 1
P1_KING = 3
# Jugador 2 (por ejemplo, 'Blancas', empieza arriba)
P2_MAN = 2
P2_KING = 4

# --- Constantes para el estado del juego ---
ONGOING = 0
P1_WINS = 1
P2_WINS = 2
DRAW = 3  # (Opcional, las reglas de empate pueden ser complejas)

# --- Clases (opcional pero recomendado para organización) ---


class Move:
    """Representa un movimiento, incluyendo capturas."""

    def __init__(self, start_pos, end_pos, captured_pieces=None):
        self.start_row, self.start_col = start_pos
        self.end_row, self.end_col = end_pos
        # Lista de coordenadas (row, col) de las piezas capturadas en este movimiento
        self.captured_pieces = captured_pieces if captured_pieces else []

    def __repr__(self):
        # Representación útil para debugging
        capture_info = (
            f", captures: {self.captured_pieces}" if self.captured_pieces else ""
        )
        return f"Move from ({self.start_row},{self.start_col}) to ({self.end_row},{self.end_col}){capture_info}"

    def __eq__(self, other):
        # Necesario para comparar movimientos si los buscas en listas
        if not isinstance(other, Move):
            return NotImplemented
        return (
            self.start_row == other.start_row
            and self.start_col == other.start_col
            and self.end_row == other.end_row
            and self.end_col == other.end_col
            and
            # Compara las piezas capturadas (el orden importa si son multi-saltos)
            self.captured_pieces == other.captured_pieces
        )

    def __hash__(self):
        # Necesario si usas movimientos como claves en diccionarios o sets
        return hash(
            (
                self.start_row,
                self.start_col,
                self.end_row,
                self.end_col,
                tuple(self.captured_pieces),
            )
        )


class Board:
    """Representa el estado del tablero y la lógica del juego."""

    def __init__(self, rows=8, cols=8):
        self.rows = rows
        self.cols = cols
        self.board = [[EMPTY for _ in range(cols)] for _ in range(rows)]
        self._setup_board()

    def _setup_board(self):
        """Configura la posición inicial de las piezas."""
        for r in range(self.rows):
            for c in range(self.cols):
                if (r + c) % 2 != 0:  # Solo colocar en casillas oscuras
                    if r < 3:
                        self.board[r][c] = P2_MAN  # Jugador 2 arriba
                    elif r > self.rows - 4:
                        self.board[r][c] = P1_MAN  # Jugador 1 abajo

    def print_board(self):
        """Imprime el tablero en la consola para visualización."""
        print("   " + " ".join(map(str, range(self.cols))))
        print("  +" + "--" * self.cols + "+")
        for r in range(self.rows):
            row_str = f"{r} |"
            for c in range(self.cols):
                piece = self.board[r][c]
                if piece == EMPTY:
                    row_str += " ."
                elif piece == P1_MAN:
                    row_str += " r"  # red
                elif piece == P1_KING:
                    row_str += " R"
                elif piece == P2_MAN:
                    row_str += " w"  # white
                elif piece == P2_KING:
                    row_str += " W"
            print(row_str + " |")
        print("  +" + "--" * self.cols + "+")

    def get_piece(self, row, col):
        """Obtiene la pieza en una posición dada, o None si está fuera."""
        if 0 <= row < self.rows and 0 <= col < self.cols:
            return self.board[row][col]
        return None

    def is_valid_pos(self, row, col):
        """Verifica si una posición está dentro de los límites del tablero."""
        return 0 <= row < self.rows and 0 <= col < self.cols

    def get_player_pieces(self, player):
        """Devuelve una lista de coordenadas (row, col) de todas las piezas de un jugador."""
        pieces = []
        player_mans = P1_MAN if player == 1 else P2_MAN
        player_kings = P1_KING if player == 1 else P2_KING
        for r in range(self.rows):
            for c in range(self.cols):
                if self.board[r][c] in (player_mans, player_kings):
                    pieces.append((r, c))
        return pieces

    def _get_piece_moves(self, r, c):
        """
        Encuentra TODOS los movimientos posibles (simples y capturas)
        para una pieza específica en (r, c).
        Devuelve una tupla: (simple_moves, capture_moves)
        """
        simple_moves = []
        capture_moves = []
        piece = self.board[r][c]

        if piece == EMPTY:
            return [], []

        player = 1 if piece in (P1_MAN, P1_KING) else 2
        opponent = 2 if player == 1 else 1
        opponent_mans = P1_MAN if opponent == 1 else P2_MAN
        opponent_kings = P1_KING if opponent == 1 else P2_KING

        # Direcciones de movimiento: [delta_row, delta_col]
        move_dirs = []
        if piece == P1_MAN:
            move_dirs = [[-1, -1], [-1, 1]]  # Solo hacia arriba
        elif piece == P2_MAN:
            move_dirs = [[1, -1], [1, 1]]  # Solo hacia abajo
        elif piece in (P1_KING, P2_KING):
            move_dirs = [[-1, -1], [-1, 1], [1, -1], [1, 1]]  # Todas las direcciones

        # --- Buscar movimientos simples ---
        for dr, dc in move_dirs:
            nr, nc = r + dr, c + dc
            if self.is_valid_pos(nr, nc) and self.board[nr][nc] == EMPTY:
                simple_moves.append(Move((r, c), (nr, nc)))

        # --- Buscar capturas (recursivamente para multi-saltos) ---
        capture_moves.extend(
            self._find_captures_recursive(
                r, c, player, opponent_mans, opponent_kings, []
            )
        )

        return simple_moves, capture_moves

    def _find_captures_recursive(
        self, r, c, player, opp_man, opp_king, captured_so_far
    ):
        """
        Función auxiliar recursiva para encontrar secuencias de captura (multi-saltos).
        """
        found_captures = []
        piece = self.board[r][c]  # La pieza que está saltando
        is_king = piece in (P1_KING, P2_KING)

        # Direcciones de salto (siempre 2 pasos)
        jump_dirs = [[-2, -2], [-2, 2], [2, -2], [2, 2]]

        for dr, dc in jump_dirs:
            nr, nc = r + dr, c + dc  # Posición de aterrizaje
            jumped_r, jumped_c = (
                r + dr // 2,
                c + dc // 2,
            )  # Posición de la pieza saltada

            # Validar dirección de salto para hombres (no pueden saltar hacia atrás)
            if not is_king:
                if player == 1 and dr > 0:
                    continue  # Jugador 1 solo salta hacia arriba (dr negativo)
                if player == 2 and dr < 0:
                    continue  # Jugador 2 solo salta hacia abajo (dr positivo)

            # Comprobar si el salto es válido
            if self.is_valid_pos(nr, nc) and self.board[nr][nc] == EMPTY:
                jumped_piece = self.get_piece(jumped_r, jumped_c)
                jumped_pos = (jumped_r, jumped_c)

                # Verificar si la pieza saltada es del oponente y NO ha sido capturada YA en ESTA secuencia
                if (
                    jumped_piece in (opp_man, opp_king)
                    and jumped_pos not in captured_so_far
                ):

                    # Crear una copia temporal del tablero para simular el salto
                    temp_board_state = [
                        row[:] for row in self.board
                    ]  # Copia superficial es suficiente aquí
                    temp_board_state[r][c] = EMPTY
                    temp_board_state[jumped_r][jumped_c] = EMPTY
                    temp_board_state[nr][nc] = piece  # Mover la pieza que salta

                    # Crear una instancia temporal del tablero con el estado simulado
                    temp_board_obj = Board(self.rows, self.cols)
                    temp_board_obj.board = temp_board_state

                    current_capture_path = captured_so_far + [jumped_pos]

                    # Buscar *más* saltos desde la nueva posición (nr, nc) en el tablero temporal
                    further_captures = temp_board_obj._find_captures_recursive(
                        nr, nc, player, opp_man, opp_king, current_capture_path
                    )

                    if not further_captures:
                        # Si no hay más saltos, este es el final de una secuencia de captura
                        found_captures.append(
                            Move((r, c), (nr, nc), current_capture_path)
                        )
                    else:
                        # Si hay más saltos, agregarlos. Los movimientos devueltos ya tendrán
                        # el punto de inicio original (r, c) implícito en la recursión anterior
                        # Necesitamos actualizar el punto de inicio en los movimientos devueltos por la recursión
                        for move in further_captures:
                            move.start_row, move.start_col = (
                                r,
                                c,
                            )  # Corregir origen al original
                            found_captures.append(move)

        return found_captures

    def get_legal_moves(self, player):
        """
        Obtiene todos los movimientos legales para un jugador.
        ¡Importante! Las capturas son obligatorias en Damas.
        """
        all_simple_moves = []
        all_capture_moves = []

        player_pieces = self.get_player_pieces(player)

        for r, c in player_pieces:
            simple, captures = self._get_piece_moves(r, c)
            all_simple_moves.extend(simple)
            all_capture_moves.extend(captures)

        # Si hay alguna captura disponible, SOLO las capturas son legales
        if all_capture_moves:
            # Filtrar para evitar duplicados si una secuencia se encontró por varias vías (raro pero posible)
            # Usar un set para eliminar duplicados basados en el hash del Move
            unique_captures = list(set(all_capture_moves))
            return unique_captures
        else:
            return all_simple_moves

    def apply_move_old(self, move):
        """
        Aplica un movimiento al tablero y devuelve un *NUEVO* objeto Board
        con el estado resultante. No modifica el tablero actual.
        """
        # Crear una copia profunda para no afectar el estado original
        new_board = Board(self.rows, self.cols)
        new_board.board = copy.deepcopy(self.board)

        # Obtener la pieza que se mueve
        piece = new_board.board[move.start_row][move.start_col]

        # Vaciar la casilla de inicio
        new_board.board[move.start_row][move.start_col] = EMPTY

        # Eliminar piezas capturadas (si las hay)
        for r_cap, c_cap in move.captured_pieces:
            new_board.board[r_cap][c_cap] = EMPTY

        # Colocar la pieza en la casilla de destino
        new_board.board[move.end_row][move.end_col] = piece

        # --- Comprobar y aplicar promoción a Dama (Rey) ---
        player = 1 if piece in (P1_MAN, P1_KING) else 2
        if piece == P1_MAN and move.end_row == 0:  # Jugador 1 llega a la fila superior
            new_board.board[move.end_row][move.end_col] = P1_KING
        elif (
            piece == P2_MAN and move.end_row == self.rows - 1
        ):  # Jugador 2 llega a la fila inferior
            new_board.board[move.end_row][move.end_col] = P2_KING

        return new_board
    
    def apply_move(self, move: Move):
        """
        Aplica un movimiento al tablero y devuelve una tupla:
        (nuevo_objeto_Board, progreso_realizado)
        No modifica el tablero actual.
        """
        new_board = Board(self.rows, self.cols)
        new_board.board = copy.deepcopy(self.board) # Usa copy si no lo importaste arriba

        piece = new_board.board[move.start_row][move.start_col]
        is_man_move = piece in (P1_MAN, P2_MAN) # ¿Se movió un hombre?
        progress_made = False # Asume no progreso por defecto
 
        # Vaciar inicio
        new_board.board[move.start_row][move.start_col] = EMPTY 

        # Eliminar capturadas (si las hay, SIEMPRE es progreso)
        if move.captured_pieces:
            progress_made = True
            for r_cap, c_cap in move.captured_pieces:
                new_board.board[r_cap][c_cap] = EMPTY

        # Colocar en destino
        new_board.board[move.end_row][move.end_col] = piece

        # Comprobar promoción y si el movimiento original fue de un hombre
        promoted = False
        if piece == P1_MAN and move.end_row == 0:
            new_board.board[move.end_row][move.end_col] = P1_KING
            promoted = True
        elif piece == P2_MAN and move.end_row == self.rows - 1:
            new_board.board[move.end_row][move.end_col] = P2_KING
            promoted = True

        # Determinar si hubo progreso: captura O movimiento de hombre
        # Incluso si un hombre promueve, fue un movimiento de hombre.
        if not progress_made and is_man_move:
            progress_made = True

        # Devuelve el nuevo tablero Y si el movimiento contó como progreso
        return new_board, progress_made

    def check_game_over(self, player_turn):
        """
        Comprueba si el juego ha terminado.
        Devuelve el estado: ONGOING, P1_WINS, P2_WINS.
        """
        # 1. Comprobar si el jugador actual tiene movimientos legales
        legal_moves = self.get_legal_moves(player_turn)
        if not legal_moves:
            # Si el jugador actual no tiene movimientos, pierde
            return P2_WINS if player_turn == 1 else P1_WINS

        # 2. Comprobar si algún jugador se ha quedado sin piezas (alternativa)
        #    Aunque la falta de movimientos suele detectarlo primero.
        p1_pieces = self.get_player_pieces(1)
        if not p1_pieces:
            return P2_WINS
        p2_pieces = self.get_player_pieces(2)
        if not p2_pieces:
            return P1_WINS

        # (Opcional: Añadir reglas de empate, como 40 movimientos sin captura, etc.)

        # Si ninguna condición de fin se cumple, el juego continúa
        return ONGOING


# --- Ejemplo de uso ---
if __name__ == "__main__":
    # print("--- DEBUG: Iniciando bloque principal ---") # <--- AÑADE ESTA LÍNEA
    board = Board()
    current_player = 1  # Empieza Jugador 1

    game_state = ONGOING
    move_count = 0

    while (
        game_state == ONGOING and move_count < 200
    ):  # Límite para evitar bucles infinitos en pruebas
        board.print_board()
        print(f"\nTurno del Jugador {current_player}")

        legal_moves = board.get_legal_moves(current_player)

        game_state = board.check_game_over(current_player)
        if game_state != ONGOING:
            break

        if not legal_moves:
            # Esto no debería ocurrir si check_game_over funciona bien, pero es una salvaguarda
            print(f"¡No hay movimientos legales para el Jugador {current_player}!")
            game_state = P2_WINS if current_player == 1 else P1_WINS
            break

        print("Movimientos legales:")
        for i, move in enumerate(legal_moves):
            print(f"  {i}: {move}")

        # --- Simulación simple de elección de movimiento (primer movimiento legal) ---
        # En el proyecto real, aquí iría la entrada del usuario o la llamada a la IA
        chosen_move_index = 0  # Elegir siempre el primer movimiento para el ejemplo
        try:
            # Intenta obtener una entrada (pero usa 0 si falla o no es número)
            # choice = input(f"Elige un movimiento (0-{len(legal_moves)-1}): ")
            # chosen_move_index = int(choice)
            # if not (0 <= chosen_move_index < len(legal_moves)):
            #    chosen_move_index = 0
            #    print("Opción inválida, eligiendo 0.")
            pass  # Comentado para ejecución automática
        except ValueError:
            # chosen_move_index = 0
            # print("Entrada no válida, eligiendo 0.")
            pass  # Comentado para ejecución automática

        chosen_move = legal_moves[chosen_move_index]
        print(f"Jugador {current_player} elige: {chosen_move}")

        # Aplicar el movimiento para obtener el *nuevo* estado del tablero
        board = board.apply_move(chosen_move)

        # Cambiar de jugador
        current_player = 2 if current_player == 1 else 1
        move_count += 1
        print("-" * 30)

    # --- Fin del juego ---
    board.print_board()
    print("\n¡¡¡JUEGO TERMINADO!!!")
    if game_state == P1_WINS:
        print("Resultado: Gana el Jugador 1 (r/R)")
    elif game_state == P2_WINS:
        print("Resultado: Gana el Jugador 2 (w/W)")
    elif game_state == DRAW:
        print("Resultado: Empate")
    else:
        print("Resultado: Juego interrumpido (límite de movimientos)")
