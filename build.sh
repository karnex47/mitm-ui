#!/usr/bin/env bash
echo "cleaning up directory"
rm -rf build dist
echo "building app"
pyinstaller --windowed MitmUI.py
echo "copying required files"
cp -a assets ./dist/MitmUI.app/Contents/MacOS/
cp config.ini ./dist/MitmUI.app/Contents/MacOS/
cp -a mitmproxy ./dist/MitmUI.app/Contents/MacOS/
echo "creating dmg"
hdiutil create dist/MitmUI.dmg -srcfolder dist/MitmUI.app/
# ./dist/MitmUi.app/Contents/MacOS/MitmUI