# from django.shortcuts import render
# from django.views.decorators.http import require_POST # Para asegurar que sea POST
# from django.views.decorators.csrf import ensure_csrf_cookie # Puede ayudar con CSRF

# from .models import Game
# from checkers_logic import Board, Move, ONGOING, P1_WINS, P2_WINS # Importa lo necesario
# # IMPORTANTE: Importa tu lógica de IA
# import checkers_ai 

# # Create your views here.
# # game/views.py

# from django.shortcuts import render, redirect, get_object_or_404
# from django.http import HttpResponse, JsonResponse # JsonResponse será útil después
# from django.urls import reverse

# from .models import Game
# from checkers_logic import Board # Importa tu lógica del juego

# game/views.py
import json
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, JsonResponse
from django.urls import reverse
from django.views.decorators.http import require_POST
from django.http import JsonResponse
from jsonschema import ValidationError
# from django.views.decorators.csrf import ensure_csrf_cookie # Descomentado por ahora

from .models import Game, MOVES_LIMIT_FOR_DRAW
# Asegúrate de importar TODAS las constantes necesarias aquí:
from checkers_logic import Board, Move, EMPTY, P1_MAN, P1_KING, P2_MAN, P2_KING, ONGOING, P1_WINS, P2_WINS, DRAW

# IMPORTANTE: Importa tu lógica de IA
import checkers_ai 

def _prepare_board_context(game_obj):
    """Función auxiliar para preparar el contexto del tablero."""
    if not game_obj or not game_obj.board_state:
        return None

    board_data = []
    rows = len(game_obj.board_state)
    cols = len(game_obj.board_state[0]) if rows > 0 else 0

    for r in range(rows):
        row_data = []
        for c in range(cols):
            piece_val = game_obj.board_state[r][c]
            is_dark = (r + c) % 2 != 0
            # Crear un diccionario para cada celda
            row_data.append({
                'row': r,
                'col': c,
                'piece_val': piece_val,
                'is_dark': is_dark
            })
        board_data.append(row_data)

    return {
        'game': game_obj,
        'board_data': board_data, # Pasamos la nueva estructura
         # Ya no necesitamos pasar rows/cols/board por separado
        'EMPTY': 0, 'P1_MAN': 1, 'P2_MAN': 2, 'P1_KING': 3, 'P2_KING': 4, 'ONGOING': ONGOING, 'DRAW': DRAW,
        'MOVES_LIMIT_FOR_DRAW': game_obj.limit_draw
    }


def index(request):
    game_to_display = None
    last_game_id = request.session.get('last_game_id')
    if last_game_id:
        try:
            game_to_display = Game.objects.get(pk=last_game_id)
        except Game.DoesNotExist:
            request.session['last_game_id'] = None

    # Preparar contexto usando la función auxiliar
    context = _prepare_board_context(game_to_display) if game_to_display else {'game': None}
    return render(request, 'game/index.html', context or {}) # Pasa diccionario vacío si context es None


# La vista index podría necesitar cargar el último juego (ver paso extra al final)
def index_old(request):
    """
    Renderiza la página principal.
    Puede opcionalmente cargar y mostrar el último juego activo (requiere lógica adicional).
    Por ahora, solo muestra el formulario.
    """
    # Lógica futura para cargar último juego iría aquí
    game_to_display = None
    context = {'game': game_to_display} # Pasa None si no hay juego a mostrar inicialmente
     # Necesitamos pasar las constantes para el tablero si game_to_display no es None
    if game_to_display:
         context.update({
            'board': game_to_display.board_state,
            'rows': range(len(game_to_display.board_state)),
            'cols': range(len(game_to_display.board_state[0]) if game_to_display.board_state else 0),
            'EMPTY': 0, 'P1_MAN': 1, 'P2_MAN': 2, 'P1_KING': 3, 'P2_KING': 4, 'ONGOING': ONGOING
         })
    return render(request, 'game/index.html', context)


@require_POST # Sigue siendo POST desde el formulario
def create_game(request):
    """
    Crea un nuevo juego y renderiza la página index mostrando ese juego.
    """
    try:
        chosen_depth = int(request.POST.get('ai_depth', Game._meta.get_field('ai_search_depth').get_default()))
        validators = Game._meta.get_field('ai_search_depth').validators
        for validator in validators:
             validator(chosen_depth)
    except (ValueError, TypeError, ValidationError):
        chosen_depth = Game._meta.get_field('ai_search_depth').get_default()
        print(f"Advertencia: Profundidad inválida recibida, usando default: {chosen_depth}")

    try:
        limit_draw = int(request.POST.get('limit_draw', Game._meta.get_field('limit_draw').get_default()))
        validators = Game._meta.get_field('limit_draw').validators
        for validator in validators:
             validator(limit_draw)
    except (ValueError, TypeError, ValidationError):
        limit_draw = Game._meta.get_field('limit_draw').get_default()
        print(f"Advertencia: movimientos tablas invalidad recibida, usando default: {chosen_depth}")

    initial_board = Board()
    board_state_list = initial_board.board
    new_game = Game.objects.create(
        board_state=board_state_list,
        current_turn=1, player1_type='HUMAN', player2_type='AI', ai_search_depth=chosen_depth,
        limit_draw=limit_draw
    )
    request.session['last_game_id'] = new_game.id

    context = _prepare_board_context(new_game)
    
    # --- DEBUGGING ---
    print("-" * 20)
    print("Contexto pasado desde create_game:")
    print("Tiene 'game':", 'game' in context and context['game'] is not None)
    print("Tiene 'board_data':", 'board_data' in context)
    if 'board_data' in context:
         print("Longitud de board_data:", len(context['board_data']))
         if len(context['board_data']) > 0:
              print("Longitud de la primera fila de board_data:", len(context['board_data'][0]))
    print("-" * 20)
    # --- FIN DEBUGGING ---
    # --- DEBUGGING ---
    print("-" * 20)
    print("Contexto pasado desde create_game:")
    print("Tiene 'game':", 'game' in context and context['game'] is not None)
    print("Tiene 'board_data':", 'board_data' in context)
    if 'board_data' in context:
         print("Longitud de board_data:", len(context['board_data']))
         if len(context['board_data']) > 0:
              print("Longitud de la primera fila de board_data:", len(context['board_data'][0]))
    print("-" * 20)
    # --- FIN DEBUGGING ---

    return render(request, 'game/index.html', context)

# Vista para mostrar una partida específica
def game_view(request, game_id):
    # Obtiene el objeto Game de la BD o devuelve un error 404 si no existe
    game = get_object_or_404(Game, pk=game_id)

     # --- DEBUG ---
    print("----- DEBUG: Datos del tablero en la vista -----")
    print(game.board_state)
    print("Tipo:", type(game.board_state)) 
    print("---------------------------------------------")
    # --- FIN DEBUG ---

    # Prepara el contexto para pasar datos a la plantilla
    context = {
        'game': game,
        'board': game.board_state, # Pasa el estado del tablero (lista de listas)
        'rows': range(len(game.board_state)),      # Para iterar en la plantilla
        'cols': range(len(game.board_state[0]) if game.board_state else 0), # Para iterar
        # Pasa las constantes para usarlas en la plantilla si es necesario
        'EMPTY': 0,
        'P1_MAN': 1,
        'P2_MAN': 2,
        'P1_KING': 3,
        'P2_KING': 4,
        'ONGOING': ONGOING,
    }
    return render(request, 'game/game_detail.html', context)

@require_POST # Asegura que solo acepte peticiones POST
def make_move(request, game_id):
    """
    Maneja la petición AJAX para realizar un movimiento en el juego.
    Valida el movimiento humano, lo aplica, actualiza el estado,
    comprueba el fin del juego (victoria/derrota/empate),
    llama a la IA si es su turno y el juego continúa,
    aplica el movimiento de la IA, y devuelve el estado final.
    """
    game = get_object_or_404(Game, pk=game_id)
    ai_thinking_flag = False # Flag para indicar al frontend si la IA está pensando

    # 1. Verificar si el juego ya terminó previamente
    if game.status != ONGOING:
        return JsonResponse({'success': False, 'error': 'El juego ya ha terminado.'}, status=400)

    # 2. Verificar si es el turno del jugador humano correcto
    is_player1_turn = game.current_turn == 1
    is_player2_turn = game.current_turn == 2
    current_player_is_human = (is_player1_turn and game.player1_type == 'HUMAN') or \
                              (is_player2_turn and game.player2_type == 'HUMAN')

    if not current_player_is_human:
         # Salvaguarda por si el frontend envía en un turno incorrecto
         return JsonResponse({'success': False, 'error': 'No es el turno de un jugador humano.'}, status=400)

    # 3. Parsear los datos del movimiento del request JSON
    try:
        data = json.loads(request.body)
        start_row = int(data.get('start_row'))
        start_col = int(data.get('start_col'))
        end_row = int(data.get('end_row'))
        end_col = int(data.get('end_col'))
        # Validar que las coordenadas son números (básico)
        if not all(isinstance(i, int) for i in [start_row, start_col, end_row, end_col]):
             raise ValueError("Coordenadas deben ser enteros.")
    except (json.JSONDecodeError, ValueError, TypeError) as e:
        return JsonResponse({'success': False, 'error': f'Datos inválidos en la petición: {e}'}, status=400)

    # 4. Crear instancia del tablero lógico y obtener movimientos legales
    current_board = Board(rows=len(game.board_state), cols=len(game.board_state[0]))
    current_board.board = game.board_state # Cargar estado actual desde la BD
    legal_moves = current_board.get_legal_moves(game.current_turn)

    # 5. Validar si el movimiento recibido es legal
    received_move = None
    for move in legal_moves:
        # Comparamos inicio y fin. NOTA: Podría ser insuficiente si hay
        # múltiples saltos posibles entre las mismas casillas de inicio/fin.
        # Una mejora sería pasar un identificador único del movimiento desde el frontend.
        if move.start_row == start_row and move.start_col == start_col and \
           move.end_row == end_row and move.end_col == end_col:
            received_move = move # Guardamos el objeto Move completo (incluye capturas)
            break

    if received_move is None:
        return JsonResponse({'success': False, 'error': 'Movimiento ilegal o no encontrado.'}, status=400)

    # --- 6. Aplicar Movimiento Humano ---
    new_board_obj, progress_made_human = current_board.apply_move(received_move)

    # 7. Actualizar contador de empate
    if progress_made_human:
        game.moves_since_progress = 0
        print(f"[{game.id}] Progreso Humano. Contador reiniciado.")
    else:
        game.moves_since_progress += 1
        print(f"[{game.id}] Sin Progreso Humano. Contador: {game.moves_since_progress}/{MOVES_LIMIT_FOR_DRAW}")

    # 8. Actualizar el estado del tablero en el objeto Game
    game.board_state = new_board_obj.board

    # 9. Determinar quién jugaría a continuación
    actual_next_turn = 3 - game.current_turn

    # 10. Comprobar estado del juego (Win/Loss/Draw) DESPUÉS del movimiento humano
    win_loss_status = new_board_obj.check_game_over(actual_next_turn) # ¿Puede moverse el siguiente jugador?

    # 11. Actualizar estado final y turno CONDICIONALMENTE
    if win_loss_status != ONGOING:
        game.status = win_loss_status
        print(f"[{game.id}] Juego Terminado por Win/Loss: Status {game.status}")
        # No se cambia el turno si el juego termina
    elif game.moves_since_progress >= MOVES_LIMIT_FOR_DRAW:
        game.status = DRAW
        print(f"[{game.id}] Juego Terminado por Empate ({game.moves_since_progress} movimientos)")
        # No se cambia el turno si el juego termina
    else:
        # El juego continúa, pasar el turno al siguiente jugador
        game.status = ONGOING
        game.current_turn = actual_next_turn
        print(f"[{game.id}] Juego continúa. Turno pasa a Jugador {game.current_turn}")

    # 12. Guardar estado intermedio (después del humano, antes de la IA)
    game.is_new=False; # marcar como juego no nuevo (para eliminar si no se ha jugado y no guardar registros sin haber empezado a jugar)
    game.save()

    # 13. Determinar si la IA debe jugar
    next_player_is_ai = False
    if game.status == ONGOING: # Solo si el juego no ha terminado
        is_player1_now = game.current_turn == 1
        is_player2_now = game.current_turn == 2
        if (is_player1_now and game.player1_type == 'AI') or \
           (is_player2_now and game.player2_type == 'AI'):
            next_player_is_ai = True
            ai_thinking_flag = True # Informar al frontend que la IA *va* a pensar

    # --- 14. Turno de la IA (si aplica) ---
    if next_player_is_ai:
        ai_depth = game.ai_search_depth
        print(f"[{game.id}] >>>>>>> Turno IA (Jugador {game.current_turn}). Profundidad: {ai_depth}")

        # Crear tablero para la IA con el estado más reciente
        ai_board = Board(rows=len(game.board_state), cols=len(game.board_state[0]))
        ai_board.board = game.board_state

        # Llamar a la función de búsqueda de la IA
        ai_move = checkers_ai.find_best_move(ai_board, game.current_turn, depth=ai_depth)

        if ai_move:
            # 14.1 Aplicar movimiento de la IA
            print(f"[{game.id}] IA (Profundidad {ai_depth}) elige mover: {ai_move}")
            final_board_obj, progress_made_ai = ai_board.apply_move(ai_move)

            # 14.2 Actualizar contador de empate tras IA
            if progress_made_ai:
                game.moves_since_progress = 0
                print(f"[{game.id}] Progreso IA. Contador reiniciado.")
            else:
                game.moves_since_progress += 1
                print(f"[{game.id}] Sin Progreso IA. Contador: {game.moves_since_progress}/{MOVES_LIMIT_FOR_DRAW}")

            # 14.3 Actualizar estado del tablero tras IA
            game.board_state = final_board_obj.board

            # 14.4 Determinar quién jugaría después de la IA
            turn_after_ai = 3 - game.current_turn

            # 14.5 Comprobar estado del juego tras IA
            win_loss_status_after_ai = final_board_obj.check_game_over(turn_after_ai)

            # 14.6 Actualizar estado final y turno CONDICIONALMENTE tras IA
            if win_loss_status_after_ai != ONGOING:
                game.status = win_loss_status_after_ai
                print(f"[{game.id}] Juego Terminado por Win/Loss tras IA: Status {game.status}")
                # No cambiar turno
            elif game.moves_since_progress >= MOVES_LIMIT_FOR_DRAW:
                 game.status = DRAW
                 print(f"[{game.id}] Juego Terminado por Empate ({game.moves_since_progress}) tras IA")
                 # No cambiar turno
            else:
                 # El juego continúa, devolver turno al siguiente jugador (humano)
                 game.status = ONGOING
                 game.current_turn = turn_after_ai
                 print(f"[{game.id}] Juego continúa tras IA. Turno pasa a Jugador {game.current_turn}")

            # 14.7 Guardar el estado final después del turno completo de la IA
            game.save()
            ai_thinking_flag = False # La IA ya terminó de pensar para esta respuesta

        else:
            # La IA no encontró movimiento (esto implica que el juego debería haber terminado)
            print(f"[{game.id}] Advertencia: La IA (Jugador {game.current_turn}) no encontró movimiento.")
            # El estado guardado previamente ya debería reflejar la victoria del oponente
            # No es necesario forzar el estado aquí si check_game_over es correcto
            ai_thinking_flag = False # No hubo pensamiento activo o ya terminó sin éxito

    # --- 15. Preparar respuesta JSON ---
    response_data = {
        'success': True,
        'board_state': game.board_state,
        'current_turn': game.current_turn,
        'status': game.status,               # 0, 1, 2, o 3
        'status_text': game.get_status_display(), # Texto descriptivo del estado
        'ai_thinking': ai_thinking_flag,      # ¿Está la IA pensando (o acaba de terminar)?
        'moves_since_progress': game.moves_since_progress, # Contador de empate
        'draw_limit': MOVES_LIMIT_FOR_DRAW   # Límite para empate
    }
    return JsonResponse(response_data)

def make_move_old(request, game_id):
    game = get_object_or_404(Game, pk=game_id)
    ai_thinking_flag = False # Para indicar al frontend si la IA va a pensar

    # Verificar si el juego ya terminó
    if game.status != ONGOING:
        return JsonResponse({'success': False, 'error': 'El juego ya ha terminado.'}, status=400)

    # Verificar si es el turno del jugador correcto (según el tipo)
    is_player1_turn = game.current_turn == 1
    is_player2_turn = game.current_turn == 2
    
    # Determinar si el jugador actual es humano
    current_player_is_human = (is_player1_turn and game.player1_type == 'HUMAN') or \
                              (is_player2_turn and game.player2_type == 'HUMAN')

    if not current_player_is_human:
         # Esto no debería pasar si el frontend funciona bien, pero es una salvaguarda
         return JsonResponse({'success': False, 'error': 'No es el turno de un jugador humano.'}, status=400)

    try:
        data = json.loads(request.body)
        start_row = int(data.get('start_row'))
        start_col = int(data.get('start_col'))
        end_row = int(data.get('end_row'))
        end_col = int(data.get('end_col'))
    except (json.JSONDecodeError, ValueError, TypeError) as e:
        return JsonResponse({'success': False, 'error': f'Datos inválidos: {e}'}, status=400)

    # Crear instancia del tablero desde el estado guardado
    current_board = Board(rows=len(game.board_state), cols=len(game.board_state[0]))
    current_board.board = game.board_state # Cargar estado

    # Obtener movimientos legales para el jugador actual
    legal_moves = current_board.get_legal_moves(game.current_turn)

    # Buscar el movimiento específico recibido entre los legales
    received_move = None
    for move in legal_moves:
        # Comparamos solo inicio y fin. IMPORTANTE: Esto asume que no hay dos
        # movimientos distintos (ej. saltos diferentes) que empiecen y terminen
        # en las mismas casillas. Si eso es posible, la validación necesita ser más robusta.
        if move.start_row == start_row and move.start_col == start_col and \
           move.end_row == end_row and move.end_col == end_col:
            received_move = move # Usamos el objeto Move completo por si tiene capturas
            break

    if received_move is None:
        return JsonResponse({'success': False, 'error': 'Movimiento ilegal.'}, status=400)

    # --- Movimiento Humano Válido ---
    # Aplicar el movimiento
    new_board_obj = current_board.apply_move(received_move)
    game.board_state = new_board_obj.board # Actualizar estado
    game.current_turn = 3 - game.current_turn # Cambiar turno (1->2, 2->1)
    game.is_new=False

    # Comprobar si el juego terminó después del movimiento humano
    game.status = new_board_obj.check_game_over(game.current_turn) # Comprueba si el *nuevo* jugador puede moverse
    
    next_player_is_ai = False
    if game.status == ONGOING:
         # Verificar si el *siguiente* jugador es la IA
         is_player1_next = game.current_turn == 1
         is_player2_next = game.current_turn == 2
         if (is_player1_next and game.player1_type == 'AI') or \
            (is_player2_next and game.player2_type == 'AI'):
             next_player_is_ai = True
             ai_thinking_flag = True # Indicar al frontend


    # Guardar estado parcial (después del humano, antes de la IA si aplica)
    # Es útil guardar aquí por si la IA tarda mucho o falla
    game.save() 

    # --- Turno de la IA (si aplica y el juego continúa) ---
    if next_player_is_ai:
         
         # --- CAMBIO AQUÍ: Lee la profundidad del juego actual ---
         ai_depth_for_this_game = game.ai_search_depth
         # ----------------------------------------------------
         print(f">>>>>>>Turno de la IA (Jugador {game.current_turn}). Profundidad: {ai_depth_for_this_game}")


         #print(f"Turno de la IA (Jugador {game.current_turn}). Profundidad: {8}") # Usa tu profundidad
         # Crear tablero para la IA con el estado ACTUALIZADO
         ai_board = Board(rows=len(game.board_state), cols=len(game.board_state[0]))
         ai_board.board = game.board_state

         #ai_move = checkers_ai.find_best_move(ai_board, game.current_turn, depth=5) # Usa una profundidad razonable para la web (5-6)
         ai_move = checkers_ai.find_best_move(ai_board, game.current_turn, depth=ai_depth_for_this_game)

         if ai_move:
             print(f"IA elige mover: {ai_move}")
             final_board_obj = ai_board.apply_move(ai_move)
             game.board_state = final_board_obj.board
             game.current_turn = 3 - game.current_turn # Devolver turno al humano
             # Comprobar estado del juego DESPUÉS del movimiento de la IA
             game.status = final_board_obj.check_game_over(game.current_turn)
             game.save() # Guardar el estado final después de la IA
             ai_thinking_flag = False # La IA ya terminó
         else:
             # La IA no encontró movimiento (el juego debería haber terminado, pero por si acaso)
             print(f"Advertencia: La IA (Jugador {3 - game.current_turn}) no encontró movimiento.")
             # El estado del juego ya debería reflejar la victoria humana si la IA no tiene movs
             # game.status = P1_WINS if game.current_turn == 2 else P2_WINS # Redundante si check_game_over funciona bien
             # game.save()
             pass # No hacer nada extra, el estado guardado antes del turno AI es el final


    # Preparar respuesta JSON final
    response_data = {
        'success': True,
        'board_state': game.board_state,
        'current_turn': game.current_turn,
        'status': game.status,
        'status_text': game.get_status_display(), # Enviar texto también puede ser útil
        'ai_thinking': ai_thinking_flag # Informar si la IA empezó a pensar (aunque podría haber terminado ya)
    }
    return JsonResponse(response_data)
    

# --- NUEVA VISTA ---
def get_legal_moves_json(request, game_id):
    """Devuelve los movimientos legales para el jugador actual en formato JSON."""
    game = get_object_or_404(Game, pk=game_id)

    # Solo devolver movimientos si el juego está en curso
    if game.status != ONGOING:
        return JsonResponse({'legal_moves': []})

    # Crear tablero desde el estado actual
    current_board = Board(rows=len(game.board_state), cols=len(game.board_state[0]))
    current_board.board = game.board_state

    # Obtener movimientos legales del backend
    legal_moves_objects = current_board.get_legal_moves(game.current_turn)

    # Convertir los objetos Move a un formato JSON simple (lista de diccionarios)
    legal_moves_data = []
    for move in legal_moves_objects:
        legal_moves_data.append({
            'start_row': move.start_row,
            'start_col': move.start_col,
            'end_row': move.end_row,
            'end_col': move.end_col,
            # Incluir capturas si quieres usarlas en el frontend (opcional por ahora)
            # 'captured': move.captured_pieces
        })

    return JsonResponse({'legal_moves': legal_moves_data})


def get_legal_moves_view(request, game_id):
    game = get_object_or_404(Game, pk=game_id)
    if game.status != ONGOING:
        return JsonResponse({'legal_moves': []}) # No hay movs si terminó

    board = Board(rows=len(game.board_state), cols=len(game.board_state[0]))
    board.board = game.board_state
    legal_moves_objects = board.get_legal_moves(game.current_turn)

    # Convertir objetos Move a diccionarios serializables
    serializable_moves = []
    for move in legal_moves_objects:
        serializable_moves.append({
            'start_row': move.start_row,
            'start_col': move.start_col,
            'end_row': move.end_row,
            'end_col': move.end_col,
            'captured_pieces': move.captured_pieces, # Lista de tuplas (r,c)
        })

    return JsonResponse({'legal_moves': serializable_moves})