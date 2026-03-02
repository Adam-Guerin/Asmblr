"""
Brain-Computer Interface for Asmblr
Direct brain-to-computer communication and neural control systems
"""

import asyncio
import logging
from datetime import datetime
from typing import Any
from dataclasses import dataclass, asdict
from enum import Enum
import uuid
import numpy as np
import scipy.signal as signal

logger = logging.getLogger(__name__)

class BCIType(Enum):
    """Brain-Computer Interface types"""
    EEG = "eeg"  # Electroencephalography
    MEG = "meg"  # Magnetoencephalography
    ECOG = "ecog"  # Electrocorticography
    INTRACORTICAL = "intracortical"
    DEEP_BRAIN = "deep_brain"
    OPTOGENETIC = "optogenetic"
    ULTRASONIC = "ultrasonic"
    FUNCTIONAL_NIRS = "functional_nirs"

class SignalType(Enum):
    """Neural signal types"""
    ALPHA = "alpha"  # 8-13 Hz
    BETA = "beta"    # 13-30 Hz
    GAMMA = "gamma"  # 30-100 Hz
    DELTA = "delta"  # 0.5-4 Hz
    THETA = "theta"  # 4-8 Hz
    MU = "mu"       # 8-13 Hz (sensorimotor)
    ERP = "erp"     # Event-related potentials
    SSVEP = "ssvep" # Steady-state visually evoked potentials
    P300 = "p300"   # P300 component

class CommandType(Enum):
    """Command types for BCI"""
    MOTOR_IMAGERY = "motor_imagery"
    STEADY_STATE = "steady_state"
    P300_SPELLING = "p300_spelling"
    SSVEP_CONTROL = "ssvep_control"
    EMOTION_DETECTION = "emotion_detection"
    ATTENTION_MONITORING = "attention_monitoring"
    SLEEP_DETECTION = "sleep_detection"
    SEIZURE_DETECTION = "seizure_detection"

class IntentType(Enum):
    """Intent types for BCI"""
    MOVE_LEFT = "move_left"
    MOVE_RIGHT = "move_right"
    MOVE_UP = "move_up"
    MOVE_DOWN = "move_down"
    SELECT = "select"
    ACTIVATE = "activate"
    DEACTIVATE = "deactivate"
    ZOOM_IN = "zoom_in"
    ZOOM_OUT = "zoom_out"
    SCROLL = "scroll"

@dataclass
class BrainSignal:
    """Brain signal data"""
    id: str
    signal_type: SignalType
    channel_data: np.ndarray
    sampling_rate: float
    timestamp: datetime
    duration: float
    quality_score: float
    metadata: dict[str, Any]

@dataclass
class BCICommand:
    """BCI command"""
    id: str
    command_type: CommandType
    intent: IntentType
    confidence: float
    parameters: dict[str, Any]
    timestamp: datetime
    user_id: str
    device_id: str

@dataclass
class Electrode:
    """Electrode configuration"""
    id: str
    name: str
    position: tuple[float, float, float]  # 3D position
    impedance: float
    signal_quality: float
    is_active: bool
    last_calibration: datetime

@dataclass
class BCIUser:
    """BCI user profile"""
    id: str
    name: str
    age: int
    gender: str
    medical_history: dict[str, Any]
    calibration_data: dict[str, Any]
    performance_metrics: dict[str, float]
    preferences: dict[str, Any]
    created_at: datetime
    last_session: datetime

@dataclass
class BCIDevice:
    """BCI device configuration"""
    id: str
    name: str
    bci_type: BCIType
    electrodes: list[Electrode]
    sampling_rate: float
    bandwidth: tuple[float, float]
    noise_level: float
    is_connected: bool
    calibration_status: str
    firmware_version: str

class EEGProcessor:
    """EEG signal processor"""
    
    def __init__(self, sampling_rate: float = 250.0):
        self.sampling_rate = sampling_rate
        self.filter_order = 4
        self.notch_freq = 50.0  # Power line noise
        self.bandpass_ranges = {
            SignalType.DELTA: (0.5, 4.0),
            SignalType.THETA: (4.0, 8.0),
            SignalType.ALPHA: (8.0, 13.0),
            SignalType.BETA: (13.0, 30.0),
            SignalType.GAMMA: (30.0, 100.0),
            SignalType.MU: (8.0, 13.0)
        }
    
    def preprocess_signal(self, raw_signal: np.ndarray) -> np.ndarray:
        """Preprocess raw EEG signal"""
        try:
            # Apply bandpass filter (0.5-100 Hz)
            nyquist = self.sampling_rate / 2
            low = 0.5 / nyquist
            high = 100.0 / nyquist
            
            b, a = signal.butter(self.filter_order, [low, high], btype='band')
            filtered = signal.filtfilt(b, a, raw_signal)
            
            # Apply notch filter for power line noise
            notch_low = (self.notch_freq - 2) / nyquist
            notch_high = (self.notch_freq + 2) / nyquist
            
            b_notch, a_notch = signal.butter(self.filter_order, [notch_low, notch_high], btype='bandstop')
            filtered = signal.filtfilt(b_notch, a_notch, filtered)
            
            # Remove DC offset
            filtered = filtered - np.mean(filtered)
            
            return filtered
            
        except Exception as e:
            logger.error(f"Error preprocessing EEG signal: {e}")
            return raw_signal
    
    def extract_features(self, signal: np.ndarray, signal_type: SignalType) -> dict[str, float]:
        """Extract features from EEG signal"""
        try:
            features = {}
            
            # Time domain features
            features['mean'] = np.mean(signal)
            features['std'] = np.std(signal)
            features['var'] = np.var(signal)
            features['rms'] = np.sqrt(np.mean(signal**2))
            features['skewness'] = self._calculate_skewness(signal)
            features['kurtosis'] = self._calculate_kurtosis(signal)
            
            # Frequency domain features
            freqs, psd = self._calculate_psd(signal)
            
            # Band power
            if signal_type in self.bandpass_ranges:
                low, high = self.bandpass_ranges[signal_type]
                band_mask = (freqs >= low) & (freqs <= high)
                band_power = np.mean(psd[band_mask])
                features['band_power'] = band_power
                features['relative_band_power'] = band_power / np.sum(psd)
            
            # Peak frequency
            peak_idx = np.argmax(psd)
            features['peak_frequency'] = freqs[peak_idx]
            
            # Spectral entropy
            features['spectral_entropy'] = self._calculate_spectral_entropy(psd)
            
            return features
            
        except Exception as e:
            logger.error(f"Error extracting EEG features: {e}")
            return {}
    
    def _calculate_skewness(self, signal: np.ndarray) -> float:
        """Calculate skewness of signal"""
        try:
            mean = np.mean(signal)
            std = np.std(signal)
            if std == 0:
                return 0.0
            return np.mean(((signal - mean) / std) ** 3)
        except:
            return 0.0
    
    def _calculate_kurtosis(self, signal: np.ndarray) -> float:
        """Calculate kurtosis of signal"""
        try:
            mean = np.mean(signal)
            std = np.std(signal)
            if std == 0:
                return 0.0
            return np.mean(((signal - mean) / std) ** 4) - 3
        except:
            return 0.0
    
    def _calculate_psd(self, signal: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        """Calculate power spectral density"""
        try:
            freqs, psd = signal.welch(signal, fs=self.sampling_rate, nperseg=1024)
            return freqs, psd
        except:
            return np.array([]), np.array([])
    
    def _calculate_spectral_entropy(self, psd: np.ndarray) -> float:
        """Calculate spectral entropy"""
        try:
            if len(psd) == 0:
                return 0.0
            
            # Normalize PSD
            psd_norm = psd / np.sum(psd)
            
            # Calculate entropy
            entropy = -np.sum(psd_norm * np.log2(psd_norm + 1e-10))
            
            return entropy
        except:
            return 0.0

class MotorImageryClassifier:
    """Motor imagery classification for BCI"""
    
    def __init__(self, num_channels: int = 64):
        self.num_channels = num_channels
        self.eeg_processor = EEGProcessor()
        self.csp_filters = None
        self.classifier = None
        self.reference_patterns = {}
        
    def train_csp(self, training_data: dict[str, np.ndarray]) -> bool:
        """Train Common Spatial Pattern filters"""
        try:
            # Calculate covariance matrices for each class
            cov_matrices = {}
            for class_label, data in training_data.items():
                cov_matrices[class_label] = self._calculate_covariance(data)
            
            # Solve generalized eigenvalue problem
            classes = list(cov_matrices.keys())
            if len(classes) >= 2:
                cov1, cov2 = cov_matrices[classes[0]], cov_matrices[classes[1]]
                
                # Simplified CSP calculation
                eigenvalues, eigenvectors = self._solve_gevp(cov1, cov2)
                
                # Select CSP filters
                self.csp_filters = eigenvectors[:, :self.num_channels//2]
                
                logger.info(f"Trained CSP filters for {len(classes)} classes")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error training CSP: {e}")
            return False
    
    def _calculate_covariance(self, data: np.ndarray) -> np.ndarray:
        """Calculate covariance matrix"""
        try:
            # Data shape: (trials, channels, samples)
            cov_sum = np.zeros((self.num_channels, self.num_channels))
            
            for trial in data:
                # Preprocess trial
                processed_trial = self.eeg_processor.preprocess_signal(trial.T)
                
                # Calculate covariance
                cov = np.cov(processed_trial)
                cov_sum += cov
            
            return cov_sum / len(data)
            
        except Exception as e:
            logger.error(f"Error calculating covariance: {e}")
            return np.eye(self.num_channels)
    
    def _solve_gevp(self, cov1: np.ndarray, cov2: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        """Solve generalized eigenvalue problem"""
        try:
            # Simplified eigenvalue decomposition
            # In practice, would use proper generalized eigenvalue solver
            combined_cov = cov1 + cov2
            eigenvalues, eigenvectors = np.linalg.eig(combined_cov)
            
            return eigenvalues, eigenvectors
            
        except Exception as e:
            logger.error(f"Error solving GEVP: {e}")
            return np.ones(self.num_channels), np.eye(self.num_channels)
    
    def classify_motor_imagery(self, eeg_data: np.ndarray) -> dict[str, float]:
        """Classify motor imagery from EEG data"""
        try:
            if self.csp_filters is None:
                return {"left": 0.5, "right": 0.5}
            
            # Apply CSP filters
            csp_data = np.dot(self.csp_filters.T, eeg_data)
            
            # Extract features
            features = []
            for i in range(csp_data.shape[0]):
                channel_data = csp_data[i, :]
                channel_features = self.eeg_processor.extract_features(
                    channel_data, SignalType.MU
                )
                features.append(channel_features.get('band_power', 0.0))
            
            # Simple classification based on feature patterns
            # In practice, would use trained classifier
            left_score = np.mean(features[:len(features)//2])
            right_score = np.mean(features[len(features)//2:])
            
            # Normalize scores
            total = left_score + right_score
            if total > 0:
                left_prob = left_score / total
                right_prob = right_score / total
            else:
                left_prob = right_prob = 0.5
            
            return {"left": left_prob, "right": right_prob}
            
        except Exception as e:
            logger.error(f"Error classifying motor imagery: {e}")
            return {"left": 0.5, "right": 0.5}

class SSVEPDetecter:
    """Steady-State Visually Evoked Potentials detector"""
    
    def __init__(self, sampling_rate: float = 250.0):
        self.sampling_rate = sampling_rate
        self.target_frequencies = [6.0, 7.0, 8.0, 9.0, 10.0]  # Hz
        self.harmonics = [1, 2, 3]  # First 3 harmonics
        
    def detect_ssvep(self, eeg_data: np.ndarray, duration: float) -> dict[str, float]:
        """Detect SSVEP responses"""
        try:
            # Calculate PSD
            freqs, psd = signal.welch(eeg_data, fs=self.sampling_rate, nperseg=1024)
            
            # Calculate SNR for each target frequency
            snr_values = {}
            
            for target_freq in self.target_frequencies:
                signal_power = 0.0
                noise_power = 0.0
                
                # Calculate signal power at target frequency and harmonics
                for harmonic in self.harmonics:
                    freq = target_freq * harmonic
                    if freq < self.sampling_rate / 2:
                        # Find closest frequency bin
                        freq_idx = np.argmin(np.abs(freqs - freq))
                        signal_power += psd[freq_idx]
                
                # Calculate noise power in surrounding frequencies
                for target_freq in self.target_frequencies:
                    for harmonic in self.harmonics:
                        freq = target_freq * harmonic
                        if freq < self.sampling_rate / 2:
                            # Noise band: ±2 Hz around target
                            noise_low = max(0.5, freq - 2.0)
                            noise_high = min(self.sampling_rate / 2 - 0.5, freq + 2.0)
                            
                            noise_mask = (freqs >= noise_low) & (freqs <= noise_high)
                            # Exclude signal frequencies
                            signal_mask = np.abs(freqs - freq) > 0.5
                            combined_mask = noise_mask & signal_mask
                            
                            noise_power += np.mean(psd[combined_mask])
                
                # Calculate SNR
                if noise_power > 0:
                    snr = 10 * np.log10(signal_power / noise_power)
                else:
                    snr = 0.0
                
                snr_values[f"{target_freq}Hz"] = snr
            
            return snr_values
            
        except Exception as e:
            logger.error(f"Error detecting SSVEP: {e}")
            return {}
    
    def classify_ssvep_command(self, snr_values: dict[str, float], threshold: float = 3.0) -> str | None:
        """Classify SSVEP command"""
        try:
            # Find frequency with highest SNR above threshold
            best_freq = None
            best_snr = threshold
            
            for freq_str, snr in snr_values.items():
                if snr > best_snr:
                    best_snr = snr
                    best_freq = freq_str
            
            if best_freq:
                # Map frequency to command
                freq_mapping = {
                    "6.0Hz": "command_1",
                    "7.0Hz": "command_2",
                    "8.0Hz": "command_3",
                    "9.0Hz": "command_4",
                    "10.0Hz": "command_5"
                }
                return freq_mapping.get(best_freq)
            
            return None
            
        except Exception as e:
            logger.error(f"Error classifying SSVEP command: {e}")
            return None

class P300Detector:
    """P300 event-related potential detector"""
    
    def __init__(self, sampling_rate: float = 250.0):
        self.sampling_rate = sampling_rate
        self.p300_window = (0.3, 0.8)  # P300 window in seconds
        self.baseline_window = (0.0, 0.1)  # Baseline window
        
    def detect_p300(self, eeg_data: np.ndarray, event_times: list[float]) -> dict[str, float]:
        """Detect P300 responses"""
        try:
            p300_amplitudes = []
            
            for event_time in event_times:
                # Extract P300 window
                start_sample = int(event_time * self.sampling_rate)
                end_sample = int((event_time + self.p300_window[1]) * self.sampling_rate)
                
                if end_sample < len(eeg_data):
                    p300_window = eeg_data[start_sample:end_sample]
                    
                    # Extract baseline
                    baseline_start = int(event_time * self.sampling_rate)
                    baseline_end = int((event_time + self.baseline_window[1]) * self.sampling_rate)
                    
                    if baseline_end < len(eeg_data):
                        baseline = eeg_data[baseline_start:baseline_end]
                        baseline_mean = np.mean(baseline)
                        
                        # Calculate P300 amplitude (peak in window)
                        p300_peak = np.max(p300_window) - baseline_mean
                        p300_amplitudes.append(p300_peak)
            
            if p300_amplitudes:
                return {
                    "mean_amplitude": np.mean(p300_amplitudes),
                    "std_amplitude": np.std(p300_amplitudes),
                    "max_amplitude": np.max(p300_amplitudes),
                    "num_responses": len(p300_amplitudes)
                }
            
            return {"mean_amplitude": 0.0, "std_amplitude": 0.0, "max_amplitude": 0.0, "num_responses": 0}
            
        except Exception as e:
            logger.error(f"Error detecting P300: {e}")
            return {"mean_amplitude": 0.0, "std_amplitude": 0.0, "max_amplitude": 0.0, "num_responses": 0}
    
    def classify_p300_target(self, p300_data: dict[str, float], threshold: float = 2.0) -> bool:
        """Classify if P300 response indicates target"""
        try:
            mean_amp = p300_data.get("mean_amplitude", 0.0)
            std_amp = p300_data.get("std_amplitude", 0.0)
            
            # Simple threshold classification
            if std_amp > 0:
                z_score = mean_amp / std_amp
                return z_score > threshold
            
            return mean_amp > threshold
            
        except Exception as e:
            logger.error(f"Error classifying P300 target: {e}")
            return False

class BrainComputerInterface:
    """Main Brain-Computer Interface system"""
    
    def __init__(self):
        self.devices: dict[str, BCIDevice] = {}
        self.users: dict[str, BCIUser] = {}
        self.signals: dict[str, BrainSignal] = []
        self.commands: list[BCICommand] = []
        
        # Initialize processors
        self.eeg_processor = EEGProcessor()
        self.motor_imagery_classifier = MotorImageryClassifier()
        self.ssvep_detector = SSVEPDetecter()
        self.p300_detector = P300Detector()
        
        # Initialize device
        self._initialize_default_device()
        
        # Start background tasks
        asyncio.create_task(self._signal_processing_loop())
        asyncio.create_task(self._command_generation_loop())
        asyncio.create_task(self._performance_monitoring())
    
    def _initialize_default_device(self):
        """Initialize default BCI device"""
        try:
            # Create electrodes (64-channel EEG cap)
            electrodes = []
            for i in range(64):
                electrode = Electrode(
                    id=f"electrode_{i}",
                    name=f"E{i+1}",
                    position=self._get_electrode_position(i),
                    impedance=np.random.uniform(5.0, 15.0),  # kΩ
                    signal_quality=np.random.uniform(0.8, 1.0),
                    is_active=True,
                    last_calibration=datetime.now()
                )
                electrodes.append(electrode)
            
            # Create device
            device = BCIDevice(
                id="default_eeg_device",
                name="Default EEG Device",
                bci_type=BCIType.EEG,
                electrodes=electrodes,
                sampling_rate=250.0,
                bandwidth=(0.5, 100.0),
                noise_level=0.1,
                is_connected=True,
                calibration_status="calibrated",
                firmware_version="1.0.0"
            )
            
            self.devices[device.id] = device
            logger.info("Initialized default BCI device")
            
        except Exception as e:
            logger.error(f"Error initializing default device: {e}")
    
    def _get_electrode_position(self, index: int) -> tuple[float, float, float]:
        """Get 3D position for electrode (simplified 10-20 system)"""
        # Simplified electrode positioning
        # In practice, would use actual 10-20 system coordinates
        theta = 2 * np.pi * index / 64
        x = np.cos(theta)
        y = np.sin(theta)
        z = 0.0
        
        return (x, y, z)
    
    async def register_user(self, user_data: dict[str, Any]) -> BCIUser:
        """Register new BCI user"""
        try:
            user = BCIUser(
                id=str(uuid.uuid4()),
                name=user_data["name"],
                age=user_data.get("age", 25),
                gender=user_data.get("gender", "other"),
                medical_history=user_data.get("medical_history", {}),
                calibration_data={},
                performance_metrics={},
                preferences=user_data.get("preferences", {}),
                created_at=datetime.now(),
                last_session=datetime.now()
            )
            
            self.users[user.id] = user
            
            logger.info(f"Registered BCI user: {user.id}")
            return user
            
        except Exception as e:
            logger.error(f"Error registering user: {e}")
            raise
    
    async def calibrate_user(self, user_id: str, calibration_type: str) -> bool:
        """Calibrate user for specific BCI task"""
        try:
            user = self.users.get(user_id)
            if not user:
                return False
            
            if calibration_type == "motor_imagery":
                # Simulate motor imagery calibration
                training_data = self._generate_motor_imagery_training_data()
                success = self.motor_imagery_classifier.train_csp(training_data)
                
                if success:
                    user.calibration_data["motor_imagery"] = {
                        "calibrated": True,
                        "date": datetime.now().isoformat(),
                        "accuracy": 0.85
                    }
            
            elif calibration_type == "ssvep":
                # Simulate SSVEP calibration
                user.calibration_data["ssvep"] = {
                    "calibrated": True,
                    "date": datetime.now().isoformat(),
                    "target_frequencies": self.ssvep_detector.target_frequencies
                }
            
            elif calibration_type == "p300":
                # Simulate P300 calibration
                user.calibration_data["p300"] = {
                    "calibrated": True,
                    "date": datetime.now().isoformat(),
                    "threshold": 2.0
                }
            
            user.last_session = datetime.now()
            
            logger.info(f"Calibrated user {user_id} for {calibration_type}")
            return True
            
        except Exception as e:
            logger.error(f"Error calibrating user: {e}")
            return False
    
    def _generate_motor_imagery_training_data(self) -> dict[str, np.ndarray]:
        """Generate simulated motor imagery training data"""
        try:
            # Simulate training data for left and right motor imagery
            num_trials = 100
            num_channels = 64
            samples_per_trial = 1000
            
            training_data = {}
            
            # Left motor imagery
            left_data = []
            for _ in range(num_trials):
                # Generate synthetic EEG with mu rhythm suppression
                trial = self._generate_mu_rhythm_suppressed(samples_per_trial, num_channels)
                left_data.append(trial)
            
            training_data["left"] = np.array(left_data)
            
            # Right motor imagery
            right_data = []
            for _ in range(num_trials):
                # Generate synthetic EEG with mu rhythm suppression
                trial = self._generate_mu_rhythm_suppressed(samples_per_trial, num_channels)
                right_data.append(trial)
            
            training_data["right"] = np.array(right_data)
            
            return training_data
            
        except Exception as e:
            logger.error(f"Error generating training data: {e}")
            return {}
    
    def _generate_mu_rhythm_suppressed(self, samples: int, channels: int) -> np.ndarray:
        """Generate synthetic EEG with mu rhythm suppression"""
        try:
            # Generate baseline EEG
            eeg = np.random.randn(channels, samples)
            
            # Add mu rhythm (8-13 Hz)
            t = np.arange(samples) / 250.0  # Time vector
            mu_freq = 10.0  # Hz
            
            for ch in range(channels):
                # Add mu rhythm with some suppression
                amplitude = np.random.uniform(0.5, 2.0)
                phase = np.random.uniform(0, 2*np.pi)
                mu_rhythm = amplitude * np.sin(2 * np.pi * mu_freq * t + phase)
                
                # Add suppression effect
                suppression = np.random.uniform(0.3, 0.7)
                eeg[ch] += mu_rhythm * suppression
            
            return eeg
            
        except Exception as e:
            logger.error(f"Error generating mu rhythm: {e}")
            return np.random.randn(channels, samples)
    
    async def process_brain_signal(self, device_id: str, raw_data: np.ndarray) -> BrainSignal:
        """Process raw brain signal"""
        try:
            device = self.devices.get(device_id)
            if not device:
                raise ValueError(f"Device {device_id} not found")
            
            # Preprocess signal
            processed_data = np.zeros_like(raw_data)
            for ch in range(raw_data.shape[0]):
                processed_data[ch] = self.eeg_processor.preprocess_signal(raw_data[ch])
            
            # Create brain signal object
            signal = BrainSignal(
                id=str(uuid.uuid4()),
                signal_type=SignalType.MU,  # Default signal type
                channel_data=processed_data,
                sampling_rate=device.sampling_rate,
                timestamp=datetime.now(),
                duration=processed_data.shape[1] / device.sampling_rate,
                quality_score=self._calculate_signal_quality(processed_data),
                metadata={
                    "device_id": device_id,
                    "num_channels": processed_data.shape[0],
                    "num_samples": processed_data.shape[1]
                }
            )
            
            self.signals.append(signal)
            
            logger.info(f"Processed brain signal: {signal.id}")
            return signal
            
        except Exception as e:
            logger.error(f"Error processing brain signal: {e}")
            raise
    
    def _calculate_signal_quality(self, signal: np.ndarray) -> float:
        """Calculate signal quality score"""
        try:
            # Simple quality metric based on variance and line noise
            quality = 1.0
            
            # Check for excessive variance (noise)
            variance = np.var(signal)
            if variance > 100.0:
                quality *= 0.8
            
            # Check for flat signals (no brain activity)
            if variance < 0.01:
                quality *= 0.5
            
            # Check for saturation
            max_amplitude = np.max(np.abs(signal))
            if max_amplitude > 100.0:  # Assuming μV scale
                quality *= 0.7
            
            return max(0.0, min(1.0, quality))
            
        except Exception as e:
            logger.error(f"Error calculating signal quality: {e}")
            return 0.5
    
    async def generate_command(self, user_id: str, signal: BrainSignal, 
                              command_type: CommandType) -> BCICommand | None:
        """Generate BCI command from brain signal"""
        try:
            user = self.users.get(user_id)
            if not user:
                return None
            
            command = None
            confidence = 0.0
            intent = None
            parameters = {}
            
            if command_type == CommandType.MOTOR_IMAGERY:
                # Motor imagery classification
                classification = self.motor_imagery_classifier.classify_motor_imagery(signal.channel_data)
                
                if classification["left"] > 0.7:
                    intent = IntentType.MOVE_LEFT
                    confidence = classification["left"]
                elif classification["right"] > 0.7:
                    intent = IntentType.MOVE_RIGHT
                    confidence = classification["right"]
                
                parameters = {"classification": classification}
            
            elif command_type == CommandType.SSVEP_CONTROL:
                # SSVEP detection
                snr_values = self.ssvep_detector.detect_ssvep(signal.channel_data, signal.duration)
                command_str = self.ssvep_detector.classify_ssvep_command(snr_values)
                
                if command_str:
                    intent = IntentType.SELECT  # Default SSVEP intent
                    confidence = max(snr_values.values()) / 10.0  # Normalize
                    parameters = {"ssvep_command": command_str, "snr_values": snr_values}
            
            elif command_type == CommandType.P300_SPELLING:
                # P300 detection (simplified - would need event timing)
                p300_data = self.p300_detector.detect_p300(signal.channel_data, [0.5, 1.0])
                is_target = self.p300_detector.classify_p300_target(p300_data)
                
                if is_target:
                    intent = IntentType.SELECT
                    confidence = min(1.0, p300_data["mean_amplitude"] / 5.0)
                    parameters = {"p300_data": p300_data}
            
            if intent and confidence > 0.5:
                command = BCICommand(
                    id=str(uuid.uuid4()),
                    command_type=command_type,
                    intent=intent,
                    confidence=confidence,
                    parameters=parameters,
                    timestamp=datetime.now(),
                    user_id=user_id,
                    device_id="default_eeg_device"
                )
                
                self.commands.append(command)
                
                # Update user performance metrics
                self._update_user_performance(user_id, command)
                
                logger.info(f"Generated BCI command: {intent.value} (confidence: {confidence:.2f})")
            
            return command
            
        except Exception as e:
            logger.error(f"Error generating command: {e}")
            return None
    
    def _update_user_performance(self, user_id: str, command: BCICommand):
        """Update user performance metrics"""
        try:
            user = self.users.get(user_id)
            if not user:
                return
            
            # Update performance metrics
            if "command_accuracy" not in user.performance_metrics:
                user.performance_metrics["command_accuracy"] = []
            
            user.performance_metrics["command_accuracy"].append(command.confidence)
            
            # Keep only last 100 commands
            if len(user.performance_metrics["command_accuracy"]) > 100:
                user.performance_metrics["command_accuracy"] = user.performance_metrics["command_accuracy"][-100:]
            
            # Calculate average accuracy
            avg_accuracy = np.mean(user.performance_metrics["command_accuracy"])
            user.performance_metrics["average_accuracy"] = avg_accuracy
            
        except Exception as e:
            logger.error(f"Error updating user performance: {e}")
    
    async def _signal_processing_loop(self):
        """Background signal processing loop"""
        while True:
            try:
                # Simulate signal acquisition
                device = self.devices.get("default_eeg_device")
                if device and device.is_connected:
                    # Generate synthetic EEG data
                    num_channels = len(device.electrodes)
                    samples = 1000  # 4 seconds at 250 Hz
                    
                    raw_data = np.random.randn(num_channels, samples)
                    
                    # Add some brain-like signals
                    t = np.arange(samples) / device.sampling_rate
                    for ch in range(num_channels):
                        # Add alpha rhythm (8-13 Hz)
                        alpha_freq = np.random.uniform(8, 13)
                        alpha_amp = np.random.uniform(0.5, 2.0)
                        alpha_phase = np.random.uniform(0, 2*np.pi)
                        raw_data[ch] += alpha_amp * np.sin(2 * np.pi * alpha_freq * t + alpha_phase)
                    
                    # Process signal
                    await self.process_brain_signal(device.id, raw_data)
                
                # Wait before next processing
                await asyncio.sleep(1.0)  # Process every second
                
            except Exception as e:
                logger.error(f"Error in signal processing loop: {e}")
                await asyncio.sleep(5)
    
    async def _command_generation_loop(self):
        """Background command generation loop"""
        while True:
            try:
                # Get latest signal
                if self.signals:
                    latest_signal = self.signals[-1]
                    
                    # Try to generate commands for each user
                    for user_id in self.users.keys():
                        # Try different command types
                        for command_type in [CommandType.MOTOR_IMAGERY, CommandType.SSVEP_CONTROL]:
                            command = await self.generate_command(user_id, latest_signal, command_type)
                            if command:
                                break  # Generate at most one command per signal per user
                
                # Wait before next command generation
                await asyncio.sleep(0.5)  # Check every 500ms
                
            except Exception as e:
                logger.error(f"Error in command generation loop: {e}")
                await asyncio.sleep(2)
    
    async def _performance_monitoring(self):
        """Background performance monitoring"""
        while True:
            try:
                # Collect performance metrics
                metrics = {
                    "total_users": len(self.users),
                    "total_devices": len(self.devices),
                    "total_signals": len(self.signals),
                    "total_commands": len(self.commands),
                    "active_devices": len([d for d in self.devices.values() if d.is_connected]),
                    "average_signal_quality": 0.0,
                    "average_command_confidence": 0.0,
                    "timestamp": datetime.now().isoformat()
                }
                
                # Calculate averages
                if self.signals:
                    metrics["average_signal_quality"] = np.mean([s.quality_score for s in self.signals[-100:]])
                
                if self.commands:
                    metrics["average_command_confidence"] = np.mean([c.confidence for c in self.commands[-100:]])
                
                # Log metrics
                logger.info(f"BCI performance metrics: {metrics}")
                
                # Wait before next monitoring
                await asyncio.sleep(60)  # Monitor every minute
                
            except Exception as e:
                logger.error(f"Error in performance monitoring: {e}")
                await asyncio.sleep(10)
    
    def get_user_info(self, user_id: str) -> dict[str, Any]:
        """Get user information"""
        try:
            user = self.users.get(user_id)
            if not user:
                return {"error": "User not found"}
            
            return {
                "id": user.id,
                "name": user.name,
                "age": user.age,
                "gender": user.gender,
                "calibration_data": user.calibration_data,
                "performance_metrics": user.performance_metrics,
                "created_at": user.created_at.isoformat(),
                "last_session": user.last_session.isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting user info: {e}")
            return {"error": str(e)}
    
    def get_device_info(self, device_id: str) -> dict[str, Any]:
        """Get device information"""
        try:
            device = self.devices.get(device_id)
            if not device:
                return {"error": "Device not found"}
            
            return {
                "id": device.id,
                "name": device.name,
                "bci_type": device.bci_type.value,
                "num_electrodes": len(device.electrodes),
                "sampling_rate": device.sampling_rate,
                "bandwidth": device.bandwidth,
                "is_connected": device.is_connected,
                "calibration_status": device.calibration_status,
                "firmware_version": device.firmware_version
            }
            
        except Exception as e:
            logger.error(f"Error getting device info: {e}")
            return {"error": str(e)}
    
    def get_recent_commands(self, user_id: str, limit: int = 10) -> list[dict[str, Any]]:
        """Get recent commands for user"""
        try:
            user_commands = [cmd for cmd in self.commands if cmd.user_id == user_id]
            user_commands.sort(key=lambda x: x.timestamp, reverse=True)
            
            recent_commands = []
            for cmd in user_commands[:limit]:
                recent_commands.append({
                    "id": cmd.id,
                    "command_type": cmd.command_type.value,
                    "intent": cmd.intent.value,
                    "confidence": cmd.confidence,
                    "timestamp": cmd.timestamp.isoformat(),
                    "parameters": cmd.parameters
                })
            
            return recent_commands
            
        except Exception as e:
            logger.error(f"Error getting recent commands: {e}")
            return []

# Global BCI manager
bci_manager = BrainComputerInterface()

# API endpoints
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter(prefix="/bci", tags=["brain_computer_interface"])

class UserRegistrationRequest(BaseModel):
    name: str
    age: int = 25
    gender: str = "other"
    medical_history: dict[str, Any] = {}
    preferences: dict[str, Any] = {}

class CalibrationRequest(BaseModel):
    user_id: str
    calibration_type: str

@router.post("/users/register")
async def register_user(request: UserRegistrationRequest):
    """Register BCI user"""
    try:
        user = await bci_manager.register_user({
            "name": request.name,
            "age": request.age,
            "gender": request.gender,
            "medical_history": request.medical_history,
            "preferences": request.preferences
        })
        
        return asdict(user)
    except Exception as e:
        logger.error(f"Error registering user: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/users/{user_id}/calibrate")
async def calibrate_user(user_id: str, request: CalibrationRequest):
    """Calibrate user for BCI task"""
    try:
        success = await bci_manager.calibrate_user(user_id, request.calibration_type)
        return {"success": success, "user_id": user_id, "calibration_type": request.calibration_type}
    except Exception as e:
        logger.error(f"Error calibrating user: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/signals/process")
async def process_signal(device_id: str):
    """Process brain signal (simulated)"""
    try:
        # Generate synthetic signal for demonstration
        device = bci_manager.devices.get(device_id)
        if not device:
            raise HTTPException(status_code=404, detail="Device not found")
        
        num_channels = len(device.electrodes)
        samples = 1000
        raw_data = np.random.randn(num_channels, samples)
        
        signal = await bci_manager.process_brain_signal(device_id, raw_data)
        
        return {
            "signal_id": signal.id,
            "signal_type": signal.signal_type.value,
            "quality_score": signal.quality_score,
            "duration": signal.duration,
            "timestamp": signal.timestamp.isoformat()
        }
    except Exception as e:
        logger.error(f"Error processing signal: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/commands/generate")
async def generate_command(user_id: str, signal_id: str, command_type: str):
    """Generate BCI command from signal"""
    try:
        # Find signal
        signal = None
        for s in bci_manager.signals:
            if s.id == signal_id:
                signal = s
                break
        
        if not signal:
            raise HTTPException(status_code=404, detail="Signal not found")
        
        cmd_type = CommandType(command_type)
        command = await bci_manager.generate_command(user_id, signal, cmd_type)
        
        if command:
            return asdict(command)
        else:
            return {"message": "No command generated (confidence too low)"}
    except Exception as e:
        logger.error(f"Error generating command: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/users/{user_id}")
async def get_user_info(user_id: str):
    """Get user information"""
    try:
        info = bci_manager.get_user_info(user_id)
        return info
    except Exception as e:
        logger.error(f"Error getting user info: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/devices/{device_id}")
async def get_device_info(device_id: str):
    """Get device information"""
    try:
        info = bci_manager.get_device_info(device_id)
        return info
    except Exception as e:
        logger.error(f"Error getting device info: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/users/{user_id}/commands")
async def get_recent_commands(user_id: str, limit: int = 10):
    """Get recent commands for user"""
    try:
        commands = bci_manager.get_recent_commands(user_id, limit)
        return {"commands": commands}
    except Exception as e:
        logger.error(f"Error getting recent commands: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/devices")
async def list_devices():
    """List BCI devices"""
    try:
        devices = []
        for device in bci_manager.devices.values():
            devices.append({
                "id": device.id,
                "name": device.name,
                "bci_type": device.bci_type.value,
                "is_connected": device.is_connected,
                "num_electrodes": len(device.electrodes)
            })
        
        return {"devices": devices}
    except Exception as e:
        logger.error(f"Error listing devices: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/users")
async def list_users():
    """List BCI users"""
    try:
        users = []
        for user in bci_manager.users.values():
            users.append({
                "id": user.id,
                "name": user.name,
                "age": user.age,
                "created_at": user.created_at.isoformat(),
                "last_session": user.last_session.isoformat()
            })
        
        return {"users": users}
    except Exception as e:
        logger.error(f"Error listing users: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/command-types")
async def list_command_types():
    """List supported command types"""
    try:
        types = [ctype.value for ctype in CommandType]
        return {"command_types": types}
    except Exception as e:
        logger.error(f"Error listing command types: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/bci-types")
async def list_bci_types():
    """List supported BCI types"""
    try:
        types = [btype.value for btype in BCIType]
        return {"bci_types": types}
    except Exception as e:
        logger.error(f"Error listing BCI types: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/status")
async def get_bci_status():
    """Get BCI system status"""
    try:
        return {
            "total_users": len(bci_manager.users),
            "total_devices": len(bci_manager.devices),
            "total_signals": len(bci_manager.signals),
            "total_commands": len(bci_manager.commands),
            "active_devices": len([d for d in bci_manager.devices.values() if d.is_connected]),
            "supported_bci_types": len(BCIType),
            "supported_command_types": len(CommandType)
        }
    except Exception as e:
        logger.error(f"Error getting BCI status: {e}")
        raise HTTPException(status_code=500, detail=str(e))
