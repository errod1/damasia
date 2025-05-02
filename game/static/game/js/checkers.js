// game/static/game/js/checkers.js
//const ONGOING = 0;
const P1_WINS = 1;
const P2_WINS = 2;
//const DRAW = 3; // <-- Añade estado de empate

function getStatusHTML(status) {
    if (status === ONGOING) return '<span class="status-ongoing">Ongoing</span>';
    if (status === P1_WINS) return '<span class="status-win">Player 1 Wins</span>';
    if (status === P2_WINS) return '<span class="status-win">Player 2 Wins</span>';
    if (status === DRAW) return '<span class="status-draw">Tablas </span>'; // <-- Manejar empate
    return '<span>Unknown</span>';
}

document.addEventListener('DOMContentLoaded', () => {
    const boardElement = document.getElementById('checkers-board');
    const messageArea = document.getElementById('message-area');
    const currentTurnSpan = document.getElementById('current-turn');
    const gameStatusSpan = document.getElementById('game-status');
    const csrfToken = document.querySelector('meta[name="csrf-token"]').getAttribute('content');
    const movesProgressSpan = document.getElementById('moves-progress'); // <-- Obtener span del contador

    

    // ... (otras constantes y variables globales) ...
    let currentLegalMoves = []; // Para almacenar los movimientos legales del turno
    const LEGAL_MOVES_URL = `/game/${GAME_ID}/legal_moves/`; // Construir la URL dinámicamente

    let selectedPiece = null; // { row: r, col: c, element: tdElement }
    let legalMovesForSelected = []; // [{end_row: r, end_col: c, captured: [...]}, ...]

    // --- Función para obtener el TD de una celda ---
    function getTdElement(row, col) {
        // Asegúrate de que tu HTML tenga data-row/data-col en los TDs
        return boardElement.querySelector(`td[data-row="${row}"][data-col="${col}"]`);
    }

     // --- Función para obtener la pieza DENTRO de un TD ---
     function getPieceElement(td) {
        return td.querySelector('.piece');
    }

    // --- Función para limpiar resaltados ---
    function clearHighlights() {
        // Quitar selección de pieza
        const selectedTd = boardElement.querySelector('.selected');
        if (selectedTd) {
            selectedTd.classList.remove('selected');
        }
        // Quitar resaltado de movimientos válidos
        boardElement.querySelectorAll('.valid-move').forEach(td => {
            td.classList.remove('valid-move');
        });
        selectedPiece = null;
        legalMovesForSelected = [];
    }

    // --- Función para resaltar movimientos válidos ---
    function highlightValidMoves(moves) {
        moves.forEach(move => {
            const td = getTdElement(move.end_row, move.end_col);
            if (td) {
                td.classList.add('valid-move');
            }
        });
    }

    
    

    // --- Función para actualizar el tablero visualmente ---
    function updateBoardUI(newBoardState, newTurn, newStatus,newMovesProgress) {
        clearHighlights(); // Limpia selecciones anteriores
        MOVES_SINCE_PROGRESS = newMovesProgress;
        CURRENT_TURN = newTurn;
        GAME_STATUS = newStatus;
        currentTurnSpan.textContent = newTurn;
        // Actualiza el texto del estado (simplificado, puedes mejorarlo para usar las clases CSS)
        //gameStatusSpan.textContent = getStatusText(newStatus); 
        gameStatusSpan.innerHTML = getStatusHTML(newStatus);
        if(movesProgressSpan) { // <-- Actualizar span del contador
            movesProgressSpan.textContent = newMovesProgress;
       }
       

        for (let r = 0; r < newBoardState.length; r++) {
            for (let c = 0; c < newBoardState[r].length; c++) {
                const td = getTdElement(r, c);
                const pieceVal = newBoardState[r][c];
                const pieceContainer = td.querySelector('.piece-container');
                let pieceHTML = ''; // Vaciar por defecto

                if (pieceVal === P1_MAN) pieceHTML = '<div class="piece p1 man" data-piece="p1man"></div>';
                else if (pieceVal === P1_KING) pieceHTML = '<div class="piece p1 king" data-piece="p1king"></div>';
                else if (pieceVal === P2_MAN) pieceHTML = '<div class="piece p2 man" data-piece="p2man"></div>';
                else if (pieceVal === P2_KING) pieceHTML = '<div class="piece p2 king" data-piece="p2king"></div>';
                
                pieceContainer.innerHTML = pieceHTML;
            }
        }

        fetchLegalMoves();

         // Actualizar mensaje según estado y turno
         updateMessage();
    }

    // --- Actualizar getStatusText para devolver HTML con clases ---
    
    
    // --- Función auxiliar para obtener texto del estado ---
    function getStatusText(status) {
        if (status === 0) return 'Ongoing'; // ONGOING
        if (status === 1) return 'Player 1 Wins'; // P1_WINS
        if (status === 2) return 'Player 2 Wins'; // P2_WINS
        return 'Unknown';
    }

     // --- Función para actualizar el área de mensajes ---
     function updateMessage_old(message = "", isError = false, isThinking=false) {
        debugger;
        messageArea.textContent = message;
        messageArea.classList.remove('error', 'thinking');
        if (isError) {
            messageArea.classList.add('error');
        } else if (isThinking) {
             messageArea.classList.add('thinking');
        } else if (GAME_STATUS !== ONGOING) {
             messageArea.textContent = `Juego Terminado: ${getStatusText(GAME_STATUS)}`;
        } else if (isMyTurn()) {
            messageArea.textContent = `Tu turno (Jugador ${CURRENT_TURN}). Selecciona una pieza.`;
        } else {
            messageArea.textContent = `Esperando movimiento del Jugador ${CURRENT_TURN}...`;
        }
    }

    function updateMessage(message = "", isError = false, isThinking = false) {
        messageArea.textContent = message;
        messageArea.classList.remove('error', 'thinking');
        if (isError) {
            messageArea.classList.add('error');
        } else if (isThinking) {
            messageArea.classList.add('thinking');
        } else if (GAME_STATUS !== ONGOING) {
            // Mensaje genérico de fin de juego (getStatusHTML ya lo muestra)
            messageArea.textContent = `Juego Terminado. Resultado: ${getStatusHTML(GAME_STATUS)}`;
            messageArea.innerHTML = `Juego Terminado. Resultado: ${getStatusHTML(GAME_STATUS)}`; // Usar InnerHTML si status tiene spans
        } else if (isMyTurn()) {
            messageArea.textContent = `Tu turno (Jugador ${CURRENT_TURN}). Selecciona una pieza.`;
        } else {
            messageArea.textContent = `Esperando movimiento del Jugador ${CURRENT_TURN}...`;
        }
    }

    // --- Función para enviar el movimiento al backend ---
    async function sendMoveToServer(startRow, startCol, endRow, endCol) {
        updateMessage("Enviando movimiento...", false, false); // Mensaje temporal
        try {
            const response = await fetch(MAKE_MOVE_URL, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrfToken
                },
                body: JSON.stringify({
                    start_row: startRow,
                    start_col: startCol,
                    end_row: endRow,
                    end_col: endCol
                })
            });

            if (!response.ok) {
                 // Intenta obtener más detalles del error si el backend los envía
                 let errorData = { detail: `Error del servidor: ${response.status}`};
                 try {
                     errorData = await response.json();
                 } catch(e) { /* No hacer nada si el cuerpo no es JSON */}
                 throw new Error(errorData.detail || `Error HTTP ${response.status}`);
            }

            const data = await response.json();

            if (data.success) {
                console.log(`respuesta ${MAKE_MOVE_URL}`);
                console.table(data);
                updateBoardUI(data.board_state, data.current_turn, data.status, data.moves_since_progress);
                //updateBoardUI(data.board_state, data.current_turn, data.status, data.moves_since_progress); // <-- Llamada ACTUALIZADA (línea ~185)
                if (data.ai_thinking) {
                    updateMessage("IA pensando...", false, true);
                }
                 // La función updateMessage llamada dentro de updateBoardUI manejará el mensaje final
            } else {
                // Error de lógica del juego (p.ej., movimiento inválido)
                updateMessage(data.error || "Error desconocido al procesar el movimiento.", true);
                clearHighlights(); // Limpiar selección si el movimiento fue inválido
            }

        } catch (error) {
            console.error("Error en fetch:", error);
            updateMessage(`Error de red o servidor: ${error.message}`, true);
            clearHighlights();
        }
    }

    // --- Inicialización al cargar ---
    if (gameStatusSpan) { // Asegura que el span existe (porque hay un juego)
        gameStatusSpan.innerHTML = getStatusHTML(GAME_STATUS); // Establece estado inicial
    }
    if(movesProgressSpan){
        movesProgressSpan.textContent = MOVES_SINCE_PROGRESS; // Establece contador inicial
    }
    updateMessage(); // Llama para poner el mensaje inicial correcto


    // --- Lógica de Click en el Tablero ---
    boardElement.addEventListener('click', (event) => {
        console.log(`>>>>>>>>> STATUS: ${GAME_STATUS}`);
        if (GAME_STATUS !== ONGOING) {
            updateMessage("El juego ha terminado.", false);
            return; // No hacer nada si el juego terminó
        }

        if (!isMyTurn()) {
             updateMessage(`No es tu turno (Jugador ${CURRENT_TURN}).`, true);
             return; // No es el turno del jugador humano (asumiendo P1 es humano)
        }


        const clickedTd = event.target.closest('td');
    if (!clickedTd) return;

    const row = parseInt(clickedTd.dataset.row);
    const col = parseInt(clickedTd.dataset.col);
    const pieceElement = getPieceElement(clickedTd);

    // --- Caso 1: Click en un destino válido (ya hay pieza seleccionada) ---
    if (selectedPiece && clickedTd.classList.contains('valid-move')) {
        // ¡Esta parte ahora debería funcionar!
        console.log("Attempting move to valid square:", row, col); // Debug
        sendMoveToServer(selectedPiece.row, selectedPiece.col, row, col);

    // --- Caso 2: Click en una pieza propia (seleccionar/cambiar selección) ---
    } else if (pieceElement) {
        const isP1Piece = pieceElement.classList.contains('p1');
        const isP2Piece = pieceElement.classList.contains('p2');

        if ((CURRENT_TURN === 1 && isP1Piece) || (CURRENT_TURN === 2 && isP2Piece)) {
            clearHighlights(); // Limpia selección/movimientos anteriores
            selectedPiece = { row, col, element: clickedTd };
            clickedTd.classList.add('selected');
            updateMessage(`Pieza seleccionada en (${row}, ${col}). Haz clic en un destino.`);

            // *** NUEVO: Filtrar y resaltar movimientos ***
            const possibleMoves = currentLegalMoves.filter(move =>
                move.start_row === row && move.start_col === col
            );
            console.log("Possible moves for selected piece:", possibleMoves); // Debug
            highlightValidMoves(possibleMoves); // Resalta los destinos
            // *** FIN NUEVO ***

        } else {
            clearHighlights();
            updateMessage("No puedes mover la pieza del oponente.", true);
        }
    // --- Caso 3: Click en casilla vacía (o fuera de pieza) sin ser destino válido ---
    } else {
        clearHighlights();
        updateMessage("Selecciona una de tus piezas para mover.");
    }
    });

     // --- Función para determinar si es el turno del jugador local ---
     // Simple: asume que HUMANO siempre juega si su tipo está configurado como HUMAN
     function isMyTurn() {
         if (CURRENT_TURN === 1 && PLAYER1_TYPE === 'HUMAN') return true;
         if (CURRENT_TURN === 2 && PLAYER2_TYPE === 'HUMAN') return true;
         // Podrías tener lógica para Humano vs Humano aquí también
         return false;
     }
     
     // --- Mensaje inicial ---
     updateMessage();

     // --- Llamada inicial para obtener movimientos legales ---
     fetchLegalMoves();
     
     // --- Opcional: Llamada inicial para obtener movimientos legales ---
     // Si quisiéramos resaltar los movimientos posibles al cargar la página/inicio de turno
     // necesitaríamos una nueva URL/vista en Django que devuelva los movimientos legales
     // para el jugador actual en formato JSON.
     // fetchLegalMoves(); 

     async function fetchLegalMoves() {
        if (GAME_STATUS !== ONGOING || !isMyTurn()) {
             currentLegalMoves = []; // Limpiar si no es mi turno o el juego terminó
             clearHighlights(); // Limpia cualquier resaltado residual
             return;
        }
        try {
            console.log("Fetching legal moves from:", LEGAL_MOVES_URL); // Debug
            const response = await fetch(LEGAL_MOVES_URL); // Petición GET por defecto
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            const data = await response.json();
            console.log("Received legal moves:", data.legal_moves); // Debug
            currentLegalMoves = data.legal_moves || []; // Almacena los movimientos
             // Podrías llamar a updateMessage aquí si quieres un mensaje específico
        } catch (error) {
            console.error("Error fetching legal moves:", error);
            updateMessage("Error al obtener movimientos legales.", true);
            currentLegalMoves = []; // Asegura que esté vacío en caso de error
        }
    }


}); // Fin del DOMContentLoaded