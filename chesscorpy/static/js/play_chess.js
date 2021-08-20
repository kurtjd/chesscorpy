function postMove(move_san) {
    $.post("/move",
        {
            id: GAME_ID,
            move: move_san
        },
        function(data, status) {
            // If move was unsuccessful on the server, undo the move on the local game.
            if (!data.successful) {
                alert("Unable to perform move.")
                game.undo()
                board.position(game.fen())
            }
        }
    )
}

function promptPromotion() {
    const promote_to = prompt("Enter piece you want to promote to: ((q)ueen, (r)ook, (b)ishop, k(n)ight): ", 'q')

    if ("qrbn".includes(promote_to)) {
        return promote_to
    } else {
        return 'q'
    }
}

function moveIsLegal(from, to) {
    for (const move of game.moves({ square: from, verbose: true })) {
        if (move.to === to) {
            return true
        }
    }

    return false
}

function moveIsPromotion(from, to) {
    // Check if piece is pawn and if it is about to move to the 1st or 8th rank.
    return game.get(from).type === 'p' && (to[1] === '1' || to[1] === '8')
}

function setCapturedDisplay() {
    $("#captured").html("Captured White: " + JSON.stringify(captured_white) +
                        "<br>Captured Black: " + JSON.stringify(captured_black))
}

function getCapturedPieces(color) {
    const captured = {'p': 0, 'n': 0, 'b': 0, 'r': 0, 'q': 0}

    for (const move of game.history({ verbose: true })) {
        if (move.hasOwnProperty("captured") && move.color !== color[0]) {
            captured[move.captured]++
        }
    }

    return captured
}

function endGame(msg) {
    alert(msg)
}

function checkGame() {
    if (game.in_checkmate()) {
        endGame("Game over. Checkmate!")
    } else if (game.in_draw()) {
        endGame("Game over. Draw!")
    } else if (game.in_stalemate()) {
        endGame("Game over. Stalemate!")
    } else if (game.in_threefold_repetition()) {
        endGame("Game over. Draw by three-fold repetition!")
    }
}

function unHighlightSquares() {
    $('#' + BOARD_NAME + " .square-55d63").css("background", '')
}

function highlightSquare(square) {
    const $square = $('#' + BOARD_NAME + " .square-" + square)
    let background = "#a9a9a9"

    if ($square.hasClass("black-3c85d")) {
        background = "#696969"
    }

    $square.css("background", background)
}

function onPieceDrag(source, piece, position, orientation) {
    // Checks that it's the selected piece's color's turn to move, that it is the player's turn,
    // and that the game is not over.
    if (game.turn() != piece[0] || game.turn() != USER_COLOR[0] || game.game_over()) {
        return false
    }
}

function onPieceMove(source, target) {
    unHighlightSquares()

    if (moveIsLegal(source, target) && moveIsPromotion(source, target)) {
        var promote_to = promptPromotion()
    } else {
        var promote_to = 'q'
    }

    const move = game.move({
        from: source,
        to: target,
        promotion: promote_to
    })

    if (move === null) {
        return "snapback"
    }

    // For now naively re-check for captured pieces even if move didn't result in capture.
    captured_white = getCapturedPieces("white")
    captured_black = getCapturedPieces("black")
    setCapturedDisplay()

    postMove(move.san)
    checkGame()
}

function onMouseoverSquare(square, piece) {
    const moves = game.moves({
        square: square,
        verbose: true
    })

    if (moves.length === 0 || game.turn() != USER_COLOR[0]) {
        return
    }

    highlightSquare(square)

    for (const move of moves) {
        highlightSquare(move.to)
    }
}

function onMouseoutSquare(square, piece) {
    unHighlightSquares()
}

function onSnapEnd() {
    board.position(game.fen())
}


const board_config = {
    position: "start",
    draggable: true,
    onDragStart: onPieceDrag,
    onDrop: onPieceMove,
    onMouseoverSquare: onMouseoverSquare,
    onMouseoutSquare: onMouseoutSquare,
    onSnapEnd: onSnapEnd
}

const BOARD_NAME = "board"
const game = new Chess()
const board = Chessboard(BOARD_NAME, board_config)

if (PGN != "None") {
    game.load_pgn(PGN)
    board.position(game.fen(), false)
}

let captured_white = getCapturedPieces("white")
let captured_black = getCapturedPieces("black")
setCapturedDisplay()

if (USER_COLOR === "white" || USER_COLOR === "none") {
    board.orientation("white")
} else {
    board.orientation("black")
}

if (board.orientation() === "white") {
    $("#player1").html("<b>" + PLAYER_BLACK + "</b>")
    $("#player2").html("<b>" + PLAYER_WHITE + "</b>")
} else {
    $("#player1").html("<b>" + PLAYER_WHITE + "</b>")
    $("#player2").html("<b>" + PLAYER_BLACK + "</b>")
}