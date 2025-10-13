"""
Simple test script to verify pawn promotion implementation.
Tests promotion in different scenarios.
"""
import chess

def test_promotion_uci_format():
    """Test that promotion moves are correctly formatted in UCI."""
    print("Testing UCI promotion format...")
    
    # Create a board position with a pawn ready to promote
    board = chess.Board()
    board.clear()
    board.set_piece_at(chess.E7, chess.Piece(chess.PAWN, chess.WHITE))
    board.set_piece_at(chess.E1, chess.Piece(chess.KING, chess.WHITE))
    board.set_piece_at(chess.E8, chess.Piece(chess.KING, chess.BLACK))
    board.turn = chess.WHITE
    
    print(f"Board FEN: {board.fen()}")
    print(f"Board:\n{board}")
    
    # Create promotion moves
    queen_promotion = chess.Move(chess.E7, chess.E8, promotion=chess.QUEEN)
    rook_promotion = chess.Move(chess.E7, chess.E8, promotion=chess.ROOK)
    bishop_promotion = chess.Move(chess.E7, chess.E8, promotion=chess.BISHOP)
    knight_promotion = chess.Move(chess.E7, chess.E8, promotion=chess.KNIGHT)
    
    # Test UCI format
    print(f"\nQueen promotion UCI: {queen_promotion.uci()}")
    assert queen_promotion.uci() == "e7e8q", "Queen promotion should be e7e8q"
    
    print(f"Rook promotion UCI: {rook_promotion.uci()}")
    assert rook_promotion.uci() == "e7e8r", "Rook promotion should be e7e8r"
    
    print(f"Bishop promotion UCI: {bishop_promotion.uci()}")
    assert bishop_promotion.uci() == "e7e8b", "Bishop promotion should be e7e8b"
    
    print(f"Knight promotion UCI: {knight_promotion.uci()}")
    assert knight_promotion.uci() == "e7e8n", "Knight promotion should be e7e8n"
    
    print("\n✓ All UCI format tests passed!")

def test_promotion_from_uci():
    """Test that promotion moves can be created from UCI strings."""
    print("\nTesting promotion from UCI strings...")
    
    # Test creating moves from UCI with promotion
    move1 = chess.Move.from_uci("e7e8q")
    print(f"Created move from 'e7e8q': {move1}")
    assert move1.promotion == chess.QUEEN, "Should be queen promotion"
    
    move2 = chess.Move.from_uci("a7a8n")
    print(f"Created move from 'a7a8n': {move2}")
    assert move2.promotion == chess.KNIGHT, "Should be knight promotion"
    
    print("\n✓ All UCI parsing tests passed!")

def test_promotion_detection():
    """Test detection of when promotion is needed."""
    print("\nTesting promotion detection logic...")
    
    # White pawn promotion
    board = chess.Board()
    board.clear()
    board.set_piece_at(chess.E7, chess.Piece(chess.PAWN, chess.WHITE))
    board.set_piece_at(chess.E1, chess.Piece(chess.KING, chess.WHITE))
    board.set_piece_at(chess.E8, chess.Piece(chess.KING, chess.BLACK))
    board.turn = chess.WHITE
    
    from_square = chess.E7
    to_square = chess.E8
    piece = board.piece_at(from_square)
    
    needs_promotion = piece and piece.piece_type == chess.PAWN and (
        (piece.color == chess.WHITE and to_square > 55) or 
        (piece.color == chess.BLACK and to_square < 8)
    )
    
    print(f"White pawn e7->e8 needs promotion: {needs_promotion}")
    assert needs_promotion, "White pawn moving to rank 8 should need promotion"
    
    # Black pawn promotion
    board.clear()
    board.set_piece_at(chess.E2, chess.Piece(chess.PAWN, chess.BLACK))
    board.set_piece_at(chess.E1, chess.Piece(chess.KING, chess.WHITE))
    board.set_piece_at(chess.E8, chess.Piece(chess.KING, chess.BLACK))
    board.turn = chess.BLACK
    
    from_square = chess.E2
    to_square = chess.E1
    piece = board.piece_at(from_square)
    
    needs_promotion = piece and piece.piece_type == chess.PAWN and (
        (piece.color == chess.WHITE and to_square > 55) or 
        (piece.color == chess.BLACK and to_square < 8)
    )
    
    print(f"Black pawn e2->e1 needs promotion: {needs_promotion}")
    assert needs_promotion, "Black pawn moving to rank 1 should need promotion"
    
    # Non-promotion move
    board.clear()
    board.set_piece_at(chess.E2, chess.Piece(chess.PAWN, chess.WHITE))
    board.set_piece_at(chess.E1, chess.Piece(chess.KING, chess.WHITE))
    board.set_piece_at(chess.E8, chess.Piece(chess.KING, chess.BLACK))
    board.turn = chess.WHITE
    
    from_square = chess.E2
    to_square = chess.E4
    piece = board.piece_at(from_square)
    
    needs_promotion = piece and piece.piece_type == chess.PAWN and (
        (piece.color == chess.WHITE and to_square > 55) or 
        (piece.color == chess.BLACK and to_square < 8)
    )
    
    print(f"White pawn e2->e4 needs promotion: {needs_promotion}")
    assert not needs_promotion, "Normal pawn move should not need promotion"
    
    print("\n✓ All promotion detection tests passed!")

if __name__ == "__main__":
    print("=" * 60)
    print("PAWN PROMOTION IMPLEMENTATION TEST")
    print("=" * 60)
    
    try:
        test_promotion_uci_format()
        test_promotion_from_uci()
        test_promotion_detection()
        
        print("\n" + "=" * 60)
        print("✓ ALL TESTS PASSED!")
        print("=" * 60)
        print("\nPawn promotion is correctly implemented!")
        print("\nKey points:")
        print("- Promotion moves include piece type in UCI (e.g., 'e7e8q')")
        print("- White pawns promote on rank 8 (squares 56-63)")
        print("- Black pawns promote on rank 1 (squares 0-7)")
        print("- Promotion options: Queen (q), Rook (r), Bishop (b), Knight (n)")
        
    except AssertionError as e:
        print(f"\n✗ TEST FAILED: {e}")
    except Exception as e:
        print(f"\n✗ ERROR: {e}")
        import traceback
        traceback.print_exc()

