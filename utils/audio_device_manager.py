"""Audio device detection and management"""
import logging
from dataclasses import dataclass
from typing import List, Optional

log = logging.getLogger("Translator")

# Audio library availability flags
SOUNDDEVICE_AVAILABLE = False
PYAUDIO_AVAILABLE = False

# Try to import audio libraries, but don't fail if they're not available
def _check_audio_libraries():
    global SOUNDDEVICE_AVAILABLE, PYAUDIO_AVAILABLE
    
    try:
        import sounddevice as sd
        SOUNDDEVICE_AVAILABLE = True
    except (ImportError, OSError) as e:
        SOUNDDEVICE_AVAILABLE = False
        log.warning(f"SoundDevice not available: {e}")

    try:
        import pyaudio
        PYAUDIO_AVAILABLE = True
    except ImportError as e:
        PYAUDIO_AVAILABLE = False
        log.warning(f"PyAudio not available: {e}")

# Check libraries when module is imported
_check_audio_libraries()

@dataclass
class AudioDevice:
    """Represents an audio device"""
    index: int
    name: str
    max_input_channels: int
    max_output_channels: int
    default_samplerate: float
    is_input: bool
    is_output: bool
    host_api: str

class AudioDeviceManager:
    """Manages audio device detection and selection"""
    def __init__(self):
        if PYAUDIO_AVAILABLE:
            try:
                self.pa = pyaudio.PyAudio()
            except Exception as e:
                log.warning(f"Failed to initialize PyAudio: {e}")
                self.pa = None
        else:
            self.pa = None
        self.devices = self._detect_devices()
        self.input_devices = [d for d in self.devices if d.is_input]
    
    def _detect_devices(self) -> List[AudioDevice]:
        """Detect all available audio devices"""
        devices = []
        
        if PYAUDIO_AVAILABLE:
            try:
                for i in range(self.pa.get_device_count()):
                    info = self.pa.get_device_info_by_index(i)
                    device = AudioDevice(
                        index=i,
                        name=info['name'],
                        max_input_channels=info['maxInputChannels'],
                        max_output_channels=info['maxOutputChannels'],
                        default_samplerate=info['defaultSampleRate'],
                        is_input=info['maxInputChannels'] > 0,
                        is_output=info['maxOutputChannels'] > 0,
                        host_api=self.pa.get_host_api_info_by_index(info['hostApi'])['name']
                    )
                    devices.append(device)
            except Exception as e:
                log.error(f"Error detecting devices with PyAudio: {e}")
        
        # Fallback to sounddevice
        if SOUNDDEVICE_AVAILABLE:
            try:
                sd_devices = sd.query_devices()
                for i, device_info in enumerate(sd_devices):
                    device = AudioDevice(
                        index=i,
                        name=device_info['name'],
                        max_input_channels=device_info['max_input_channels'],
                        max_output_channels=device_info['max_output_channels'],
                        default_samplerate=device_info['default_samplerate'],
                        is_input=device_info['max_input_channels'] > 0,
                        is_output=device_info['max_output_channels'] > 0,
                        host_api=device_info.get('hostapi', 'Unknown')
                    )
                    devices.append(device)
            except Exception as e:
                log.error(f"Error detecting devices with sounddevice: {e}")
        
        # If no devices found, create a dummy device
        if not devices:
            log.warning("No audio devices detected, creating dummy device")
            devices.append(AudioDevice(
                index=0,
                name="Default Microphone",
                max_input_channels=1,
                max_output_channels=0,
                default_samplerate=16000,
                is_input=True,
                is_output=False,
                host_api="Unknown"
            ))
        
        return devices
    
    def get_default_input_device(self) -> Optional[AudioDevice]:
        """Get the default input device"""
        if PYAUDIO_AVAILABLE:
            try:
                default_info = self.pa.get_default_input_device_info()
                for device in self.input_devices:
                    if device.index == default_info['index']:
                        return device
            except:
                pass
        
        # Fallback to sounddevice
        if SOUNDDEVICE_AVAILABLE:
            try:
                default_device = sd.default.device[0]  # input device
                for device in self.input_devices:
                    if device.index == default_device:
                        return device
            except:
                pass
        
        return self.input_devices[0] if self.input_devices else None
    
    def get_loopback_device(self) -> Optional[AudioDevice]:
        """Get loopback device with validation and better error handling"""
        keywords = ['stereo mix', 'loopback', 'wave out', 'what u hear', 'wave-out', 'waveout', 'mix', 'monitor']
        candidates = []
        
        log.info("Searching for loopback devices...")
        
        # Find all potential loopback devices
        for device in self.input_devices:
            device_name_lower = device.name.lower()
            if any(k in device_name_lower for k in keywords):
                candidates.append(device)
                log.info(f"Found potential loopback device: {device.name}")
        
        # Try to find a working device by testing each candidate
        for device in candidates:
            try:
                # Quick test with sounddevice
                test_stream = sd.InputStream(
                    channels=1,
                    samplerate=int(device.default_samplerate),
                    device=device.index,
                    blocksize=1024
                )
                test_stream.close()
                log.info(f"Found working loopback device: {device.name}")
                return device
            except Exception as e:
                log.warning(f"Loopback device {device.name} failed test: {e}")
                continue
        
        # If no keywords match, try the default input device if it's not a microphone
        try:
            default = self.get_default_input_device()
            if default and 'mic' not in default.name.lower() and 'microphone' not in default.name.lower():
                log.info(f"Trying default input as loopback: {default.name}")
                # Test this device too
                try:
                    test_stream = sd.InputStream(
                        channels=1,
                        samplerate=int(default.default_samplerate),
                        device=default.index,
                        blocksize=1024
                    )
                    test_stream.close()
                    return default
                except Exception as e:
                    log.warning(f"Default device {default.name} failed test: {e}")
        except Exception as e:
            log.warning(f"Default device check failed: {e}")
        
        # Last resort: try any input device that might work
        log.warning("No specific loopback device found, trying all input devices...")
        for device in self.input_devices:
            try:
                test_stream = sd.InputStream(
                    channels=1,
                    samplerate=int(device.default_samplerate),
                    device=device.index,
                    blocksize=1024
                )
                test_stream.close()
                log.info(f"Using fallback device: {device.name}")
                return device
            except Exception as e:
                log.debug(f"Device {device.name} failed test: {e}")
                continue
        
        log.error("No working audio input devices found")
        return None
    
    def test_device(self, device: AudioDevice, duration: float = 1.0) -> bool:
        """Test if a device is working"""
        if SOUNDDEVICE_AVAILABLE:
            try:
                # Use sounddevice for testing
                test_stream = sd.InputStream(
                    channels=1,
                    samplerate=int(device.default_samplerate),
                    device=device.index,
                    blocksize=1024
                )
                test_stream.close()
                return True
            except:
                return False
        else:
            # If no audio libraries available, assume device works
            return True
    
    def cleanup(self):
        """Clean up PyAudio resources"""
        if PYAUDIO_AVAILABLE and self.pa:
            self.pa.terminate()

# Global instance
audio_device_manager = AudioDeviceManager()
