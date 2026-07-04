# -Hardware Inventory Automation Script
A Python script that automatically collects 19 hardware and software parameters from a Windows workstation in under 5 seconds and outputs them in a standardized inventory format replacing manual, per-machine data collection.

##Features

The script collects:

Manufacturer name and serial number (via Win32_BIOS)
Inventory / asset tag number (via Win32_SystemEnclosure)
Device type detection: Laptop vs Desktop (via battery sensor presence)
CPU model and clock speed (via Win32_Processor)
RAM, auto-rounded to standard market sizes (4 / 8 / 16 / 32 GB)
Storage size, rounded to standard sizes (128 / 256 / 512 / 1024 GB)
Monitor diagonal size (via WmiMonitorBasicDisplayParams)
Printer and scanner presence
Windows activation status (via Win32_SoftwareLicensingProduct)
Hostname, IP address, domain/workgroup, connection type (LAN/Wi-Fi)
Installed antivirus product (via the SecurityCenter2 namespace)

##Requirements

Windows 10 / Windows 11
Python 3.11+
The following Python packages:
pip install psutil wmi
____________________________________________________________________________________________________________
platform, socket, subprocess, and math are part of the Python standard library and require no installation.
____________________________________________________________________________________________________________

##How It Works


Cross-platform data (RAM, disk, network interfaces, battery) is collected using psutil.
Windows-specific data (BIOS, CPU, monitor, licensing, antivirus) is collected using the wmi library, which accesses the Win32 API directly. This library was chosen over the legacy wmic command-line tool, which was removed starting with Windows 11 build 26200+.
RAM/storage rounding uses 2^ceil(log2(actual_GB)) to normalize raw values to standard market sizes.
IP detection filters out virtual adapters (Docker, VirtualBox, VMware, WSL, loopback) to return only the real network-facing IP address.
subprocess is used as a PowerShell-based fallback for data points not available through WMI.

##Notes / Limitations

The script was developed, tested, and validated on a personal machine only.
Deployment on production/corporate workstations was not approved by the department due to internal IT policy on running intern-developed tools on company hardware — this repository is shared for demonstration and portfolio purposes.
Requires the script to be run with sufficient permissions to query WMI (administrator rights recommended).

Developed as part of an internship project
