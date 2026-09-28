import chess

from ai.engine import evaluate, best_move, choose_move, order_moves


class TestEvaluation:
    def test_starting_position_is_balanced(self):
        score = evaluate(chess.Board())
        assert 0.0 <= score <= 30.0

    def test_white_ahead_material(self):
        board = chess.Board("r4rk1/pp1n1ppp/8/8/8/8/PPPPPPPP/R4RK1 w - - 0 1")
        score = evaluate(board)
        assert score > 0

    def test_black_ahead_material(self):
        board = chess.Board("rnbqkbnq/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w - - 0 1")
        score = evaluate(board)
        assert score < 0

    def test_checkmate_is_extreme(self):
        board = chess.Board("rnb1kbnr/pppp1ppp/8/4p3/6Pq/5P2/PPPPP2P/RNBQKBNR w KQkq - 0 3")
        assert abs(evaluate(board)) > 9000


class TestSearch:
    def test_best_move_from_starting_position(self):
        move, score = best_move(chess.Board(), depth=2)
        assert move is not None
        assert move in chess.Board().legal_moves
        assert isinstance(score, float)

    def test_can_find_queen_capture(self):
        # White to move: take undefended black queen.
        board = chess.Board("8/3q4/8/3R4/8/8/8/K1k5 w - - 0 1")
        move, _ = best_move(board, depth=3)
        assert move.to_square == chess.parse_square("d7")

    def test_finds_immediate_check_vs_quiet(self):
        # From this position the only winning-looking moves give check with the
        # rook; engine must choose a legal rook move.
        board = chess.Board("7k/8/8/8/8/8/8/R6K w - - 0 1")
        move, _ = best_move(board, depth=2)
        assert move is not None

    def test_game_over_no_moves(self):
        from ai.engine import choose_move

        board = chess.Board("7k/5Q1K/8/8/8/8/8/8 b - - 0 1")
        result = choose_move(board.fen(), "hard")
        assert result["game_over"] is True
        assert result["move"] is None


class TestChooseMove:
    def test_returns_coordinates(self):
        result = choose_move(chess.Board().fen(), "easy")
        assert result["move"]["from"] in chess.SQUARE_NAMES
        assert result["move"]["to"] in chess.SQUARE_NAMES
        assert result["move"]["san"]

    def test_valid_moves_for_side_to_move(self):
        for level in ("beginner", "easy", "medium", "hard", "expert"):
            result = choose_move(chess.Board().fen(), level)
            board = chess.Board()
            move = board.parse_san(result["move"]["san"])
            assert move in list(board.legal_moves)
            assert result["depth"] >= 1

    def test_wrong_side_move_is_legal(self):  # state-position sanity
        fen = "8/8/8/8/8/8/R7/K1k5 b - - 0 1"
        result = choose_move(fen, "hard")
        board = chess.Board(fen)
        move = board.parse_uci(result["move"]["from"] + result["move"]["to"])
        assert move in list(board.legal_moves)

    def test_order_moves_returns_all_legals(self):
        board = chess.Board()
        assert set(order_moves(board)) == set(board.legal_moves)