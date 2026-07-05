"""GPU hardware abstraction layer for OpenCV operations."""

import cv2
import numpy as np
from enum import Enum
from services.logger import logger_service

class ProcessingBackend(Enum):
    AUTO = "auto"
    CUDA = "cuda"
    OPENCL = "opencl"
    CPU = "cpu"

class GPUManager:
    """Manages OpenCV hardware acceleration."""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if hasattr(self, "_initialized"):
            return
            
        self._initialized = True
        self.logger = logger_service.get_logger("gpu_manager")
        
        self.has_cuda = False
        self.has_opencl = False
        
        # Check CUDA
        try:
            if hasattr(cv2, 'cuda') and cv2.cuda.getCudaEnabledDeviceCount() > 0:
                self.has_cuda = True
                self.logger.info(f"NVIDIA CUDA Detected. Devices: {cv2.cuda.getCudaEnabledDeviceCount()}")
        except Exception:
            pass
            
        # Check OpenCL
        try:
            if cv2.ocl.haveOpenCL():
                self.has_opencl = True
                cv2.ocl.setUseOpenCL(True)
                self.logger.info("OpenCL Detected and Enabled.")
        except Exception:
            pass
            
        self.active_backend = ProcessingBackend.AUTO
        self.resolved_backend = self._resolve_backend(ProcessingBackend.AUTO)
        self.logger.info(f"Resolved default backend to: {self.resolved_backend.value.upper()}")
        
    def _resolve_backend(self, desired: ProcessingBackend) -> ProcessingBackend:
        """Resolve requested backend against available hardware."""
        if desired == ProcessingBackend.AUTO:
            if self.has_cuda:
                return ProcessingBackend.CUDA
            elif self.has_opencl:
                return ProcessingBackend.OPENCL
            return ProcessingBackend.CPU
            
        if desired == ProcessingBackend.CUDA:
            return ProcessingBackend.CUDA if self.has_cuda else self._resolve_backend(ProcessingBackend.AUTO)
            
        if desired == ProcessingBackend.OPENCL:
            return ProcessingBackend.OPENCL if self.has_opencl else ProcessingBackend.CPU
            
        return ProcessingBackend.CPU
        
    def set_backend(self, backend_str: str) -> bool:
        """Set processing backend."""
        try:
            desired = ProcessingBackend(backend_str.lower())
            resolved = self._resolve_backend(desired)
            
            if resolved != self.resolved_backend:
                self.resolved_backend = resolved
                self.active_backend = desired
                self.logger.info(f"Backend switched to: {resolved.value.upper()}")
                
                # Manage OpenCL global state
                if resolved == ProcessingBackend.OPENCL:
                    cv2.ocl.setUseOpenCL(True)
                else:
                    cv2.ocl.setUseOpenCL(False)
                    
                return True
            return False
        except ValueError:
            self.logger.error(f"Invalid backend requested: {backend_str}")
            return False
            
    def get_status(self) -> dict:
        return {
            "has_cuda": self.has_cuda,
            "has_opencl": self.has_opencl,
            "active_backend": self.active_backend.value,
            "resolved_backend": self.resolved_backend.value
        }
        
    # --- Acceleration Wrappers ---
    # These wrap standard OpenCV operations dynamically.
    
    def resize(self, frame: np.ndarray, size: tuple, interpolation=cv2.INTER_LINEAR) -> np.ndarray:
        if self.resolved_backend == ProcessingBackend.CUDA:
            try:
                gpu_frame = cv2.cuda_GpuMat()
                gpu_frame.upload(frame)
                gpu_resized = cv2.cuda.resize(gpu_frame, size, interpolation=interpolation)
                return gpu_resized.download()
            except Exception as e:
                self.logger.debug(f"CUDA resize failed: {e}")
                
        elif self.resolved_backend == ProcessingBackend.OPENCL:
            umat = cv2.UMat(frame)
            return cv2.resize(umat, size, interpolation=interpolation).get()
            
        return cv2.resize(frame, size, interpolation=interpolation)
        
    def cvtColor(self, frame: np.ndarray, code) -> np.ndarray:
        if self.resolved_backend == ProcessingBackend.CUDA:
            try:
                gpu_frame = cv2.cuda_GpuMat()
                gpu_frame.upload(frame)
                gpu_cvt = cv2.cuda.cvtColor(gpu_frame, code)
                return gpu_cvt.download()
            except Exception:
                pass
                
        elif self.resolved_backend == ProcessingBackend.OPENCL:
            return cv2.cvtColor(cv2.UMat(frame), code).get()
            
        return cv2.cvtColor(frame, code)

gpu_manager = GPUManager()
