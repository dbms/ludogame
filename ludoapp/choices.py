
OPEN = 'open'
ACCEPTED = 'accepted'
OVER = 'over'
INPROGRESS = 'inprogress'
CANCELLED = 'cancelled'

MATCH_STATUSES = (
    (OPEN, 'Open'),
    (ACCEPTED, 'Accepted'),
    (INPROGRESS, 'In Progress'),
    (OVER, 'Over'),
    (CANCELLED, 'Cancelled'),
)

WON = 'won'
LOST = 'lost'

GAME_OUTPUTS = (
    (WON, 'Won'),
    (LOST, "Lost"),
    (CANCELLED, 'Cancelled'),
)

MATCH_LOST = 'match_lost'
MATCH_WON = 'match_won'
MATCH_COMMISSION = 'match_commission'
BUY_COIN = 'buy_coin'
COIN_SOLD = 'coin_sold'

TRANSACTION_MODE = (
    (MATCH_LOST, 'Match Lost'),
    (MATCH_WON, 'Match Won'),
    (MATCH_COMMISSION, 'Match Commission'),
    (BUY_COIN, 'Buy Coin'),
    (COIN_SOLD, 'Coin Sold'),
)


GAME_CODE_LENGTH = 8
MAX_OTP_LIMIT = 5
MAX_OTP_ATTEMPTS = 10

INITIATED = 'initiated'
PROCESSED = 'processed'
DENIED = 'denied'

WITHDRAW_STATUS = (
    (INITIATED, 'Initiated'),
    (PROCESSED, "Processed"),
    (DENIED, 'Denied')
)

MIN_WITHDRAW_AMOUNT = 50

USER_VERIFICATION = 'user_verification'
PASSWORD_RESET = 'password_reset'
