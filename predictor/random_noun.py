import random

GET_TOKEN_POS = "SELECT pos FROM tokens WHERE token_id=%(token_id)s"

# Initial randomized data for training
def get_random_noun_list(cursor, token_ids, n = 64):
    token_ids = list(token_ids)
    candidates = []
    while len(candidates) < n:
        token_id = random.choice(token_ids)
        cursor.execute(GET_TOKEN_POS, {
            'token_id': token_id
        })
        pos = cursor.fetchall()[0][0]
        if pos == 'NN':
            candidates.append(token_id)
    return sorted(candidates)
