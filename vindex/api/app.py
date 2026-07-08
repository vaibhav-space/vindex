import json
import logging
import uuid
from pathlib import Path
from typing import Any, Dict

from fastapi import FastAPI, BackgroundTasks, UploadFile, File, Form, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware

from vindex.compiler.pipeline import compile_video

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("vindex.api")

app = FastAPI(
    title="Vindex API",
    description="REST Service for the Vindex Video Perception Compiler",
    version="0.1.0"
)

# Enable CORS for external agents/frontends
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_JOBS_DIR = Path("/Users/vaibhav/code/vindex/temp_jobs")
BASE_JOBS_DIR.mkdir(parents=True, exist_ok=True)

# In-memory job state tracking
JOBS: Dict[str, Dict[str, Any]] = {}

def background_compile(job_id: str, video_temp_path: Path, job_dir: Path, config: dict):
    try:
        logger.info(f"Starting job {job_id} on {video_temp_path}")
        JOBS[job_id]["status"] = "processing"
        JOBS[job_id]["progress"] = "Compiling video (running perception pipeline)..."
        
        # Execute the Vindex pipeline
        vm = compile_video(video_temp_path, job_dir, config)
        
        # Load output data
        vm_json_path = job_dir / "visual_memory.json"
        vm_md_path = job_dir / "visual_memory.md"
        
        if vm_json_path.exists():
            with open(vm_json_path, "r", encoding="utf-8") as f:
                JOBS[job_id]["result"] = json.load(f)
        else:
            JOBS[job_id]["result"] = vm.model_dump()
            
        if vm_md_path.exists():
            JOBS[job_id]["narration"] = vm_md_path.read_text(encoding="utf-8")
        else:
            JOBS[job_id]["narration"] = ""
            
        JOBS[job_id]["status"] = "completed"
        JOBS[job_id]["progress"] = "Compilation completed successfully!"
        logger.info(f"Job {job_id} completed successfully.")
    except Exception as e:
        logger.exception(f"Job {job_id} failed.")
        JOBS[job_id]["status"] = "failed"
        JOBS[job_id]["progress"] = "Compilation failed."
        JOBS[job_id]["error"] = str(e)
    finally:
        # Cleanup raw uploaded video file to save disk space
        if video_temp_path.exists():
            try:
                video_temp_path.unlink()
            except Exception as cleanup_err:
                logger.error(f"Error cleaning up temp video {video_temp_path}: {cleanup_err}")

@app.post("/api/compile")
async def compile_video_endpoint(
    background_tasks: BackgroundTasks,
    video: UploadFile = File(...),
    sampling_strategy: str = Form("middle"),
    stages: str = Form(None)
):
    job_id = str(uuid.uuid4())
    job_dir = BASE_JOBS_DIR / job_id
    job_dir.mkdir(parents=True, exist_ok=True)
    
    # Save the uploaded file to a unique temp path
    video_temp_path = BASE_JOBS_DIR / f"raw_{job_id}_{video.filename}"
    try:
        with open(video_temp_path, "wb") as f:
            content = await video.read()
            f.write(content)
    except Exception as e:
        logger.error(f"Failed to write temp video file: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to upload video file: {str(e)}")

    # Construct Vindex configuration
    config = {
        "use_cache": False,
        "sampling_strategy": sampling_strategy,
        "asr_model_dir": "/Users/vaibhav/.vindex/models/faster-whisper-medium",

        "det_model_dir": "/Users/vaibhav/.paddlex/official_models/PP-OCRv6_medium_det",
        "rec_model_dir": "/Users/vaibhav/.paddlex/official_models/PP-OCRv6_medium_rec",
        "vlm_model_dir": "/Users/vaibhav/.vindex/models/Qwen2-VL-2B-Instruct-4bit",
        "embed_model_dir": "/Users/vaibhav/.vindex/models/all-MiniLM-L6-v2",
        "scene_understanding.ignore_text_regions": True,
        "similarity_threshold": 0.65,
        "max_gap_ms": 5000,
    }
    if stages:
        config["stages"] = [s.strip() for s in stages.split(",") if s.strip()]

        
    JOBS[job_id] = {
        "job_id": job_id,
        "status": "processing",
        "progress": "Video uploaded. Queuing compilation pipeline...",
        "error": None,
        "result": None,
        "narration": None,
        "job_dir": str(job_dir)
    }
    
    # Queue background task
    background_tasks.add_task(background_compile, job_id, video_temp_path, job_dir, config)
    
    return {"job_id": job_id, "status": "processing"}

@app.get("/api/jobs/{job_id}/status")
def get_job_status(job_id: str):
    if job_id not in JOBS:
        raise HTTPException(status_code=404, detail="Job not found")
    job = JOBS[job_id]
    return {
        "job_id": job_id,
        "status": job["status"],
        "progress": job["progress"],
        "error": job["error"]
    }

@app.get("/api/jobs/{job_id}/result")
def get_job_result(job_id: str):
    if job_id not in JOBS:
        raise HTTPException(status_code=404, detail="Job not found")
    job = JOBS[job_id]
    if job["status"] != "completed":
        raise HTTPException(status_code=400, detail=f"Job is not completed. Current status: {job['status']}")
    return job["result"]

@app.get("/api/jobs/{job_id}/narration")
def get_job_narration(job_id: str):
    if job_id not in JOBS:
        raise HTTPException(status_code=404, detail="Job not found")
    job = JOBS[job_id]
    if job["status"] != "completed":
        raise HTTPException(status_code=400, detail=f"Job is not completed. Current status: {job['status']}")
    return {"markdown": job["narration"]}

@app.get("/api/jobs/{job_id}/frame/{filename}")
def get_job_frame(job_id: str, filename: str):
    if job_id not in JOBS:
        raise HTTPException(status_code=404, detail="Job not found")
    
    frame_path = BASE_JOBS_DIR / job_id / "frames" / filename
    if not frame_path.exists():
        raise HTTPException(status_code=404, detail="Frame image not found")
        
    return FileResponse(frame_path)

@app.get("/", response_class=HTMLResponse)
def get_index():
    static_file = Path(__file__).parent / "static" / "index.html"
    if static_file.exists():
        return HTMLResponse(content=static_file.read_text(encoding="utf-8"), status_code=200)
    return HTMLResponse(
        content="<h1>Vindex Client UI index.html not found. Place it in vindex/api/static/index.html</h1>",
        status_code=404
    )
