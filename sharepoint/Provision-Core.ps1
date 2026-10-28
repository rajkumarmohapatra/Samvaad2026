#Requires -Version 7.4
#Requires -Modules PnP.PowerShell
<# Creates EMPTY, permission-isolated core lists. No participant data is uploaded.
   Run only against a dedicated private pilot site. Review README before execution.
   This script has not been executed against a tenant in the build environment. #>
[CmdletBinding(SupportsShouldProcess, ConfirmImpact='Medium')]
param(
  [Parameter(Mandatory)][uri]$SiteUrl,
  [Parameter(Mandatory)][guid]$ClientId,
  [Parameter(Mandatory)][string]$StreamConfiguration,
  [Parameter(Mandatory)][switch]$PrivateSiteVerified
)
$ErrorActionPreference='Stop'
if ($SiteUrl.Scheme -ne 'https' -or $SiteUrl.Host -notmatch '\.sharepoint\.com$') { throw 'Supply your HTTPS SharePoint Online site URL.' }
if (-not $PrivateSiteVerified) { throw 'Verify dedicated private site permissions first.' }
$streams=@(Get-Content -Raw $StreamConfiguration | ConvertFrom-Json)
if ($streams.Count -eq 0) { throw 'At least one explicitly classified pilot stream is required.' }
foreach($stream in $streams){
  if($stream.code -notmatch '^[A-Z][A-Z0-9]{1,15}$' -or [string]::IsNullOrWhiteSpace($stream.name)){throw 'Each stream needs a stable uppercase code and name.'}
}
if(@($streams.code | Select-Object -Unique).Count -ne $streams.Count){throw 'Stream codes must be unique.'}
if (-not $PSCmdlet.ShouldProcess($SiteUrl.AbsoluteUri,'Connect and provision isolated SAMBAD pilot lists')) { return }
Connect-PnPOnline -Url $SiteUrl.AbsoluteUri -Interactive -ClientId $ClientId
$web=Get-PnPWeb -Includes AssociatedOwnerGroup,RoleAssignments
$owners=$web.AssociatedOwnerGroup
# Fail closed: no site-wide grant except the owners group. Empty default member and
# visitor groups must have their site grants removed during private-site preparation.
foreach($assignment in $web.RoleAssignments){
  $member=Get-PnPProperty -ClientObject $assignment -Property Member
  if($member.Id -ne $owners.Id){throw "Site-wide principal '$($member.Title)' is present. Remove broad site grants before provisioning."}
}
$schema=Get-Content -Raw (Join-Path $PSScriptRoot 'core-lists.json') | ConvertFrom-Json
$groups=@('SB Config Readers','SB Reviewers','SB Registration Readers','SB Automation')
$groups+=@($streams | ForEach-Object { "SB Stream $($_.code)" })
foreach($name in $groups){if(-not(Get-PnPGroup -Identity $name -ErrorAction SilentlyContinue)){New-PnPGroup -Title $name | Out-Null}}
# A custom writer excludes deletion and list/schema administration. SharePoint read
# access still permits API retrieval/export: this does NOT enforce an export ban.
if(-not(Get-PnPRoleDefinition -Identity 'SB Draft Editor' -ErrorAction SilentlyContinue)){
  Add-PnPRoleDefinition -RoleName 'SB Draft Editor' -Clone 'Read' -Include AddListItems,EditListItems,ViewVersions | Out-Null
}
if(-not(Get-PnPRoleDefinition -Identity 'SB Append Only' -ErrorAction SilentlyContinue)){
  Add-PnPRoleDefinition -RoleName 'SB Append Only' -Clone 'Read' -Include AddListItems | Out-Null
}
function New-IsolatedList($definition,$name,$writer,$reader,$writerRole='SB Draft Editor'){
  $list=Get-PnPList -Identity $name -ErrorAction SilentlyContinue
  if($list){
    # Re-runs validate existing lists rather than silently changing access/schema.
    $unique=Get-PnPProperty -ClientObject $list -Property HasUniqueRoleAssignments
    if(-not $unique){throw "Existing list $name inherits permissions; review manually."}
    Write-Warning "Existing list $name skipped. Run tenant acceptance checks for schema and grants."
    return
  }
  $list=New-PnPList -Title $name -Template GenericList -OnQuickLaunch:$false
  $list.BreakRoleInheritance($false,$false); Invoke-PnPQuery
  Set-PnPListPermission -Identity $list -Group $owners.Title -AddRole 'Full Control'
  $automationRole=if($definition.name -eq 'AuditEvents'){'SB Append Only'}else{'SB Draft Editor'}
  Set-PnPListPermission -Identity $list -Group 'SB Automation' -AddRole $automationRole
  if($writer){Set-PnPListPermission -Identity $list -Group $writer -AddRole $writerRole}
  if($reader){Set-PnPListPermission -Identity $list -Group $reader -AddRole 'Read'}
  Set-PnPList -Identity $list -EnableVersioning $true -MajorVersions 100 -EnableAttachments $false
  Set-PnPField -List $list -Identity Title -Values @{Required=$false;Hidden=$true}
  foreach($field in $definition.fields){
    $type=switch($field.type){'guid'{'Text'} 'memo'{'Note'} 'integer'{'Number'} 'money'{'Currency'} 'boolean'{'Boolean'} 'date'{'DateTime'} 'datetime'{'DateTime'} default{'Text'}}
    $fieldParameters=@{List=$list;DisplayName=$field.name;InternalName=$field.name;Type=$type;Required=[bool]$field.required}
    Add-PnPField @fieldParameters | Out-Null
    if($field.index -or $field.unique){
      $values=@{Indexed=$true}
      if($field.unique){$values.EnforceUniqueValues=$true}
      Set-PnPField -List $list -Identity $field.name -Values $values
    }
    if($field.type -eq 'date'){Set-PnPField -List $list -Identity $field.name -Values @{DisplayFormat=0}}
  }
  Add-PnPView -List $list -Title 'Operational view' -Fields @('RecordKey','CreatedAt','UpdatedAt') -RowLimit 100 -Paged -SetAsDefault | Out-Null
  Write-Output "Created isolated list: $name"
}
foreach($definition in $schema){
  if($definition.name -eq 'Nominations'){
    foreach($stream in $streams){New-IsolatedList $definition "SB_Nominations_$($stream.code)" "SB Stream $($stream.code)" 'SB Reviewers'}
  } elseif($definition.name -eq 'ReviewQueue'){
    New-IsolatedList $definition 'SB_ReviewQueue' 'SB Reviewers' $null
  } elseif($definition.name -eq 'ParticipationSnapshots'){
    New-IsolatedList $definition 'SB_ParticipationSnapshots' $null 'SB Registration Readers'
    foreach($stream in $streams){New-IsolatedList $definition "SB_Projection_$($stream.code)" $null "SB Stream $($stream.code)"}
  } elseif($definition.name -eq 'AuditEvents'){
    New-IsolatedList $definition 'SB_AuditEvents' $null $null
  } elseif($definition.name -eq 'WorkflowReceipts'){
    New-IsolatedList $definition 'SB_WorkflowReceipts' $null $null
  } else {
    New-IsolatedList $definition "SB_$($definition.name)" $owners.Title 'SB Config Readers' 'Full Control'
  }
}
Write-Warning 'Provisioning complete for empty core lists only. No canvas app or workflows have been installed. Do not add real records before permission and automation acceptance tests pass.'
