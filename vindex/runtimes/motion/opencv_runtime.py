from pathlib import Path
from typing import Any

from vindex.core.interfaces.runtimes import MotionAnalysisRuntime


class OpenCVFlowRuntime(MotionAnalysisRuntime):
    """Motion analysis runtime using OpenCV Farneback Optical Flow."""

    def load(self, model_dir_or_path: Path) -> None:
        """No-op: mathematical algorithm runtime."""
        pass

    def unload(self) -> None:
        """No-op: mathematical algorithm runtime."""
        pass

    def analyze_motion(self, frame_paths: list[Path], config: dict[str, Any]) -> dict[str, Any]:
        """Analyze motion/camera movement between a sequence of frame paths."""
        if len(frame_paths) < 2:
            return {
                "motion_score": 0.0,
                "camera_movement": "static",
            }

        import cv2
        import numpy as np

        flow_magnitudes = []
        pan_votes = 0
        tilt_votes = 0
        zoom_votes = 0
        static_votes = 0

        # Downscale for performance
        target_size = (256, 256)

        prev_gray = None

        for path in frame_paths:
            img: Any = cv2.imread(str(path))
            if img is None:
                continue
            
            img_resized = cv2.resize(img, target_size)
            gray = cv2.cvtColor(img_resized, cv2.COLOR_BGR2GRAY)

            if prev_gray is not None:
                # Calculate Farneback dense optical flow
                flow = cv2.calcOpticalFlowFarneback(
                    prev_gray, gray, None, 0.5, 3, 15, 3, 5, 1.2, 0
                )  # type: ignore[call-overload]

                
                # Flow in x and y
                fx, fy = flow[..., 0], flow[..., 1]
                magnitude = np.sqrt(fx**2 + fy**2)
                avg_mag = float(np.mean(magnitude))
                flow_magnitudes.append(avg_mag)

                # Classify camera movement (pan/tilt/zoom/static)
                if avg_mag < 1.0:
                    static_votes += 1
                else:
                    # Calculate mean direction
                    mean_fx = np.mean(fx)
                    mean_fy = np.mean(fy)
                    std_fx = np.std(fx)
                    std_fy = np.std(fy)

                    # High directional consensus indicates camera pan/tilt
                    if abs(mean_fx) > std_fx * 0.8:
                        pan_votes += 1
                    elif abs(mean_fy) > std_fy * 0.8:
                        tilt_votes += 1
                    else:
                        zoom_votes += 1

            prev_gray = gray

        if not flow_magnitudes:
            return {
                "motion_score": 0.0,
                "camera_movement": "static",
            }

        # Average motion score
        motion_score = float(np.mean(flow_magnitudes))

        # Determine camera movement by majority vote
        votes = {
            "static": static_votes,
            "pan": pan_votes,
            "tilt": tilt_votes,
            "zoom": zoom_votes,
        }
        camera_movement = max(votes, key=lambda k: votes[k])

        return {
            "motion_score": motion_score,
            "camera_movement": camera_movement,
        }

    @property
    def runtime_id(self) -> str:
        return "opencv.farneback.v1"
