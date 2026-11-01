"""Readiness checks never connect, pair, or send print jobs."""
import base64
import contextlib
import io
import json
from pathlib import Path
import socket
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from desktop import windows_check as check

ADDRESS = '00:11:22:33:44:55'


class WindowsCheck(unittest.TestCase):
    def run_check(self, *, radio=None, device=None, missing=(), address=ADDRESS):
        with contextlib.ExitStack() as stack:
            stack.enter_context(patch.object(check.sys, 'platform', 'win32'))
            stack.enter_context(patch.object(check.socket, 'AF_BLUETOOTH', 32, create=True))
            stack.enter_context(patch.object(check.importlib.util, 'find_spec', side_effect=lambda name: None if name in missing else object()))
            stack.enter_context(patch.object(check, 'port_free'))
            stack.enter_context(patch.object(check, 'bluetooth', side_effect=radio if isinstance(radio, Exception) else None, return_value=radio or {'radios': 1, 'paired': True}))
            inspector = stack.enter_context(patch.object(check, 'disabled_adapter', side_effect=device if isinstance(device, Exception) else None, return_value=device or {}))
            result = check.report(address, (18635, 18636))
            return result, inspector.call_count

    def status(self, result, name):
        return next(c['status'] for c in result['checks'] if c['check'] == name)

    def test_paired_without_optional_models(self):
        with tempfile.TemporaryDirectory() as folder, patch.object(check, 'ROOT', Path(folder)):
            result, calls = self.run_check()
        self.assertTrue(result['ready']); self.assertEqual(calls, 0)
        self.assertEqual(self.status(result, 'face-model'), 'warning')
        self.assertNotIn(ADDRESS, json.dumps(result))

    def test_missing_dependency_is_actionable(self):
        result, _ = self.run_check(missing=('aiohttp',))
        self.assertFalse(result['ready'])
        self.assertEqual(self.status(result, 'dependencies'), 'error')
        self.assertIn('aiohttp', json.dumps(result))

    def test_adapter_disabled_parent(self):
        result, calls = self.run_check(radio={'radios': 0, 'paired': False}, device={'disabled': False, 'parentDisabled': True})
        self.assertFalse(result['ready']); self.assertEqual(calls, 1)
        self.assertEqual(self.status(result, 'disabled-device'), 'error')

    def test_absent_adapter(self):
        result, _ = self.run_check(radio={'radios': 0, 'paired': False}, device={'disabled': False, 'parentDisabled': False})
        self.assertEqual(self.status(result, 'adapter'), 'error')
        self.assertNotIn('disabled-device', [c['check'] for c in result['checks']])

    def test_permission_failure_is_not_absence(self):
        result, calls = self.run_check(radio=PermissionError('private device details'))
        self.assertEqual(self.status(result, 'adapter'), 'unknown'); self.assertEqual(calls, 0)
        self.assertNotIn('private device details', json.dumps(result))

    def test_inspection_timeout_is_unknown(self):
        result, _ = self.run_check(radio={'radios': 0, 'paired': False}, device=subprocess.TimeoutExpired('powershell', 20))
        self.assertEqual(self.status(result, 'disabled-device'), 'unknown')

    def test_unpaired_and_unknown_pairing(self):
        for paired, status in [(False, 'error'), (None, 'unknown')]:
            result, _ = self.run_check(radio={'radios': 1, 'paired': paired})
            self.assertFalse(result['ready']); self.assertEqual(self.status(result, 'pairing'), status)

    def test_invalid_address_never_queried(self):
        result, _ = self.run_check(address='bad')
        self.assertEqual(self.status(result, 'address'), 'error')
        self.assertNotIn('pairing', [c['check'] for c in result['checks']])

    def test_occupied_port(self):
        with socket.socket() as listener:
            listener.bind(('127.0.0.1', 0)); listener.listen()
            with self.assertRaises(OSError): check.port_free(listener.getsockname()[1])

    def test_duplicate_ports(self):
        with patch.object(check, 'port_free'):
            result = check.report(ADDRESS, (18635, 18635))
        self.assertEqual(self.status(result, 'ports'), 'error')

    @unittest.skipUnless(sys.platform == 'win32', 'PowerShell integration requires Windows')
    def test_parent_query_with_synthetic_devices(self):
        real_run = subprocess.run
        prefix = r"""
function Get-PnpDevice {param($ErrorAction) [pscustomobject]@{Class='Bluetooth';InstanceId='USB\VID_TEST'} }
function Get-PnpDeviceProperty {param($InstanceId,$KeyName,$ErrorAction)
 [pscustomobject]@{KeyName='DEVPKEY_Device_ProblemCode';Data=$(if ($InstanceId -eq 'USB\ROOT_TEST') {22} else {0})}
 [pscustomobject]@{KeyName='DEVPKEY_Device_Parent';Data=$(if ($InstanceId -eq 'USB\VID_TEST') {'USB\ROOT_TEST'} else {''})}
}
"""
        def run(command, **kwargs):
            source = base64.b64decode(command[-1]).decode('utf-16-le')
            command = command[:-1] + [base64.b64encode((prefix + source).encode('utf-16-le')).decode()]
            return real_run(command, **kwargs)
        with patch.object(check.subprocess, 'run', side_effect=run):
            self.assertEqual(check.disabled_adapter(), {'disabled': False, 'parentDisabled': True})
        prefix = "function Get-PnpDevice {throw 'test access denied'}\n"
        with patch.object(check.subprocess, 'run', side_effect=run):
            with self.assertRaises(OSError): check.disabled_adapter()

    def test_json_cli_exit_and_no_private_path(self):
        result = {'ready': False, 'checks': [], 'note': 'read only'}
        with patch.object(check, 'report', return_value=result), contextlib.redirect_stdout(io.StringIO()) as output:
            self.assertEqual(check.main(['--json']), 1)
        self.assertEqual(json.loads(output.getvalue()), result)


if __name__ == '__main__':
    unittest.main()
