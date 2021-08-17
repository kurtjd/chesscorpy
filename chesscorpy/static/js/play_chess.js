function send_move_to_server(move_uci)
{
    $.post("/move",
        {
            id: GAME_ID,
            move: move_uci
        },
        function(data, status)
        {
            alert("Status: " + status + "\nData: " + data)
        }
    )
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
    if (game.turn() != piece[0] || game.game_over())
        return false
}

function onDrop(source, target)
{
    unHighlightSquares()

    // TODO: Check promotion
    var move = game.move({
        from: source,
        to: target
    })

    if (move == null)
        return "snapback"

    send_move_to_server(source + target)

    check_game()
}

function onMouseoverSquare(square, piece)
{
    var moves = game.moves({
        square: square,
        verbose: true
    })

    if (moves.length == 0)
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


var board_config = {
    position: "start",
    draggable: true,
    onDragStart: onDragStart,
    onDrop: onDrop,
    onMouseoverSquare: onMouseoverSquare,
    onMouseoutSquare: onMouseoutSquare
}

var board_name = "board"
var game = new Chess()
var board = Chessboard(board_name, board_config)

