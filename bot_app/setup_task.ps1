$action = New-ScheduledTaskAction -Execute "cmd.exe" -Argument "/c `"d:\Nghiên cứu AI\vnstock-agent-guide\bot_app\run_scheduled.bat`" --scheduled" -WorkingDirectory "d:\Nghiên cứu AI\vnstock-agent-guide\bot_app"
$trigger = New-ScheduledTaskTrigger -Once -At (Get-Date) -RepetitionInterval (New-TimeSpan -Minutes 10) -RepetitionDuration (New-TimeSpan -Days 3650)
Register-ScheduledTask -TaskName "Vnstock_Bot_App" -Action $action -Trigger $trigger -Force
