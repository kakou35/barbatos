"""
Tests unitaires pour les modules de contrôle système (system.shell, system.files, system.windows_ops).
"""

import asyncio
from pathlib import Path
from system.shell import shell_executor
from system.files import file_manager
from system.windows_ops import windows_ops


def test_shell_execution():
    async def run_shell():
        res = await shell_executor.execute("echo 'BARBATOS_ONLINE'", timeout=10)
        assert res["success"] is True
        assert "BARBATOS_ONLINE" in res["stdout"]

    asyncio.run(run_shell())


def test_shell_security_blacklist():
    async def run_dangerous():
        res = await shell_executor.execute("rm -rf /")
        assert res["success"] is False
        assert "BLOQUÉE" in res["stderr"]

    asyncio.run(run_dangerous())


def test_file_operations():
    test_file = "data/test_temp.txt"
    # Écriture
    w_res = file_manager.write_file(test_file, "Contenu de test Barbatos")
    assert w_res["success"] is True

    # Lecture
    r_res = file_manager.read_file(test_file)
    assert r_res["success"] is True
    assert "Contenu de test Barbatos" in r_res["content"]

    # Suppression
    d_res = file_manager.delete_path(test_file)
    assert d_res["success"] is True


def test_hardware_metrics():
    metrics = windows_ops.get_hardware_metrics()
    assert "cpu_percent" in metrics
    assert "ram_percent" in metrics
    assert metrics["ram_percent"] > 0


if __name__ == "__main__":
    test_shell_execution()
    test_shell_security_blacklist()
    test_file_operations()
    test_hardware_metrics()
    print("Tests Contrôle Système validés avec succès !")
