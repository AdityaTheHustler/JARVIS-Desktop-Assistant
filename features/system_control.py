import os
import platform
import psutil
import ctypes
import subprocess
from typing import Dict, List, Optional, Tuple
import json
from datetime import datetime
import time

class SystemController:
    def __init__(self):
        self.system_info = self._get_system_info()
        self.os_type = platform.system()
        self.monitoring_active = False

    def _get_system_info(self) -> Dict:
        """Get basic system information."""
        return {
            'platform': platform.system(),
            'platform_version': platform.version(),
            'processor': platform.processor(),
            'memory': {
                'total': psutil.virtual_memory().total,
                'available': psutil.virtual_memory().available
            },
            'cpu_count': psutil.cpu_count(),
            'battery': self._get_battery_info()
        }

    def _get_battery_info(self) -> Dict:
        """Get battery information."""
        try:
            battery = psutil.sensors_battery()
            if battery:
                return {
                    'percent': battery.percent,
                    'power_plugged': battery.power_plugged,
                    'time_left': battery.secsleft if battery.secsleft != -2 else None
                }
            return {'percent': None, 'power_plugged': None, 'time_left': None}
        except:
            return {'percent': None, 'power_plugged': None, 'time_left': None}

    def get_system_stats(self) -> Dict:
        """Get current system statistics."""
        return {
            'cpu_percent': psutil.cpu_percent(interval=1),
            'memory_percent': psutil.virtual_memory().percent,
            'disk_usage': psutil.disk_usage('/').percent,
            'battery': self._get_battery_info()
        }

    def lock_system(self) -> bool:
        """Lock the system."""
        try:
            if self.os_type == 'Windows':
                os.system('rundll32.exe user32.dll,LockWorkStation')
            elif self.os_type == 'Linux':
                os.system('gnome-screensaver-command -l')
            elif self.os_type == 'Darwin':  # macOS
                os.system('/System/Library/CoreServices/Menu\\ Extras/User.menu/Contents/Resources/CGSession -suspend')
            return True
        except Exception as e:
            print(f"Lock error: {e}")
            return False

    def shutdown_system(self) -> bool:
        """Shutdown the computer."""
        try:
            if self.os_type == 'Windows':
                os.system('shutdown /s /t 10')
            elif self.os_type == 'Linux':
                os.system('shutdown -h +1')
            elif self.os_type == 'Darwin':  # macOS
                os.system('shutdown -h +1')
            return True
        except Exception as e:
            print(f"Shutdown error: {e}")
            return False

    def restart_system(self) -> bool:
        """Restart the computer."""
        try:
            if self.os_type == 'Windows':
                os.system('shutdown /r /t 10')
            elif self.os_type == 'Linux':
                os.system('shutdown -r now')
            elif self.os_type == 'Darwin':  # macOS
                os.system('shutdown -r now')
            return True
        except Exception as e:
            print(f"Restart error: {e}")
            return False

    def sleep_system(self) -> bool:
        """Put the computer to sleep."""
        try:
            if self.os_type == 'Windows':
                os.system('rundll32.exe powrprof.dll,SetSuspendState 0,1,0')
            elif self.os_type == 'Linux':
                os.system('systemctl suspend')
            elif self.os_type == 'Darwin':  # macOS
                os.system('pmset sleepnow')
            return True
        except Exception as e:
            print(f"Sleep error: {e}")
            return False

    def set_system_volume(self, volume: int) -> bool:
        """Set system volume (0-100)."""
        try:
            if platform.system() == 'Windows':
                from ctypes import cast, POINTER
                from comtypes import CLSCTX_ALL
                from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
                
                devices = AudioUtilities.GetSpeakers()
                interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
                volume_interface = cast(interface, POINTER(IAudioEndpointVolume))
                volume_interface.SetMasterVolumeLevelScalar(volume / 100, None)
                return True
            else:
                # For Linux/Mac
                subprocess.run(['amixer', 'set', 'Master', f'{volume}%'])
                return True
        except Exception as e:
            print(f"Error setting volume: {e}")
            return False

    def get_running_processes(self) -> List[Dict]:
        """Get list of running processes."""
        processes = []
        for proc in psutil.process_iter(['pid', 'name', 'username', 'memory_percent', 'cpu_percent']):
            try:
                processes.append(proc.info)
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass
        return processes

    def kill_process(self, pid: int) -> bool:
        """Kill a process by PID."""
        try:
            process = psutil.Process(pid)
            process.terminate()
            return True
        except Exception as e:
            print(f"Error killing process: {e}")
            return False

    def get_installed_apps(self) -> List[Dict]:
        """Get list of installed applications."""
        apps = []
        if platform.system() == 'Windows':
            import winreg
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall") as key:
                for i in range(winreg.QueryInfoKey(key)[0]):
                    try:
                        subkey_name = winreg.EnumKey(key, i)
                        with winreg.OpenKey(key, subkey_name) as subkey:
                            try:
                                name = winreg.QueryValueEx(subkey, "DisplayName")[0]
                                version = winreg.QueryValueEx(subkey, "DisplayVersion")[0]
                                apps.append({'name': name, 'version': version})
                            except:
                                continue
                    except:
                        continue
        return apps

    def open_application(self, app_name: str) -> bool:
        """Open an application by name."""
        try:
            if platform.system() == 'Windows':
                os.startfile(app_name)
            else:
                subprocess.Popen([app_name])
            return True
        except Exception as e:
            print(f"Error opening application: {e}")
            return False

    def get_performance_metrics(self) -> Dict:
        """Get current system performance metrics."""
        try:
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)
            cpu_cores = psutil.cpu_count(logical=False)
            cpu_threads = psutil.cpu_count(logical=True)
            
            # Memory usage
            memory = psutil.virtual_memory()
            memory_total = self._format_bytes(memory.total)
            memory_used = self._format_bytes(memory.used)
            memory_percent = memory.percent
            
            # Disk usage
            disk = psutil.disk_usage('/')
            disk_total = self._format_bytes(disk.total)
            disk_used = self._format_bytes(disk.used)
            disk_percent = disk.percent
            
            # Network stats
            net_io = psutil.net_io_counters()
            net_sent = self._format_bytes(net_io.bytes_sent)
            net_recv = self._format_bytes(net_io.bytes_recv)
            
            # Battery info if available
            battery_percent = None
            battery_time_left = None
            if hasattr(psutil, "sensors_battery"):
                battery = psutil.sensors_battery()
                if battery:
                    battery_percent = battery.percent
                    if battery.secsleft != psutil.POWER_TIME_UNLIMITED and battery.secsleft != psutil.POWER_TIME_UNKNOWN:
                        mins, secs = divmod(battery.secsleft, 60)
                        hours, mins = divmod(mins, 60)
                        battery_time_left = f"{hours:02d}:{mins:02d}"
            
            metrics = {
                'cpu_percent': cpu_percent,
                'cpu_cores': cpu_cores,
                'cpu_threads': cpu_threads,
                'memory_total': memory_total,
                'memory_used': memory_used,
                'memory_percent': memory_percent,
                'disk_total': disk_total,
                'disk_used': disk_used,
                'disk_percent': disk_percent,
                'net_sent': net_sent,
                'net_recv': net_recv,
                'battery_percent': battery_percent,
                'battery_time_left': battery_time_left
            }
            
            # Get top processes by CPU usage
            processes = []
            for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
                try:
                    process_info = proc.info
                    if process_info['cpu_percent'] > 0.5:  # Only include significant CPU usage
                        processes.append({
                            'pid': process_info['pid'],
                            'name': process_info['name'],
                            'cpu_percent': process_info['cpu_percent'],
                            'memory_percent': process_info['memory_percent']
                        })
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    pass
            
            # Sort by CPU usage and take top 5
            top_processes = sorted(processes, key=lambda x: x['cpu_percent'], reverse=True)[:5]
            metrics['top_processes'] = top_processes
            
            return metrics
        except Exception as e:
            print(f"Error getting performance metrics: {e}")
            return {'error': str(e)}

    def _format_bytes(self, bytes_value: int) -> str:
        """Format bytes to human-readable format."""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if bytes_value < 1024:
                return f"{bytes_value:.2f} {unit}"
            bytes_value /= 1024
        return f"{bytes_value:.2f} PB" 