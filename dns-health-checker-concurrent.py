from pypsrp.client import Client
from concurrent.futures import ThreadPoolExecutor
from glob import glob
import os

def update_dns(domain_name, old_octet, new_octet):
  client = Client("epsilon.local", username=os.environ.get("DNSCHECKER_USER"), password=os.environ.get("DNSCHECKER_PASSWORD"), ssl=False)

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
    print(f"Client domain records updated successfully: {domain_name}")
  except Exception as e:
    print(f"Error executing PowerShell script for domain {domain_name}: {e}")
  finally:
    client.close()

def run_script(old_octet, new_octet):
  log_files = glob("/etc/openvpn/logs/*-status.log")
  with ThreadPoolExecutor(max_workers=8) as executor:
    for log in log_files:
      domain_name = log.split('/')[-1].replace('-status.log', '')
      with open(log, "r") as l:
        lines = l.readlines()

        if not lines:
          print(f"Client not connected: {domain_name}")
          continue

        if not lines[3][:-1].startswith(domain_name):
          print(f"Client not connected: {domain_name}")
          continue

      executor.submit(update_dns, domain_name, old_octet, new_octet)

if __name__ == "__main__":
  run_script(80, 70)