"""
Edge-AI simulation for onboard detection and processing
"""
import asyncio
import numpy as np
from typing import List, Dict, Optional, Any
from uuid import UUID, uuid4
from datetime import datetime
import random

from models import (
    AIModelConfig, DetectionResult, CameraFrame,
    Position3D
)


class EdgeAISimulator:
    """
    Simulates edge-AI processing onboard drone:
    - Object detection
    - Segmentation
    - Classification
    - Configurable performance characteristics
    - Resource constraints simulation
    """

    def __init__(self, model_config: AIModelConfig):
        self.config = model_config

        # Resource usage tracking
        self.current_cpu_usage = 0.0
        self.current_memory_mb = 0.0
        self.current_gpu_usage = 0.0

        # Performance tracking
        self.frames_processed = 0
        self.total_inference_time = 0.0
        self.last_inference_time = 0.0

        # Detection database (for consistent detections)
        self.known_objects: List[Dict] = []

        # Throttling
        self.last_process_time = 0.0
        self.min_frame_interval = 1.0 / self.config.max_fps

    async def process_frame(
        self,
        frame: CameraFrame,
        drone_id: UUID,
        timestamp: float
    ) -> List[DetectionResult]:
        """
        Process a camera frame and return detections

        Args:
            frame: Camera frame to process
            drone_id: Drone ID
            timestamp: Current simulation time

        Returns:
            List of detection results
        """
        # Check throttling
        time_since_last = timestamp - self.last_process_time
        if time_since_last < self.min_frame_interval:
            return []  # Skip frame due to throttling

        self.last_process_time = timestamp

        # Simulate resource usage
        self._update_resource_usage()

        # Check if resources are overloaded
        if self.current_cpu_usage > 95 and self.config.enable_throttling:
            # Skip frame due to overload
            return []

        # Simulate inference time
        inference_time = self._simulate_inference_time()
        await asyncio.sleep(inference_time / 1000.0)  # Convert ms to seconds

        # Generate detections
        detections = self._generate_detections(frame, drone_id)

        # Update statistics
        self.frames_processed += 1
        self.total_inference_time += inference_time
        self.last_inference_time = inference_time

        return detections

    def _generate_detections(
        self,
        frame: CameraFrame,
        drone_id: UUID
    ) -> List[DetectionResult]:
        """Generate realistic detections for the frame"""
        detections = []

        # Number of objects to detect (based on scene complexity)
        num_objects = np.random.poisson(2)  # Average 2 objects per frame

        for _ in range(num_objects):
            # Select random class
            class_name = random.choice(self.config.classes)

            # Generate confidence (with configurable accuracy)
            if random.random() > self.config.false_negative_rate:
                # True positive
                confidence = self._generate_confidence(is_true_positive=True)

                # Generate bounding box
                bbox = self._generate_bounding_box(frame.width, frame.height)

                detection = DetectionResult(
                    detection_id=uuid4(),
                    drone_id=drone_id,
                    timestamp=datetime.utcnow(),
                    class_name=class_name,
                    confidence=confidence,
                    bounding_box=bbox,
                    image_id=str(frame.frame_id),
                    position={
                        'latitude': frame.latitude,
                        'longitude': frame.longitude
                    },
                    altitude=frame.altitude,
                    model_name=self.config.model_name,
                    model_version=self.config.model_version,
                    inference_time_ms=self.last_inference_time
                )
                detections.append(detection)

        # Add false positives
        if random.random() < self.config.false_positive_rate:
            class_name = random.choice(self.config.classes)
            confidence = self._generate_confidence(is_true_positive=False)
            bbox = self._generate_bounding_box(frame.width, frame.height)

            detection = DetectionResult(
                detection_id=uuid4(),
                drone_id=drone_id,
                timestamp=datetime.utcnow(),
                class_name=class_name,
                confidence=confidence,
                bounding_box=bbox,
                image_id=str(frame.frame_id),
                position={
                    'latitude': frame.latitude,
                    'longitude': frame.longitude
                },
                altitude=frame.altitude,
                model_name=self.config.model_name,
                model_version=self.config.model_version,
                inference_time_ms=self.last_inference_time,
                metadata={'false_positive': True}
            )
            detections.append(detection)

        return detections

    def _generate_confidence(self, is_true_positive: bool) -> float:
        """Generate detection confidence score"""
        if is_true_positive:
            # True positives have high confidence (above threshold)
            mean = 0.8
            std = 0.1
        else:
            # False positives have lower confidence (around threshold)
            mean = self.config.confidence_threshold + 0.05
            std = 0.15

        confidence = np.random.normal(mean, std)
        return np.clip(confidence, 0.0, 1.0)

    def _generate_bounding_box(self, width: int, height: int) -> Dict[str, float]:
        """Generate random bounding box"""
        # Random position and size
        x_center = random.uniform(0.2, 0.8)
        y_center = random.uniform(0.2, 0.8)
        box_width = random.uniform(0.05, 0.3)
        box_height = random.uniform(0.05, 0.3)

        return {
            'x': x_center * width,
            'y': y_center * height,
            'width': box_width * width,
            'height': box_height * height
        }

    def _simulate_inference_time(self) -> float:
        """Simulate inference time with variation"""
        # Base inference time with some variation
        base_time = self.config.inference_time_ms
        variation = base_time * 0.2  # 20% variation

        inference_time = np.random.normal(base_time, variation)
        return max(10, inference_time)  # Minimum 10ms

    def _update_resource_usage(self):
        """Update simulated resource usage"""
        # CPU usage varies around configured value
        target_cpu = self.config.cpu_usage
        self.current_cpu_usage += (target_cpu - self.current_cpu_usage) * 0.3
        self.current_cpu_usage += np.random.randn() * 5.0
        self.current_cpu_usage = np.clip(self.current_cpu_usage, 0, 100)

        # Memory usage is relatively stable
        target_memory = self.config.memory_mb
        self.current_memory_mb += (target_memory - self.current_memory_mb) * 0.1
        self.current_memory_mb += np.random.randn() * 10.0
        self.current_memory_mb = max(0, self.current_memory_mb)

        # GPU usage (if available)
        if self.config.gpu_usage is not None:
            target_gpu = self.config.gpu_usage
            self.current_gpu_usage += (target_gpu - self.current_gpu_usage) * 0.3
            self.current_gpu_usage += np.random.randn() * 5.0
            self.current_gpu_usage = np.clip(self.current_gpu_usage, 0, 100)

    def get_statistics(self) -> Dict[str, Any]:
        """Get AI processing statistics"""
        avg_inference_time = 0.0
        if self.frames_processed > 0:
            avg_inference_time = self.total_inference_time / self.frames_processed

        return {
            'model_name': self.config.model_name,
            'model_version': self.config.model_version,
            'frames_processed': self.frames_processed,
            'avg_inference_time_ms': avg_inference_time,
            'last_inference_time_ms': self.last_inference_time,
            'cpu_usage': self.current_cpu_usage,
            'memory_mb': self.current_memory_mb,
            'gpu_usage': self.current_gpu_usage,
            'fps': self.frames_processed / (self.total_inference_time / 1000.0) if self.total_inference_time > 0 else 0
        }

    def reset_statistics(self):
        """Reset processing statistics"""
        self.frames_processed = 0
        self.total_inference_time = 0.0


class EdgeAIManager:
    """Manages edge-AI simulators for multiple drones"""

    def __init__(self):
        self.simulators: Dict[UUID, EdgeAISimulator] = {}
        self.default_configs: Dict[str, AIModelConfig] = {}

        # Register default models
        self._register_default_models()

    def _register_default_models(self):
        """Register default AI models"""
        # Crack detection model
        self.default_configs['crack_detector'] = AIModelConfig(
            model_name='crack_detector',
            model_version='1.0.0',
            model_type='detection',
            framework='pytorch',
            inference_time_ms=150.0,
            cpu_usage=60.0,
            memory_mb=600.0,
            confidence_threshold=0.6,
            false_positive_rate=0.08,
            false_negative_rate=0.12,
            classes=['crack', 'spall', 'corrosion', 'delamination'],
            max_fps=10.0
        )

        # PPE detection model
        self.default_configs['ppe_detector'] = AIModelConfig(
            model_name='ppe_detector',
            model_version='1.0.0',
            model_type='detection',
            framework='onnx',
            inference_time_ms=80.0,
            cpu_usage=45.0,
            memory_mb=400.0,
            confidence_threshold=0.7,
            false_positive_rate=0.05,
            false_negative_rate=0.10,
            classes=['person', 'hardhat', 'safety_vest', 'no_ppe'],
            max_fps=15.0
        )

        # Generic object detector
        self.default_configs['object_detector'] = AIModelConfig(
            model_name='object_detector',
            model_version='1.0.0',
            model_type='detection',
            framework='pytorch',
            inference_time_ms=100.0,
            cpu_usage=50.0,
            memory_mb=500.0,
            confidence_threshold=0.5,
            false_positive_rate=0.10,
            false_negative_rate=0.15,
            classes=['person', 'vehicle', 'obstacle', 'animal'],
            max_fps=20.0
        )

    def create_simulator(
        self,
        drone_id: UUID,
        model_name: str = 'crack_detector',
        custom_config: Optional[AIModelConfig] = None
    ) -> EdgeAISimulator:
        """Create an edge-AI simulator for a drone"""
        if custom_config:
            config = custom_config
        elif model_name in self.default_configs:
            config = self.default_configs[model_name]
        else:
            raise ValueError(f"Unknown model: {model_name}")

        simulator = EdgeAISimulator(config)
        self.simulators[drone_id] = simulator
        return simulator

    def get_simulator(self, drone_id: UUID) -> Optional[EdgeAISimulator]:
        """Get edge-AI simulator for a drone"""
        return self.simulators.get(drone_id)

    def remove_simulator(self, drone_id: UUID):
        """Remove edge-AI simulator for a drone"""
        if drone_id in self.simulators:
            del self.simulators[drone_id]

    def get_all_statistics(self) -> Dict[UUID, Dict[str, Any]]:
        """Get statistics for all simulators"""
        return {
            drone_id: simulator.get_statistics()
            for drone_id, simulator in self.simulators.items()
        }


# Singleton instance
_edge_ai_manager: Optional[EdgeAIManager] = None


def get_edge_ai_manager() -> EdgeAIManager:
    """Get global edge-AI manager instance"""
    global _edge_ai_manager
    if _edge_ai_manager is None:
        _edge_ai_manager = EdgeAIManager()
    return _edge_ai_manager
