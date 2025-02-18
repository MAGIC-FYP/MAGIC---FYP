from board import Board

def main():
    board = Board()
    board.print_ascii()
    board.move((0, 0), (1, 1), legal_required=False)
    board.print_ascii()
if __name__ == "__main__":
    main()