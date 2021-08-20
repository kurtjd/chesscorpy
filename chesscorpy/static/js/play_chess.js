function postMove(move_san)
{
    $.post("/move",
        {
            id: GAME_ID,
            move: move_san
        },
        function(data, status)
        {
            // If move was unsuccessful on the server, undo the move on the local game.
            if (!data.successful)
            {
                alert("Unable to perform move.")
                game.undo()
                board.position(game.fen())
            }
        }
    )
}

function promptPromotion()
{
    var promote_to = prompt("Enter piece you want to promote to: ((q)ueen, (r)ook, (b)ishop, k(n)ight): ", 'q')

    if ("qrbn".includes(promote_to))
    {
        return promote_to
    }
    else
    {
        return 'q'
    }
}

function moveIsLegal(from, to)
{
    var legal_moves = game.moves({ square: from, verbose: true })

    for (let i = 0; i < legal_moves.length; i++)
    {
        if (legal_moves[i].to == to)
        {
            return true
        }
    }

    return false
}

function moveIsPromotion(from, to)
{
    // Check if piece is pawn and if it is about to move to the 1st or 8th rank.
    return game.get(from).type == 'p' && (to[1] == '1' || to[1] == '8')
}

function getCapturedPieces(color)
{
    var history = game.history({ verbose: true })
    var captured = {
        'p': 0,
        'n': 0,
        'b': 0,
        'r': 0,
        'q': 0
    }

    for (let i = 0; i < history.length; i++)
    {
        let move = history[i]

        if (move.hasOwnProperty("captured") && move.color != color[0])
        {
            captured[move.captured]++
        }
    }

    alert(color + ": " + JSON.stringify(captured))
    return captured
}

function endGame(msg)
{
    alert(msg)
}

function checkGame()
{
    if (game.in_checkmate())
    {
        endGame("Game over. Checkmate!")
    }
    else if (game.in_draw())
    {
        endGame("Game over. Draw!")
    }
    else if (game.in_stalemate())
    {
        endGame("Game over. Stalemate!")
    }
    else if (game.in_threefold_repetition())
    {
        endGame("Game over. Draw by three-fold repetition!")
    }
}

function unHighlightSquares()
{
    $('#' + board_name + " .square-55d63").css("background", '')
}

function highlightSquare(square)
{
    var $square = $('#' + board_name + " .square-" + square)
    var background = "#a9a9a9"

    if ($square.hasClass("black-3c85d"))
    {
        background = "#696969"
    }

    $square.css("background", background)
}

function onPieceDrag(source, piece, position, orientation)
{
    // Checks that it's the selected piece's color's turn to move, that it is the player's turn,
    // and that the game is not over.
    if (game.turn() != piece[0] || game.turn() != USER_COLOR[0] || game.game_over())
    {
        return false
    }
}

function onPieceMove(source, target)
{
    unHighlightSquares()

    if (moveIsLegal(source, target) && moveIsPromotion(source, target))
    {
        var promote_to = promptPromotion()
    }
    else
    {
        var promote_to = 'q'
    }

    var move = game.move({
        from: source,
        to: target,
        promotion: promote_to
    })

    if (move == null)
    {
        return "snapback"
    }

    postMove(move.san)
    checkGame()
}

function onMouseoverSquare(square, piece)
{
    var moves = game.moves({
        square: square,
        verbose: true
    })

    if (moves.length == 0 || game.turn() != USER_COLOR[0])
    {
        return
    }

    highlightSquare(square)

    for (let i = 0; i < moves.length; i++)
    {
        highlightSquare(moves[i].to)
    }
}

function onMouseoutSquare(square, piece)
{
    unHighlightSquares()
}

function onSnapEnd()
{
    board.position(game.fen())
}


var board_config = {
    position: "start",
    draggable: true,
    onDragStart: onPieceDrag,
    onDrop: onPieceMove,
    onMouseoverSquare: onMouseoverSquare,
    onMouseoutSquare: onMouseoutSquare,
    onSnapEnd: onSnapEnd
}

var board_name = "board"
var game = new Chess()
var board = Chessboard(board_name, board_config)

if (PGN != "None")
{
    game.load_pgn(PGN)
    board.position(game.fen(), false)
}

var captured_white = getCapturedPieces("white")
var captured_black = getCapturedPieces("black")

if (USER_COLOR == "white" || USER_COLOR == "none")
{
    board.orientation("white")
}
else
{
    board.orientation("black")
}

if (board.orientation() == "white")
{
    $("#player1").html("<b>" + PLAYER_BLACK + "</b>")
    $("#player2").html("<b>" + PLAYER_WHITE + "</b>")
}
else
{
    $("#player1").html("<b>" + PLAYER_WHITE + "</b>")
    $("#player2").html("<b>" + PLAYER_BLACK + "</b>")
}