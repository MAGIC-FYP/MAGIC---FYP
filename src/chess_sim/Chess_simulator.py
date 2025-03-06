from board import Board

def main():
    board = Board()
    board.print_ascii()
    board.move((1, 0), (2, 0), legal_required=True)
    board.print_ascii()

if __name__ == "__main__":
    main()