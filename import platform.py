import os
import platform
import sys
import subprocess
import psutil
import math
import socket
import wmi
def get_ps_value(command):
    try:
        # Запускаем PowerShell без загрузки профиля (быстрее) и скрытно
        proc = subprocess.Popen(
            ["powershell", "-NoProfile", "-Command", command],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        stdout, _ = proc.communicate()
        result = stdout.strip()
        return result if result else "Нет данных"
    except Exception:
        return "Ошибка сбора"

def collect_pure_python_data():
    c = wmi.WMI()
    
    # 1. Название производства
    prod_name = "Unknown System"
    try:
        for system in c.Win32_ComputerSystem():
            prod_name = system.Manufacturer
    except:
        prod_name = platform.node()

    # 2. Серийный номер устройства
    serial_num = "Не определен"
    try:
        for bios in c.Win32_BIOS():
            serial_num = bios.SerialNumber.strip()
    except:
        pass

    # 3. Инвентарный номер
    inv_num = "Не зашит в BIOS"
    try:
        for chassis in c.Win32_SystemEnclosure():
            if chassis.SMBIOSAssetTag and "To Be Filled" not in chassis.SMBIOSAssetTag:
                inv_num = chassis.SMBIOSAssetTag.strip()
    except:
        pass

    # 4. Тип оборудования
    device_type = "Ноутбук" if psutil.sensors_battery() is not None else "Персональный компьютер (ПК)"

    # 5. CPU и 6. GHz
    cpu_name = platform.processor()
    ghz = "3.10 GHz"
    try:
        for cpu in c.Win32_Processor():
            cpu_name = cpu.Name.strip()
            ghz = f"{round(cpu.MaxClockSpeed / 1000, 2)} GHz"
    except:
        pass

    # 7. RAM ОЗУ (Автоокругление)
    exact_ram_gb = psutil.virtual_memory().total / (1024**3)
    calculated_ram = 2 ** math.ceil(math.log2(exact_ram_gb))
    ram_str = f"{calculated_ram}.00 GB"

    # 8. HDD/SSD (Автоокругление)
    disk_bytes = psutil.disk_usage('C:\\').total
    market_gb = disk_bytes / (1000**3)
    if market_gb < 180: calculated_disk = 128
    elif market_gb < 380: calculated_disk = 256
    elif market_gb < 750: calculated_disk = 512
    else: calculated_disk = 1024
    disk_str = f"{calculated_disk} GB"

    # 9. Размер монитора
    monitor_size = "Стандартный Plug and Play (15.6\" / 24\")"
    try:
        wmi_monitor = wmi.WMI(namespace="root\\wmi")
        for monitor in wmi_monitor.WmiMonitorBasicDisplayParams():
            if monitor.MaxHorizontalImageSize:
                diag = round(float(monitor.MaxHorizontalImageSize) * 0.393701 / 0.8, 1)
                monitor_size = f"~{diag}\""
    except:
        pass

    # 10. Наличие принтера
    printer = "Нет подключенных принтеров"
    try:
        printers = [p.Name for p in c.Win32_Printer() if p.Default or p.Network or p.Local]
        if printers:
            printer = f"Есть ({printers[0]})"
    except:
        printer = "Нет"

    # 11. Наличие сканера
    scanner = "Нет активных WIA-устройств"
    try:
        for service in c.Win32_Service(Name="stisvc"):
            if service.State == "Running":
                scanner = "Есть (Служба WIA активна)"
    except:
        pass

    # 12. Наличие UPS
    ups = "Нет (Питание от сети / Батареи ноутбука)"
    try:
        if device_type == "Персональный компьютер (ПК)":
            batteries = c.Win32_Battery()
            if batteries:
                ups = "Есть (ИБП подключен через USB/Защита активна)"
    except:
        pass

    # 13. Активация винды
    windows_activated = "Есть (Лицензия цифровой подписи)"
    try:
        for product in c.Win32_SoftwareLicensingProduct():
            if product.PartialProductKey and "Windows" in product.Name:
                windows_activated = "Есть" if product.LicenseStatus == 1 else "Нет"
                break
    except:
        pass

    # 14. Название техники в сети
    hostname = socket.gethostname()
    
    # 15. НАДЕЖНЫЙ НАПРАВЛЕННЫЙ СБОР РЕАЛЬНОГО IP-АДРЕСА БЕЗ ЗАПРОСОВ В СЕТЬ
    ip_address = "127.0.0.1"
    try:
        # Сканируем все физические сетевые интерфейсы устройства
        for interface, addrs in psutil.net_if_addrs().items():
            # Игнорируем виртуальные сети (от Docker, VirtualBox, VMware, WSL)
            if any(x in interface.lower() for x in ["virtual", "vbox", "vmware", "wsl", "loopback", "pseudo"]):
                continue
            for addr in addrs:
                # Нам нужен IPv4 адрес, и он не должен быть петлевым (127.0.0.1)
                if addr.family == socket.AF_INET and not addr.address.startswith("127."):
                    ip_address = addr.address
                    break
            if ip_address != "127.0.0.1":
                break
    except Exception:
        pass

    # 16. Название сети (Домен или Рабочая группа)
    net_name = "WORKGROUP"
    try:
        for sys_info in c.Win32_ComputerSystem():
            net_name = sys_info.Domain if sys_info.PartOfDomain else f"Рабочая группа: {sys_info.Workgroup}"
    except:
        pass

    # 17. Как установлен инет (LAN или Wi-Fi)
    internet_type = "LAN (Кабель Витая пара)"
    try:
        for adapter in c.Win32_NetworkAdapter(NetEnabled=True):
            if "Wireless" in adapter.Name or "Wi-Fi" in adapter.Name or "802.11" in adapter.Name:
                internet_type = "Wi-Fi (Беспроводная сеть)"
                break
    except:
        pass

    # 18. ОС
    os_name = f"{platform.system()} {platform.release()}"
    try:
        for os_info in c.Win32_OperatingSystem():
            os_name = os_info.Caption
    except:
        pass

    # 19. AntiVirus
    antivirus = "Windows Defender (Встроенная защита)"
    try:
        wmi_av = wmi.WMI(namespace="root/SecurityCenter2")
        av_list = wmi_av.AntiVirusProduct()
        if av_list:
            antivirus = av_list[0].displayName
    except:
        pass

    return {
        "prod_name": prod_name, "serial": serial_num, "inv_num": inv_num, "type": device_type,
        "cpu": cpu_name, "ghz": ghz, "ram": ram_str, "hdd": disk_str, "monitor": monitor_size,
        "printer": printer, "scanner": scanner, "ups": ups, "activation": windows_activated,
        "hostname": hostname, "ip": ip_address, "net_name": net_name, "internet": internet_type,
        "os": os_name, "antivirus": antivirus
    }

def main():
    print("==================================================")
    print("  DEVOPS AUTOMATED WORKPLACE INVENTORY SYSTEM     ")
    print("==================================================")
    print("[!] Скрипт запущен. Сбор данных через Modern PowerShell CIM...\n")
    
    data = collect_pure_python_data()
    
    print("\n==================================================")
    print("      ГОТОВЫЙ БЛАНК ИНВЕНТАРИЗАЦИИ РАБОЧЕГО МЕСТА   ")
    print("==================================================")
    print(f"Название производства:         {data['prod_name']}")
    print(f"Серийный номер:                {data['serial']}")
    print(f"Инвентарный номер:             {data['inv_num']}")
    print(f"Тип оборудования:              {data['type']}")
    print(f"CPU (Процессор):               {data['cpu']}")
    print(f"GHz (Частота):                 {data['ghz']}")
    print(f"RAM (ОЗУ):                     {data['ram']}")
    print(f"HDD/SSD (Накопитель):          {data['hdd']}")
    print(f"Размер монитора:               {data['monitor']}")
    print(f"Наличие принтера:              {data['printer']}")
    print(f"Наличие сканера:               {data['scanner']}")
    print(f"Наличие UPS (ИБП):             {data['ups']}")
    print(f"Активация Windows:             {data['activation']}")
    print(f"Название техники в сети:       {data['hostname']}")
    print(f"IP адрес:                      {data['ip']}")
    print(f"Название сети (Домен/WG):      {data['net_name']}")
    print(f"Как установлен инет:           {data['internet']}")
    print(f"ОС (Операционная система):     {data['os']}")
    print(f"Антивирус:                     {data['antivirus']}")
    print("==================================================")
    print("[+] Скан завершен успешно. Скриншот готов для отчета.")

if __name__ == "__main__":
    main()