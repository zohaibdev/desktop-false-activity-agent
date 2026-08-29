' ============================================
' AI Desktop Automation Agent - Hidden Runner
' ============================================
' This VBScript runs the agent without showing a console window
' Double-click this file to start the agent in background
'
' Controls (still work even with hidden console):
'   F8  = Stop agent gracefully
'   F9  = Emergency stop
'   F10 = Pause / Resume

Set WshShell = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")

' Get the directory where this script is located
scriptDir = fso.GetParentFolderName(WScript.ScriptFullName)

' Change to script directory
WshShell.CurrentDirectory = scriptDir

' Run Python with pythonw (no console) or use hidden window
' 0 = Hide window, False = Don't wait for completion
WshShell.Run "pythonw main.py", 0, False

' Alternative if pythonw doesn't work:
' WshShell.Run "cmd /c python main.py", 0, False
