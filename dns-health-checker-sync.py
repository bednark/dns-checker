from pypsrp.client import Client
from glob import glob
import os

def run_script(old_octet, new_octet):
  client = Client("epsilon.local", username=os.environ.get("DNSCHECKER_USER"), password=os.environ.get("DNSCHECKER_PASSWORD"), ssl=False)
  log_files = glob("/etc/openvpn/logs/*-status.log")

  for log in log_files:
    with open(log, "r") as l:
      domain_name = log.split('/')[-1].replace('-status.log', '')

      lines = l.readlines()

      if not lines:
        print("Client not connected.")
        continue

      if not lines[3][:-1].startswith(domain_name):
        print("Client not connected.")
        continue

      domain_name = '_'.join(domain_name.split('_')[::-1]).replace('_', '.')

      ps_script = """function update_dns {
  param(
    [parameter(Mandatory=$true)]
    [string]$record_fqdn
  )

  $old_record = Get-DnsServerResourceRecord -ComputerName epsilon.local -ZoneName kl -Name $record_fqdn
  $old_ip = $old_record.RecordData.IPv4Address.IPAddressToString
  $octets = $old_ip.Split('.')

  if ($octets[1] -eq OLD_OCTET) {
    $octets[1] = NEW_OCTET
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

$domain = "DOMAIN_NAME"

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
}"""

    ps_script = ps_script.replace("DOMAIN_NAME", domain_name).replace("OLD_OCTET", str(old_octet)).replace("NEW_OCTET", str(new_octet))

    try:
        client.execute_ps(ps_script)
        print("Client domain records updated successfully.")
    except Exception as e:
        print(f"Error executing PowerShell script: {e}")

run_script(80, 70)