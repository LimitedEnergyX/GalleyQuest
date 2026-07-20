Get-NetFirewallRule -DisplayName '*Node*' | ForEach-Object {
  $rule = $_
  $addr = $rule | Get-NetFirewallAddressFilter
  $port = $rule | Get-NetFirewallPortFilter
  [PSCustomObject]@{
    Name = $rule.DisplayName
    Enabled = $rule.Enabled
    Direction = $rule.Direction
    Action = $rule.Action
    Profile = $rule.Profile
    RemoteAddress = $addr.RemoteAddress
    LocalPort = $port.LocalPort
    Protocol = $port.Protocol
  }
} | Format-List
