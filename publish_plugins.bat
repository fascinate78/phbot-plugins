@echo off
setlocal
title FasscinaTe phBot Plugin Publisher
pushd "%~dp0"

powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0publish_plugins.ps1"
if errorlevel 1 goto :publish_failed

git rev-parse --is-inside-work-tree >nul 2>&1
if errorlevel 1 goto :git_missing

git add --all
if errorlevel 1 goto :git_failed

git diff --cached --quiet
if not errorlevel 1 goto :nothing_to_publish

git commit -m "Publish plugin updates"
if errorlevel 1 goto :git_failed

git push origin main
if errorlevel 1 goto :push_failed

echo.
echo Plugins were published to GitHub successfully.
goto :finish_success

:nothing_to_publish
echo.
echo No plugin changes were found. GitHub is already current.
goto :finish_success

:publish_failed
echo.
echo Plugin preparation failed. Nothing was pushed to GitHub.
goto :finish_error

:git_missing
echo.
echo This folder is not connected to a Git repository.
goto :finish_error

:git_failed
echo.
echo Git could not create the commit. Review the messages above.
goto :finish_error

:push_failed
echo.
echo The commit was created locally, but GitHub push failed.
echo Check your internet connection and GitHub login, then run this BAT again.
goto :finish_error

:finish_success
echo.
pause
popd
exit /b 0

:finish_error
echo.
pause
popd
exit /b 1
