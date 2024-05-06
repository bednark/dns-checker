function update_dns {
  param(
    [parameter(Mandatory=$true)]
    [string]$record_fqdn
  )

  $old_record = Get-DnsServerResourceRecord -ComputerName epsilon.local -ZoneName kl -Name $record_fqdn
  $old_ip = $old_record.RecordData.IPv4Address.IPAddressToString
  $octets = $old_ip.Split('.')
  
  if ($octets[1] -eq 70) {
    $octets[1] = 80
    $new_ip = $octets -join '.'

    $new_record = $old_record.Clone()
    $new_record.RecordData.Ipv4Address = $new_ip

    Set-DnsServerResourceRecord -ComputerName epsilon.local -ZoneName kl -OldInputObject $old_record -NewInputObject $new_record
    Write-Output "Record updated."
  }
  else {
    Write-Output "Nothing to do."
  }
}

$domain = "stale.zlojaworzno"

if ($domain.StartsWith("lte.")) {
  update_dns -record_fqdn $domain
  exit
}

$old_records = Get-DnsServerResourceRecord -ComputerName epsilon.local -ZoneName kl -Name $domain

foreach ($record in $old_records) {
  if ($record.HostName -eq "lte") {
    continue
  }

  $record_fqdn = ($record.HostName + "." + $domain)
  update_dns -record_fqdn $record_fqdn
}