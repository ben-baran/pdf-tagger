import random
import re

GET_TOKEN_INFO = "SELECT token_id, word, pos FROM tokens WHERE ssid=%(ssid)s ORDER BY token_n"

# Initial randomized data for training
# see http://bdewilde.github.io/blog/2014/09/23/intro-to-automatic-keyphrase-extraction/
# for some more ideas?

def get_random_noun_list(cursor, ssid, n = 16, max_failures = 16):
    cursor.execute(GET_TOKEN_INFO, {
        'ssid': ssid
    })
    info = cursor.fetchall()
    word_to_ids = {}
    
    def pos_to_char(pos):
        if pos == 'NN':
            return 'n'
        if pos == 'JJ':
            return 'j'
        return '_'
    
    pos_stream = ''.join([pos_to_char(pos) for _, _, pos in info])
    nn_locs = [m.span() for m in re.finditer('j*n+', pos_stream)]
    
    phrases_to_ids = {}
    for span in nn_locs:
        size = span[1] - span[0]
        info_for_span = info[span[0]:span[1]]
        words_spanned = [word for _, word, _ in info_for_span]
        phrase = ' '.join(words_spanned)
        if phrase not in phrases_to_ids:
            # We can't just use the matches found by regex since this will skip
            # noun phrases found within noun phrases
            phrases_to_ids[phrase] = []
            for info_i in range(len(info)):
                if info_i + size - 1 >= len(info):
                    break
                match = True
                possible_words_spanned = [word for _, word, _ in info[info_i:info_i + size]]
                for word_a, word_b in zip(words_spanned, possible_words_spanned):
                    if word_a != word_b:
                        match = False
                        break
                if match:
                    phrases_to_ids[phrase].append([token_id for token_id, _, _ in info[info_i:info_i + size]])
        
    # We filter out any phrases that only occur once
    phrases_to_ids = {phrase:ids for phrase,ids in phrases_to_ids.items() if len(ids) > 1}
        
    phrases = list(phrases_to_ids.keys())
    candidate_locations = {}
    failures = 0
    
    while len(candidate_locations) < n:
        phrase = random.choice(phrases)
        if phrase in candidate_locations:
            failures += 1
            if failures == max_failures:
                break
            continue
        failures = 0
        
        candidate_locations[phrase] = phrases_to_ids[phrase]
        
    return list(candidate_locations.values())
