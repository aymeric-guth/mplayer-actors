#!/bin/sh

build() {
  gcc -o main_sw main.c `pkg-config --libs --cflags sdl2` -I/opt/x86_64-apple-darwin18/include -L/opt/x86_64-apple-darwin18/lib -lmpv -std=c99
  # gcc -o main main.c `pkg-config --libs --cflags sdl2` -I/opt/x86_64-apple-darwin18/include -L/opt/x86_64-apple-darwin18/lib -lmpv -std=c99
}

run() {
  ./main_sw AVGN_S01E001.mp4
}
