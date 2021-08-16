function unHighlightSquares()
{
    $('#board .square-55d63').css('background', '')
}

function highlightSquare(square)
{
    var $square = $('#board .square-' + square)

    var background = '#a9a9a9'
    if ($square.hasClass('black-3c85d'))
    {
        background = '#696969'
    }

    $square.css('background', background)
}

function onDragStart(source, piece, position, orientation)
{
    if (game.turn() != piece[0])
        return false
}

function onDrop(source, target)
{
    unHighlightSquares()

    var move = game.move({
        from: source,
        to: target
    })

    if (move == null)
        return "snapback"
}

function onMouseoverSquare(square, piece)
{
    var moves = game.moves({
        square: square,
        verbose: true
    })

    if (moves.length === 0)
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

var game = new Chess()
var board = Chessboard("board", board_config)

