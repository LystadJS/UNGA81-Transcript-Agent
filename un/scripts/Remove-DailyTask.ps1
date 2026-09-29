[CmdletBinding(SupportsShouldProcess=$true)]
param([string]$TaskName='UN Daily Briefing')
if($PSCmdlet.ShouldProcess($TaskName,'Unregister local scheduled task')) { Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false }
