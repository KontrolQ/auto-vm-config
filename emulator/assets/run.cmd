@ECHO OFF
IF /I "%~1"=="install" GOTO INSTALL

{{run_command}}
GOTO :EOF

:INSTALL
{{install_command}}
