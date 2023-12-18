@echo off
cd ..
del /s /q /f *.pyc
SET TARGET=WxGPGPX
pyinstaller.exe --clean --noconfirm ^
-p .\modules\ ^
-p .\plugins\ ^
--additional-hooks-dir=hooks ^
--exclude-module FixTk ^
--exclude-module tcl ^
--exclude-module _tkinter ^
--exclude-module tkinter ^
--exclude-module Tkinter ^
--exclude-module tk ^
--exclude-module win32com ^
--exclude-module pywin32 ^
--exclude-module pubsub ^
--exclude-module PyQt5 ^
%TARGET%.py 
xcopy /e /Y /i docs dist\%TARGET%\docs
xcopy /e /Y /i scripts dist\%TARGET%\scripts
xcopy /e /Y /i plugins dist\%TARGET%\plugins
xcopy /Y wxgpx_settings.json dist\%TARGET%\
xcopy /Y README.md dist\%TARGET%\
xcopy /Y License.txt dist\%TARGET%\
xcopy /Y Changelog.md dist\%TARGET%\
REM make symlinks to files and folders
REM mklink name target (name relative to cwd, target relative to link)
mklink dist\WxGPGPX.exe %TARGET%\WxGPGPX.exe
mklink dist\wxgpx_settings.json %TARGET%\wxgpx_settings.json
mklink dist\README.md %TARGET%\README.md
mklink dist\License.txt %TARGET%\License.txt
mklink /D dist\scripts %TARGET%\scripts
mklink /D dist\docs %TARGET%\docs
mklink /D dist\plugins %TARGET%\plugins
rmdir /s /q build
pause