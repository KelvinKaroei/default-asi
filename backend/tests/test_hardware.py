from unittest.mock import patch
from app.hardware import detect_hardware


def test_gpu_unavailable_does_not_hide_ram_and_cpu(tmp_path):
    with patch("app.hardware.subprocess.run", side_effect=FileNotFoundError):
        result = detect_hardware(tmp_path)
    assert result["gpus"] == []
    assert result["ram_total_gib"] > 0
    assert result["disk_free_gib"] > 0
