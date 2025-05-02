# game/models.py

from django.db import models
from django.contrib.postgres.fields import ArrayField # Si decides usar arrays directamente
from django.utils import timezone # Para timestamps
from django.core.validators import MaxValueValidator, MinValueValidator # Para limitar la profundidad
import json # Para serializar/deserializar el tablero si usamos TextField

# Importa tus constantes de lógica si las necesitas directamente aquí
# O mejor aún, define nuevas constantes específicas para los tipos de jugador/estado en el modelo
from checkers_logic import EMPTY, P1_MAN, P1_KING, P2_MAN, P2_KING, ONGOING, P1_WINS, P2_WINS, DRAW

# --- Constante para el límite de empate ---
# 80 medio-movimientos = 40 movimientos completos de ambos jugadores
MOVES_LIMIT_FOR_DRAW = 40

class Game(models.Model):
    """Representa una partida de Damas en la base de datos."""

    PLAYER_TYPE_CHOICES = [
        ('HUMAN', 'Human'),
        ('AI', 'AI'),
    ]

    GAME_STATUS_CHOICES = [
        (ONGOING, 'Ongoing'),
        (P1_WINS, 'Player 1 Wins'),
        (P2_WINS, 'Player 2 Wins'),
        (DRAW, 'Draw'), # <-- Añade la opción de Empate
        # Añade DRAW si lo implementas en la lógica
    ]

    # Campo para almacenar el tablero. JSONField es ideal.
    # Guarda la estructura de lista de listas directamente en la BD.
    board_state = models.JSONField(default=list)

    # Alternativa con TextField (requiere serialización manual):
    # board_state_text = models.TextField(default='[]')

    player1_type = models.CharField(max_length=5, choices=PLAYER_TYPE_CHOICES, default='HUMAN')
    player2_type = models.CharField(max_length=5, choices=PLAYER_TYPE_CHOICES, default='AI')

    # Guarda qué jugador tiene el turno (1 o 2)
    current_turn = models.IntegerField(default=1)

    # Estado actual del juego
    status = models.IntegerField(choices=GAME_STATUS_CHOICES, default=ONGOING)

    # Timestamps automáticos
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # --- NUEVO CAMPO ---
    ai_search_depth = models.IntegerField(
        default=5, # Profundidad por defecto (ajusta según veas conveniente)
        validators=[
            MinValueValidator(1), # Mínimo 1 nivel
            MaxValueValidator(8)  # Máximo 8 (o el límite práctico que quieras)
        ],
        help_text="Profundidad de búsqueda para la IA (más alto = más 'inteligente' pero más lento)"
    )
    # --- FIN NUEVO CAMPO ---

     # --- NUEVO CAMPO ---
    limit_draw = models.IntegerField(
        default=10, # Profundidad por defecto (ajusta según veas conveniente)
        validators=[
            MinValueValidator(10), # Mínimo 1 nivel
            MaxValueValidator(80)  # Máximo 8 (o el límite práctico que quieras)
        ],
        help_text="Maximo numero de movimientos para tablas,desde 10 (facil) hasta 80 (dificil)"
    ) 
    # --- FIN NUEVO CAMPO ---

    # --- NUEVO CAMPO ---
    moves_since_progress = models.IntegerField(
        default=0,
        help_text="Contador de medio-movimientos desde la última captura o movimiento de peón."
    )
    # --- FIN NUEVO CAMPO ---

    # --- NUEVO CAMPO
    is_new = models.BooleanField(default=True)
    # --- FIN NUEVO CAMPO

    # (Opcional) Para almacenar el historial de movimientos si quieres replay
    # move_history = models.JSONField(default=list)

    def __str__(self):
        #return f"Game {self.id} - Status: {self.get_status_display()}"
        #return f"Game {self.id} - Status: {self.get_status_display()} (AI Depth: {self.ai_search_depth})"
        return f"Game {self.id} - Status: {self.get_status_display()} (AI Depth: {self.ai_search_depth}, Prog: {self.moves_since_progress}/{MOVES_LIMIT_FOR_DRAW})"
    

    # Métodos útiles (opcional pero recomendado)

    # Si usas TextField para el tablero:
    # def get_board_list(self):
    #     """ Convierte el texto del tablero a lista de listas """
    #     try:
    #         return json.loads(self.board_state_text)
    #     except json.JSONDecodeError:
    #         return [] # O maneja el error como prefieras

    # def set_board_list(self, board_list):
    #     """ Convierte lista de listas a texto para guardar """
    #     self.board_state_text = json.dumps(board_list)

    # Podrías añadir métodos aquí para obtener/setear el tablero
    # interactuando con tu clase Board de checkers_logic.py si lo ves útil,
    # pero usualmente esa conversión se hace en las vistas (views.py).