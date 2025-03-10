from board import Board
from src.chess_sim_revamp.GUI import Display

def main():
    board = Board()
    state = "R---K--R/PPP--PPP/--NQ--qN/---PPB--/---p----/--p-pppp/pp------/rnbqkbnr/"
    board.load_from_url(state)
    display = Display()
    gameRunning = True
    while gameRunning:
        display.disp_board(board)
        gameRunning = display.handle_events(board)
        nextMove = display.get_next_move_from_click(board)
        board.move(nextMove[0], nextMove[1], legal_required=True)

if __name__ == "__main__":
    main()

