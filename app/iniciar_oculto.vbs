Option Explicit
Dim shell, fso, root, pythonExe, launcher
Set shell = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")
root = fso.GetParentFolderName(fso.GetParentFolderName(WScript.ScriptFullName))
pythonExe = fso.BuildPath(root, ".runtime\Scripts\python.exe")
launcher = fso.BuildPath(root, "app\launcher.py")
shell.Run Chr(34) & pythonExe & Chr(34) & " " & Chr(34) & launcher & Chr(34), 0, False
