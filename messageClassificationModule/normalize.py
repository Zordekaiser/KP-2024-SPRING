import pymorphy2


def normalize_nouns(text):
    morph = pymorphy2.MorphAnalyzer()
    words = text.split()
    normalized_words = []
    for word in words:
        parsed_word = morph.parse(word)[0]
        if 'NOUN' in parsed_word.tag:
            normalized_word = parsed_word.inflect({'nomn'}).word
            normalized_words.append(normalized_word)
        elif 'ADJF' in parsed_word.tag:
            normalized_word = parsed_word.inflect({'nomn'}).word
            normalized_words.append(normalized_word)
        else:
            normalized_words.append(word)
    return ' '.join(normalized_words)
