import unittest
import checkers_logic as cl  # Importa tu código del juego


class TestCheckersLogic(unittest.TestCase):

    def setUp(self):
        """Se ejecuta antes de CADA prueba."""
        self.board = cl.Board()

    def test_initial_setup_p1_pieces(self):
        """Verifica el número correcto de piezas del Jugador 1 al inicio."""
        p1_pieces = self.board.get_player_pieces(1)
        # En un tablero estándar 8x8, hay 12 piezas por jugador
        self.assertEqual(len(p1_pieces), 12)
        # Podrías añadir más asserts para verificar posiciones específicas

    def test_initial_setup_p2_pieces(self):
        """Verifica el número correcto de piezas del Jugador 2 al inicio."""
        p2_pieces = self.board.get_player_pieces(2)
        self.assertEqual(len(p2_pieces), 12)

    def test_simple_p1_initial_move(self):
        """Verifica un movimiento simple específico del Jugador 1."""
        # Asume que una pieza P1 está en (5, 0) y puede moverse a (4, 1)
        self.assertEqual(self.board.get_piece(5, 0), cl.P1_MAN)
        self.assertEqual(self.board.get_piece(4, 1), cl.EMPTY)

        # Busca el movimiento específico en los movimientos legales
        legal_moves = self.board.get_legal_moves(1)
        expected_move = cl.Move(start_pos=(5, 0), end_pos=(4, 1))

        # self.assertIn(expected_move, legal_moves) # Descomenta cuando Move tenga __eq__ y __hash__ bien definidos

        # Alternativa si no quieres depender de __eq__ / __hash__ al principio:
        found = any(
            m.start_row == 5 and m.start_col == 0 and m.end_row == 4 and m.end_col == 1
            for m in legal_moves
        )
        self.assertTrue(
            found, "El movimiento simple esperado de (5,0) a (4,1) no se encontró"
        )

    def test_apply_simple_move(self):
        """Verifica que aplicar un movimiento actualice el tablero correctamente."""
        move = cl.Move(start_pos=(5, 0), end_pos=(4, 1))
        new_board = self.board.apply_move(move)

        # Verificar que la pieza está en el nuevo lugar
        self.assertEqual(new_board.get_piece(4, 1), cl.P1_MAN)
        # Verificar que la casilla original está vacía
        self.assertEqual(new_board.get_piece(5, 0), cl.EMPTY)
        # Verificar que el tablero original no cambió (importante!)
        self.assertEqual(self.board.get_piece(5, 0), cl.P1_MAN)
        self.assertEqual(self.board.get_piece(4, 1), cl.EMPTY)

    def test_mandatory_jump(self):
        """Verifica que solo los saltos son legales si están disponibles."""
        # Configurar un escenario de salto obligatorio para P1
        self.board.board = [
            [cl.EMPTY for _ in range(8)] for _ in range(8)
        ]  # Tablero vacío
        self.board.board[5][4] = cl.P1_MAN  # Pieza P1
        self.board.board[4][3] = cl.P2_MAN  # Pieza P2 a saltar
        self.board.board[6][3] = cl.P1_MAN  # Otra pieza P1 (no puede saltar)
        # Añadir casilla de aterrizaje vacía (¡importante!)
        self.board.board[3][2] = cl.EMPTY

        legal_moves = self.board.get_legal_moves(1)

        self.assertEqual(
            len(legal_moves), 1
        )  # Solo debe haber un movimiento legal (el salto)

        # Asegurarse de que realmente hay un movimiento antes de acceder a él
        if not legal_moves:
            self.fail(
                "No se encontraron movimientos legales cuando se esperaba un salto."
            )

        jump_move = legal_moves[0]

        # --- Corrección Aquí ---
        # Comprobar start_row y start_col por separado
        self.assertEqual(jump_move.start_row, 5)
        self.assertEqual(jump_move.start_col, 4)

        # Comprobar end_row y end_col por separado
        self.assertEqual(jump_move.end_row, 3)
        self.assertEqual(jump_move.end_col, 2)
        # --- Fin Corrección ---

        self.assertEqual(jump_move.captured_pieces, [(4, 3)])

    def test_king_promotion_p1(self):
        """Verifica que una pieza P1 se convierte en rey."""
        self.board.board = [
            [cl.EMPTY for _ in range(8)] for _ in range(8)
        ]  # Tablero vacío
        self.board.board[1][0] = cl.P1_MAN  # P1 a punto de coronar

        move = cl.Move(start_pos=(1, 0), end_pos=(0, 1))
        new_board = self.board.apply_move(move)

        self.assertEqual(new_board.get_piece(0, 1), cl.P1_KING)  # Debe ser Rey P1

    # --- AÑADE MÁS TESTS ---
    # - Múltiples saltos
    # - Movimientos y saltos de Reyes (en todas direcciones)
    # - Condiciones de fin de juego (check_game_over)
    # - Intentar mover una pieza vacía o del oponente (no debería ser legal)
    # - Movimientos a casillas ocupadas (no debería ser legal)
    # - Casos de borde del tablero


if __name__ == "__main__":
    unittest.main()
