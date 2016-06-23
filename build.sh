#!/usr/bin/env bash
rm -rf build dist
pyinstaller --windowed main.py
cp -a assets ./dist/main.app/Contents/MacOS/
cp config.ini ./dist/main.app/Contents/MacOS/
cp -a mitmproxy ./dist/main.app/Contents/MacOS/
./dist/main.app/Contents/MacOS/main