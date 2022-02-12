import pickle

from pathlib import Path



path = Path(__file__).parent

try:
    with open(path / 'constants_character_encoding.pckl', "rb") as file:
        (
            accents_non_standard,
            pattern_dubious_modifiers,
            accents_standard_map,
            global_ideographic,
            modifier,
            full_width,
            half_width,
            emoji_data,
        ) = pickle.load(file)
except OSError:
    from .character_encoding_ import (accents_non_standard, pattern_dubious_modifiers, accents_standard_map, global_ideographic, modifier, full_width, half_width, emoji)
    args = (
        accents_non_standard,
        pattern_dubious_modifiers,
        accents_standard_map,
        global_ideographic,
        modifier,
        full_width,
        half_width,
        emoji,
    )
    with open(path / 'constants_character_encoding.pckl', "wb") as file:
        pickle.dump(args, file)

    with open(path / 'constants_character_encoding.pckl', "rb") as file:
        (
            accents_non_standard,
            pattern_dubious_modifiers,
            accents_standard_map,
            global_ideographic,
            modifier,
            full_width,
            half_width,
            emoji_data,
        )= pickle.load(file)
