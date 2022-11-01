#!/bin/sh

[ -f "$DOTFILES/funcs/py_venv.sh" ] && . "$DOTFILES/funcs/py_venv.sh"

cleanup() {
  _cleanup
}
