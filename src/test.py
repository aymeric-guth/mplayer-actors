cmd = {'command': ['loadlist', './playlist.txt'], 'request_id': 3}
# cmd {'command': [], }

match cmd:
    case {'command': [p2, p3], 'request_id': p4}:
        print(f'\n{p2=}\n{p3=}\n{p4=}')
    case {'event': p1}:
    # {'event': 'start-file', 'playlist_entry_id': 1}
        ...
    case {'data': p1, 'request_id': p2, 'error': status}:
        ...
    case _:
        print('default')

# json_data={'event': 'start-file', 'playlist_entry_id': 1}
# json_data={'event': 'tracks-changed'}
# json_data={'event': 'end-file', 'reason': 'error', 'playlist_entry_id': 1, 'file_error': 'loading failed'}
# json_data={'event': 'start-file', 'playlist_entry_id': 2}
# json_data={'event': 'tracks-changed'}
# json_data={'event': 'end-file', 'reason': 'error', 'playlist_entry_id': 2, 'file_error': 'loading failed'}
# json_data={'event': 'start-file', 'playlist_entry_id': 3}
# json_data={'event': 'tracks-changed'}
# json_data={'event': 'end-file', 'reason': 'error', 'playlist_entry_id': 3, 'file_error': 'loading failed'}
# json_data={'event': 'start-file', 'playlist_entry_id': 4}
# json_data={'event': 'tracks-changed'}
# json_data={'event': 'end-file', 'reason': 'error', 'playlist_entry_id': 4, 'file_error': 'loading failed'}
# json_data={'event': 'idle'}
