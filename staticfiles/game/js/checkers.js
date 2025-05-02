// game/static/game/js/checkers.js

document.addEventListener('DOMContentLoaded', () => {
    const boardElement = document.getElementById('checkers-board');
    const messageArea = document.getElementById('message-area');
    const currentTurnSpan = document.getElementById('current-turn');
    const gameStatusSpan = document.getElementById('game-status');
    const csrfToken = document.querySelector('meta[name="csrf-token"]').getAttribute('content');

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
    function updateBoardUI(newBoardState, newTurn, newStatus) {
        clearHighlights(); // Limpia selecciones anteriores
        CURRENT_TURN = newTurn;
        GAME_STATUS = newStatus;
        currentTurnSpan.textContent = newTurn;
        // Actualiza el texto del estado (simplificado, puedes mejorarlo para usar las clases CSS)
        gameStatusSpan.textContent = getStatusText(newStatus); 

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
         // Actualizar mensaje según estado y turno
         updateMessage();
    }
    
    // --- Función auxiliar para obtener texto del estado ---
    function getStatusText(status) {
        if (status === 0) return 'Ongoing'; // ONGOING
        if (status === 1) return 'Player 1 Wins'; // P1_WINS
        if (status === 2) return 'Player 2 Wins'; // P2_WINS
        return 'Unknown';
    }

     // --- Función para actualizar el área de mensajes ---
     function updateMessage(message = "", isError = false, isThinking=false) {
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
                updateBoardUI(data.board_state, data.current_turn, data.status);
                 // Mensaje después de actualizar la UI
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

    // --- Lógica de Click en el Tablero ---
    boardElement.addEventListener('click', (event) => {
        if (GAME_STATUS !== ONGOING) {
            updateMessage("El juego ha terminado.", false);
            return; // No hacer nada si el juego terminó
        }

        if (!isMyTurn()) {
             updateMessage(`No es tu turno (Jugador ${CURRENT_TURN}).`, true);
             return; // No es el turno del jugador humano (asumiendo P1 es humano)
        }


        const clickedTd = event.target.closest('td'); // Asegura que clickeamos en un TD
        if (!clickedTd) return;

        const row = parseInt(clickedTd.dataset.row);
        const col = parseInt(clickedTd.dataset.col);
        const pieceElement = getPieceElement(clickedTd);

        // --- Caso 1: Click en un destino válido (ya hay pieza seleccionada) ---
        if (selectedPiece && clickedTd.classList.contains('valid-move')) {
            // Encuentra el move object correspondiente (necesitamos capturas si las hay)
            // Por ahora, asumimos que no necesitamos pasar las capturas explícitamente,
            // el backend las validará. Podríamos mejorarlo pasando el move completo.
            sendMoveToServer(selectedPiece.row, selectedPiece.col, row, col);

        // --- Caso 2: Click en una pieza propia (seleccionar/cambiar selección) ---
        } else if (pieceElement) {
             // Determinar si la pieza pertenece al jugador actual
            const isP1Piece = pieceElement.classList.contains('p1');
            const isP2Piece = pieceElement.classList.contains('p2');

            if ((CURRENT_TURN === 1 && isP1Piece) || (CURRENT_TURN === 2 && isP2Piece)) {
                 // Es una pieza propia, seleccionarla
                clearHighlights(); // Limpia selección/movimientos anteriores
                selectedPiece = { row, col, element: clickedTd };
                clickedTd.classList.add('selected');
                updateMessage(`Pieza seleccionada en (${row}, ${col}). Haz clic en un destino.`);
                
                // *** MEJORA FUTURA: ***
                // Aquí podríamos hacer una llamada AJAX para obtener SOLO los
                // movimientos legales para ESTA pieza específica y resaltarlos.
                // Por ahora, no resaltamos destinos específicos al seleccionar.
                // O, podríamos pre-cargar TODOS los movimientos legales al inicio del turno.

            } else {
                 // Click en pieza del oponente
                 clearHighlights();
                 updateMessage("No puedes mover la pieza del oponente.", true);
            }

        // --- Caso 3: Click en casilla vacía (o fuera de pieza) sin ser destino válido ---
        } else {
            clearHighlights(); // Deseleccionar si se hace clic en vacío
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
     
     // --- Opcional: Llamada inicial para obtener movimientos legales ---
     // Si quisiéramos resaltar los movimientos posibles al cargar la página/inicio de turno
     // necesitaríamos una nueva URL/vista en Django que devuelva los movimientos legales
     // para el jugador actual en formato JSON.
     // fetchLegalMoves(); 


}); // Fin del DOMContentLoaded