"""
ViSNET AI Platform Integration
Provides hooks for uploading images, detections, and work orders
"""
import httpx
from typing import Optional, Dict, Any, List
from datetime import datetime
import asyncio

from config import settings
from models import DetectionResult, CameraFrame


class ViSNETIntegration:
    """Integration with ViSNET AI platform"""

    def __init__(self, api_url: Optional[str] = None, api_key: Optional[str] = None):
        self.api_url = api_url or settings.VISNET_API_URL or "http://visnet-api:8080"
        self.api_key = api_key or settings.VISNET_API_KEY
        self.client = httpx.AsyncClient(
            base_url=self.api_url,
            headers={"Authorization": f"Bearer {self.api_key}"} if self.api_key else {},
            timeout=30.0
        )

    async def upload_image(
        self,
        frame: CameraFrame,
        image_data: Optional[bytes] = None,
        metadata: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Upload image to ViSNET platform

        Args:
            frame: Camera frame metadata
            image_data: Actual image bytes (optional for simulator)
            metadata: Additional metadata

        Returns:
            Upload response with image ID
        """
        payload = {
            "drone_id": str(frame.drone_id),
            "timestamp": frame.timestamp.isoformat(),
            "location": {
                "latitude": frame.latitude,
                "longitude": frame.longitude,
                "altitude": frame.altitude
            },
            "camera": {
                "gimbal_pitch": frame.gimbal_pitch,
                "gimbal_yaw": frame.gimbal_yaw,
                "fov": frame.fov,
                "width": frame.width,
                "height": frame.height
            },
            "metadata": metadata or {}
        }

        # In simulator, we don't have actual image data
        # In production, this would be multipart/form-data with image file
        if image_data:
            # For actual deployment
            files = {"image": ("frame.jpg", image_data, "image/jpeg")}
            response = await self.client.post("/images/upload", data=payload, files=files)
        else:
            # For simulator - just send metadata
            response = await self.client.post("/images/metadata", json=payload)

        response.raise_for_status()
        return response.json()

    async def submit_detection(
        self,
        detection: DetectionResult,
        image_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Submit detection result to ViSNET

        Args:
            detection: Detection result
            image_id: Associated image ID

        Returns:
            Submission response
        """
        payload = {
            "detection_id": str(detection.detection_id),
            "image_id": image_id or detection.image_id,
            "drone_id": str(detection.drone_id),
            "timestamp": detection.timestamp.isoformat(),
            "class_name": detection.class_name,
            "confidence": detection.confidence,
            "bounding_box": detection.bounding_box,
            "location": detection.position,
            "altitude": detection.altitude,
            "model": {
                "name": detection.model_name,
                "version": detection.model_version
            },
            "metadata": detection.metadata
        }

        response = await self.client.post("/detections", json=payload)
        response.raise_for_status()
        return response.json()

    async def create_work_order(
        self,
        detection: DetectionResult,
        priority: str = "medium",
        description: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create work order in ViSNET for defect remediation

        Args:
            detection: Detection that triggered work order
            priority: Priority level (low, medium, high, critical)
            description: Work order description

        Returns:
            Work order creation response
        """
        payload = {
            "detection_id": str(detection.detection_id),
            "type": "defect_remediation",
            "priority": priority,
            "title": f"{detection.class_name.title()} Detected",
            "description": description or f"Automated work order for {detection.class_name} detected by drone",
            "location": detection.position,
            "altitude": detection.altitude,
            "metadata": {
                "confidence": detection.confidence,
                "drone_id": str(detection.drone_id),
                "detection_timestamp": detection.timestamp.isoformat()
            }
        }

        response = await self.client.post("/work-orders", json=payload)
        response.raise_for_status()
        return response.json()

    async def update_asset_condition(
        self,
        asset_id: str,
        condition: str,
        detections: List[DetectionResult]
    ) -> Dict[str, Any]:
        """
        Update asset condition based on inspection detections

        Args:
            asset_id: Asset identifier
            condition: Condition rating (excellent, good, fair, poor, critical)
            detections: Related detections

        Returns:
            Update response
        """
        payload = {
            "asset_id": asset_id,
            "condition": condition,
            "inspection_date": datetime.utcnow().isoformat(),
            "detections": [
                {
                    "id": str(d.detection_id),
                    "class": d.class_name,
                    "confidence": d.confidence
                }
                for d in detections
            ]
        }

        response = await self.client.put(f"/assets/{asset_id}/condition", json=payload)
        response.raise_for_status()
        return response.json()

    async def get_asset_history(self, asset_id: str) -> Dict[str, Any]:
        """Get inspection history for an asset"""
        response = await self.client.get(f"/assets/{asset_id}/history")
        response.raise_for_status()
        return response.json()

    async def sync_mission_results(
        self,
        mission_id: str,
        results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Sync complete mission results to ViSNET

        Args:
            mission_id: Mission identifier
            results: Mission results including all detections and images

        Returns:
            Sync response
        """
        payload = {
            "mission_id": mission_id,
            "timestamp": datetime.utcnow().isoformat(),
            "status": results.get("status", "completed"),
            "duration": results.get("duration", 0),
            "images_captured": results.get("images_captured", 0),
            "detections": results.get("detections", []),
            "coverage_area": results.get("coverage_area"),
            "metadata": results.get("metadata", {})
        }

        response = await self.client.post("/missions/sync", json=payload)
        response.raise_for_status()
        return response.json()

    async def close(self):
        """Close HTTP client"""
        await self.client.aclose()


# GIS Integration Example
class GISIntegration:
    """Integration with GIS systems (WMS/WMTS)"""

    def __init__(self, wms_url: str):
        self.wms_url = wms_url

    async def get_terrain_layer(self, bounds: Dict) -> str:
        """Get terrain layer for map display"""
        # Return WMS URL for terrain
        return f"{self.wms_url}/terrain?bbox={bounds}"

    async def get_asset_layer(self, asset_type: str) -> str:
        """Get asset layer (e.g., bridges, towers)"""
        return f"{self.wms_url}/assets/{asset_type}"


# ERP/CMMS Integration Example
class ERPIntegration:
    """Integration with ERP/CMMS systems"""

    def __init__(self, erp_url: str, api_key: str):
        self.erp_url = erp_url
        self.api_key = api_key

    async def create_maintenance_ticket(self, work_order: Dict) -> Dict:
        """Create maintenance ticket in ERP system"""
        # Mock implementation
        return {"ticket_id": "MAINT-12345", "status": "created"}

    async def update_asset_register(self, asset_id: str, data: Dict) -> Dict:
        """Update asset register with inspection data"""
        return {"status": "updated"}


# Singleton instances
_visnet_integration: Optional[ViSNETIntegration] = None


def get_visnet_integration() -> ViSNETIntegration:
    """Get ViSNET integration instance"""
    global _visnet_integration
    if _visnet_integration is None:
        _visnet_integration = ViSNETIntegration()
    return _visnet_integration
