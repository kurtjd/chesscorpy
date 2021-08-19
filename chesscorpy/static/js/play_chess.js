function send_move_to_server(move_san)
{
    $.post("/move",
        {
            id: GAME_ID,
            move: move_san
        },
        function(data, status)
        {
            if (!data.successful)
                alert("Unable to perform move.")
        }
    )
}

function promptPromotion()
{
    promote_to = prompt("Enter piece you want to promote to: ((q)ueen, (r)ook, (b)ishop, k(n)ight): ", 'q')
    if ("qrbn".includes(promote_to))
        return promote_to
    else
        return 'q'
}

function is_legal_move(from, to)
{
    legal_moves = game.moves({ square: from, verbose: true })
    for (var i = 0; i < legal_moves.length; i++)
    {
        if (legal_moves[i].to == to)
            return true
    }

    return false
}

function is_promotion(from, to)
{
    return game.get(from).type == 'p' && (to[1] == '1' || to[1] == '8')
}

function end_game(msg)
{
    alert(msg)
}

function check_game()
{
    if (game.in_checkmate())
        end_game("Game over. Checkmate!")
    else if (game.in_draw())
        end_game("Game over. Draw!")
    else if (game.in_stalemate())
        end_game("Game over. Stalemate!")
    else if (game.in_threefold_repetition())
        end_game("Game over. Draw by three-fold repetition!")
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

function onDragStart(source, piece, position, orientation)
{
    if (game.turn() != piece[0] || game.turn() != USER_COLOR[0] || game.game_over())
        return false
}

function onDrop(source, target)
{
    unHighlightSquares()

    if (is_legal_move(source, target) && is_promotion(source, target))
        promote_to = promptPromotion()
    else
        promote_to = 'q'

    var move = game.move({
        from: source,
        to: target,
        promotion: promote_to
    })

    if (move == null)
        return "snapback"

    send_move_to_server(move.san)
    check_game()
}

function onMouseoverSquare(square, piece)
{
    var moves = game.moves({
        square: square,
        verbose: true
    })

    if (moves.length == 0 || game.turn() != USER_COLOR[0])
        return

    highlightSquare(square)

    for (var i = 0; i < moves.length; i++)
    {
        highlightSquare(moves[i].to)
    }
}

function onMouseoutSquare(square, piece)
{
    unHighlightSquares()
}

function onSnapEnd ()
{
    board.position(game.fen())
}


var board_config = {
    position: "start",
    draggable: true,
    onDragStart: onDragStart,
    onDrop: onDrop,
    onMouseoverSquare: onMouseoverSquare,
    onMouseoutSquare: onMouseoutSquare,
    onSnapEnd: onSnapEnd
}

var board_name = "board"
var game = new Chess()
var board = Chessboard(board_name, board_config)

if (PGN != "None")
    game.load_pgn(PGN)
    board.position(game.fen(), false)

if (USER_COLOR == "white" || USER_COLOR == "none")
    board.orientation("white")
else
    board.orientation("black")

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
