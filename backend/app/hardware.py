import csv
import io
import platform
import shutil
import subprocess

import psutil


def detect_hardware(data_dir):
    memory = psutil.virtual_memory()
    cpu = platform.processor()
    if platform.system() == "Windows":
        try:
            import winreg
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE,
                               r"HARDWARE\DESCRIPTION\System\CentralProcessor\0") as key:
                cpu = winreg.QueryValueEx(key, "ProcessorNameString")[0].strip()
        except OSError:
            pass
    gpus = []
    try:
        result = subprocess.run(["nvidia-smi", "--query-gpu=name,memory.total,memory.free",
                                 "--format=csv,noheader,nounits"], capture_output=True,
                                text=True, check=True, timeout=5,
                                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
        for name, total, free in csv.reader(io.StringIO(result.stdout)):
            gpus.append({"name": name.strip(), "total_mib": int(total), "free_mib": int(free)})
    except (OSError, subprocess.SubprocessError, ValueError):
        pass
    return {"cpu": cpu, "os": platform.system(), "ram_total_gib": round(memory.total / 2**30, 1),
            "ram_available_gib": round(memory.available / 2**30, 1), "gpus": gpus,
            "disk_free_gib": round(shutil.disk_usage(data_dir).free / 2**30, 1),
            "recommendation": "Qwen3 8B · contexto inicial 4096" if
            any(g["total_mib"] >= 10000 for g in gpus) and memory.total >= 14 * 2**30
            else "Comece com um modelo de 4B ou menor e contexto 2048; valide o uso de memória."}
