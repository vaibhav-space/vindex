import io
import time
from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

from vindex.api.app import app
from vindex.core.schemas.artifacts import Timeline, VisualMemory

client = TestClient(app)

def test_get_index():
    response = client.get("/")
    assert response.status_code == 200
    assert "vindex studio" in response.text.lower() or "vindex client" in response.text.lower()

@patch("vindex.api.app.compile_video")
def test_compile_and_status_flow(mock_compile):
    # Setup mock return value for compile_video
    mock_vm = MagicMock(spec=VisualMemory)
    mock_timeline = MagicMock(spec=Timeline)
    mock_timeline.scenes = []
    mock_timeline.total_duration_ms = 1000
    mock_timeline.model_dump.returnOf = {}
    mock_vm.timeline = mock_timeline
    mock_vm.video_hash = "mock_hash"
    mock_vm.model_dump.return_value = {"mock": "result"}
    
    mock_compile.return_value = mock_vm

    # Create dummy video content
    dummy_video = io.BytesIO(b"dummy mp4 file content")
    
    # Trigger compile request
    response = client.post(
        "/api/compile",
        files={"video": ("test_vid.mp4", dummy_video, "video/mp4")},
        data={"sampling_strategy": "middle", "stages": "scene,frame"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "job_id" in data
    assert data["status"] == "processing"
    
    job_id = data["job_id"]
    
    # Immediately check status
    status_response = client.get(f"/api/jobs/{job_id}/status")
    assert status_response.status_code == 200
    status_data = status_response.json()
    assert status_data["job_id"] == job_id
    assert status_data["status"] in ["processing", "completed"]

    # If status is not completed yet, wait up to 2 seconds for the background task
    retries = 20
    while retries > 0:
        status_response = client.get(f"/api/jobs/{job_id}/status")
        status_data = status_response.json()
        if status_data["status"] in ["completed", "failed"]:
            break
        time.sleep(0.1)
        retries -= 1
        
    assert status_data["status"] == "completed"
    
    # Check result
    result_response = client.get(f"/api/jobs/{job_id}/result")
    assert result_response.status_code == 200
    result_data = result_response.json()
    assert "mock" in result_data or "timeline" in result_data

    # Check narration
    narration_response = client.get(f"/api/jobs/{job_id}/narration")
    assert narration_response.status_code == 200
    narration_data = narration_response.json()
    assert "markdown" in narration_data

def test_invalid_job_id():
    # Verify 404 for unknown job_id
    response = client.get("/api/jobs/invalid-uuid-string-xyz/status")
    assert response.status_code == 404
    
    response = client.get("/api/jobs/invalid-uuid-string-xyz/result")
    assert response.status_code == 404
    
    response = client.get("/api/jobs/invalid-uuid-string-xyz/narration")
    assert response.status_code == 404


def test_demo_static_endpoints():
    # Test demo video serving
    response = client.get("/demo.mp4")
    assert response.status_code == 200
    assert "video/mp4" in response.headers.get("content-type", "")

    # Test demo data javascript serving
    response = client.get("/demo_data.js")
    assert response.status_code == 200
    assert "DEMO_VINDEX_DATA" in response.text

    # Test demo keyframe images
    response = client.get("/frames/sh001_1500.png")
    assert response.status_code == 200

    # Test nonexistent frame returns 404
    response = client.get("/frames/missing_frame_xyz.png")
    assert response.status_code == 404

