import re

from .emoji_data import emoji

#trouvé sur un album des bérus et des groupes fr ça doit venir de windobe
# encore beaucoup de permutations possibles genre 3-4 blockssur le site d'unicode
# https://www.utf8-chartable.de/unicode-utf8-table.pl
accents_utf8_standard_str = [
    'À', 'Á', 'Â', 'Ä', 'Ã', 'Å',
    'à', 'á', 'â', 'ä', 'ã', 'å',
    'Ć', 'Ĉ', 'Ç',
    'ć', 'ĉ', 'ç',
    'È', 'É', 'Ê', 'Ë',
    'è', 'é', 'ê', 'ë',
    'Ì', 'Í', 'Î', 'Ï',
    'ì', 'í', 'î', 'ï',
    'Ǹ','Ń', 'Ñ', 'Ņ', 'Ň',
    'ǹ','ń', 'ñ', 'ņ', 'ň',
    'Ò', 'Ó', 'Ô', 'Ö', 'Õ',
    'ò', 'ó', 'ô', 'ö', 'õ',
    'Ù', 'Ú', 'Û', 'Ü',
    'ù', 'ú', 'û', 'ü',
    'Ý', 'Ŷ', 'Ÿ',
    'ý', 'ŷ', 'ÿ',
]
accents_utf8_standard_bytes = [
    b'\xc3\x80', b'\xc3\x81', b'\xc3\x82', b'\xc3\x84', b'\xc3\x83', b'\xc3\x85',
    b'\xc3\xa0', b'\xc3\xa1', b'\xc3\xa2', b'\xc3\xa4', b'\xc3\xa3', b'\xc3\xa5',
    b'\xc4\x86', b'\xc4\x88', b'\xc3\x87',
    b'\xc4\x87', b'\xc4\x89', b'\xc3\xa7',
    b'\xc3\x88', b'\xc3\x89', b'\xc3\x8a', b'\xc3\x8b',
    b'\xc3\xa8', b'\xc3\xa9', b'\xc3\xaa', b'\xc3\xab',
    b'\xc3\x8c', b'\xc3\x8d', b'\xc3\x8e', b'\xc3\x8f',
    b'\xc3\xac', b'\xc3\xad', b'\xc3\xae', b'\xc3\xaf',
    b'\xc7\xb8', b'\xc5\x83', b'\xc3\x91', b'\xc5\x85', b'\xc5\x87',
    b'\xc7\xb9', b'\xc5\x84', b'\xc3\xb1', b'\xc5\x86', b'\xc5\x88',
    b'\xc3\x92', b'\xc3\x93', b'\xc3\x94', b'\xc3\x96', b'\xc3\x95',
    b'\xc3\xb2', b'\xc3\xb3', b'\xc3\xb4', b'\xc3\xb6', b'\xc3\xb5',
    b'\xc3\x99', b'\xc3\x9a', b'\xc3\x9b', b'\xc3\x9c',
    b'\xc3\xb9', b'\xc3\xba', b'\xc3\xbb', b'\xc3\xbc',
    b'\xc3\x9d', b'\xc5\xb6', b'\xc5\xb8',
    b'\xc3\xbd', b'\xc5\xb7', b'\xc3\xbf',
]
accents_utf8_non_standard_str = [
    'À', 'Á', 'Â', 'Ä', 'Ã', 'Å',
    'à', 'á', 'â', 'ä', 'ã', 'å',
    'Ć', 'Ĉ', 'Ç',
    'ć', 'ĉ', 'ç',
    'È', 'É', 'Ê', 'Ë',
    'è', 'é', 'ê', 'ë',
    'Ì', 'Í', 'Î', 'Ï',
    'ì', 'í', 'î', 'ï',
    'Ǹ', 'Ń','Ñ', 'Ņ', 'Ň',
    'ǹ', 'ń', 'ñ', 'ņ', 'ň',
    'Ò', 'Ó', 'Ô', 'Ö', 'Õ',
    'ò', 'ó', 'ô', 'ö', 'õ',
    'Ù', 'Ú', 'Û', 'Ü',
    'ù', 'ú', 'û', 'ü',
    'Ý', 'Ŷ', 'Ÿ',
    'ý', 'ŷ', 'ÿ',
]
# bizarrerie avec le a minuscule accent grave(à) provient de iterm qui change la typo?
accents_utf8_non_standard_bytes = [
    b'A\xcc\x80', b'A\xcc\x81', b'A\xcc\x82', b'A\xcc\x88', b'A\xcc\x83', b'A\xcc\x8a',
    b'a\xcc\x80', b'a\xcc\x81', b'a\xcc\x82', b'a\xcc\x88', b'a\xcc\x83', b'a\xcc\x8a',
    b'C\xcc\x81', b'C\xcc\x82', b'C\xcc\xa7',
    b'c\xcc\x81', b'c\xcc\x82', b'c\xcc\xa7',
    b'E\xcc\x80', b'E\xcc\x81', b'E\xcc\x82', b'E\xcc\x88',
    b'e\xcc\x80', b'e\xcc\x81', b'e\xcc\x82', b'e\xcc\x88',
    b'I\xcc\x80', b'I\xcc\x81', b'I\xcc\x82', b'I\xcc\x88',
    b'i\xcc\x80', b'i\xcc\x81', b'i\xcc\x82', b'i\xcc\x88',
    b'N\xcc\x80', b'N\xcc\x81', b'N\xcc\x83', b"N\xcc\xa7", b"N\xcc\x8c",
    b'n\xcc\x80', b'n\xcc\x81', b'n\xcc\x83', b"n\xcc\xa7", b"n\xcc\x8c",
    b'O\xcc\x80', b'O\xcc\x81', b'O\xcc\x82', b'O\xcc\x88', b'O\xcc\x83',
    b'o\xcc\x80', b'o\xcc\x81', b'o\xcc\x82', b'o\xcc\x88', b'o\xcc\x83',
    b'U\xcc\x80', b'U\xcc\x81', b'U\xcc\x82', b'U\xcc\x88',
    b'u\xcc\x80', b'u\xcc\x81', b'u\xcc\x82', b'u\xcc\x88',
    b'Y\xcc\x81', b'Y\xcc\x82', b'Y\xcc\x88',
    b'y\xcc\x81', b'y\xcc\x82', b'y\xcc\x88',
]

accents_standard_map = dict( zip(
    accents_utf8_non_standard_bytes,
    accents_utf8_standard_bytes ) )

non_standard_special = [
'　', '“', '”',#trouvé dans 1991 - Artisan
'‎', ' ',#trouvé dans des albums wave
]
non_standard_special_fixed = [
' ', '"', '"',
' ', ' '
]

# Japanese Modifiers
# range(12330, 12334), range(12441, 12443)
# Korean Hangul Modifiers
# range(0x1160, 0x11A7), range(0x1161, 0x1176), range(0x11A8, 0x11C3)
modifier_ = *range(12330, 12334), *range(12441, 12443),\
    *range(0x1160, 0x11A7), *range(0x1161, 0x1176), *range(0x11A8, 0x11C3)

# Japanese Half-Width Katakana
# range(65377, 65501), range(65511, 65519), range(12351,12352)
half_width_ = *range(65377, 65501), *range(65511, 65519), *range(12351,12352)

# Japanese Ponctuation
# range(12288, 12330), range(12334, 12350)
# Japanese Hiragana
# range(12352, 12441)
# Japanese Katakana
# range(12443, 12447), range(12448, 12543)
# Japanese Kanji
# range(13312, 19904), range(19968, 40880)
# Japanese Romanji
# range(65280, 65377), range(65504, 65511)
# Korean Hangul
# range(0x1100, 0x1113)
# Emojis
# 127769, 127873, 127800,
full_width_ = *range(12288, 12330), *range(12334, 12350),\
    *range(12352, 12441),\
    *range(12443, 12447), *range(12448, 12543),\
    *range(13312, 19904), *range(19968, 40880),\
    *range(65280, 65377), *range(65504, 65511),\
    *range(0x1100, 0x1113),\
    127769, 127873, 127800,

modifier = { chr(i) for i in modifier_ }
half_width = { chr(i) for i in half_width_ }
full_width = { chr(i) for i in full_width_ }
global_ideographic = modifier | half_width | full_width | emoji

accents_non_standard = {'̃', '̊', '̀', '̧', '̂', '̈', '́', '̌', '̧'}
p = b"|".join([i.encode("utf8") for i in accents_non_standard ])
pattern_dubious_modifiers = re.compile(b"[ACEINOUYaceuinoy]{1}" + b"(?=" + p + b")")


################################################################################
# TESTS TESTS TESTS TESTS TESTS TESTS TESTS TESTS TESTS TESTS TESTS TESTS TESTS#
################################################################################

# for i, v in enumerate(accents_utf8_standard_bytes):
#     print(f"ACTUAL  : {accents_utf8_standard_str[i]} | {accents_utf8_standard_str[i]}")
#     print(f"EXPECTED: {v.decode('utf8')} | {accents_utf8_non_standard_bytes[i].decode('utf8')}")
#     print()

# Lazy Generate {accents_non_standard}
# s = "{"
# for i in accents_non_standard:
#     s += f"'{i}', "
# x = b'\xcc\x8c'.decode('utf8')
# s += f"'{x}', "
# x = b'\xcc\xa7'.decode('utf8')
# s += f"'{x}'"
# s += "}"
# print(s)

# grave b'\xcc\x80'
# aigu b'\xcc\x81'
# chapoflex b'\xcc\x82'
# trema b'\xcc\x88'
# ninio b'\xcc\x83'
# cedille b'\xcc\xa7'
# caron b'\xcc\x8c'
# angstrom b'\xcc\x8a'

################################################################################
# TESTS TESTS TESTS TESTS TESTS TESTS TESTS TESTS TESTS TESTS TESTS TESTS TESTS#
################################################################################

# Guard sommaire pour s'assurer que les listes ont au moins les memes longueurs
a = len(accents_utf8_standard_str)
b = len(accents_utf8_standard_bytes)
c = len(accents_utf8_standard_str)
d = len(accents_utf8_non_standard_bytes)
if a != b or b != c or c != d or d != a: raise Exception('Lists Incomplete')
