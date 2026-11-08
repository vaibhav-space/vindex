// Live Demo Data for Vindex — "Stop making AI watch the same video twice"
const DEMO_VINDEX_DATA = {
  "schema_version": "2.0",
  "video_hash": "93738e5ac619146593940e2bd31060ce518c98df14f98556e42ea43114af515a",
  "generated_at": "2026-11-08T13:45:00Z",
  "video_url": "demo.mp4",
  "metadata": {
    "resolution": "1280×720",
    "framerate": "24 fps",
    "channels": "Stereo (48 kHz)",
    "duration": "10.03s",
    "file_size": "4.4 MB"
  },
  "timeline": {
    "schema_version": "2.0",
    "video_hash": "93738e5ac619146593940e2bd31060ce518c98df14f98556e42ea43114af515a",
    "total_duration_ms": 10026,
    "scenes": [
      {
        "scene_id": "sc001",
        "start_ms": 0,
        "end_ms": 3200,
        "dominant_caption": "Robotic industrial manipulator arms operating in a dark modern research laboratory, spotlighting an illuminated sensory device inside a glass enclosure.",
        "shots": [
          {
            "shot_id": "sh001",
            "start_ms": 0,
            "end_ms": 3200,
            "frames": [
              {
                "schema_version": "1.0",
                "timestamp_ms": 1500,
                "source": "frame_extraction.pyav.v1",
                "shot_id": "sh001",
                "frame_path": "frames/sh001_1500.png",
                "frame_hash": "f_hash_sh001"
              }
            ],
            "asr_words": [
              {"schema_version": "1.0", "timestamp_ms": 0, "source": "asr.faster_whisper.v1", "word": "Stop", "start_ms": 0, "end_ms": 520, "confidence": 0.82},
              {"schema_version": "1.0", "timestamp_ms": 520, "source": "asr.faster_whisper.v1", "word": "making", "start_ms": 520, "end_ms": 880, "confidence": 1.0},
              {"schema_version": "1.0", "timestamp_ms": 880, "source": "asr.faster_whisper.v1", "word": "AI", "start_ms": 880, "end_ms": 1260, "confidence": 0.94},
              {"schema_version": "1.0", "timestamp_ms": 1260, "source": "asr.faster_whisper.v1", "word": "watch", "start_ms": 1260, "end_ms": 1600, "confidence": 1.0},
              {"schema_version": "1.0", "timestamp_ms": 1600, "source": "asr.faster_whisper.v1", "word": "the", "start_ms": 1600, "end_ms": 1800, "confidence": 1.0},
              {"schema_version": "1.0", "timestamp_ms": 1800, "source": "asr.faster_whisper.v1", "word": "same", "start_ms": 1800, "end_ms": 2040, "confidence": 1.0},
              {"schema_version": "1.0", "timestamp_ms": 2040, "source": "asr.faster_whisper.v1", "word": "video", "start_ms": 2040, "end_ms": 2380, "confidence": 1.0},
              {"schema_version": "1.0", "timestamp_ms": 2380, "source": "asr.faster_whisper.v1", "word": "twice.", "start_ms": 2380, "end_ms": 2960, "confidence": 1.0}
            ],
            "ocr": [
              {"schema_version": "1.0", "timestamp_ms": 1500, "source": "ocr.paddleocr.v1", "text": "LAB STAGE 01", "bbox": [110, 80, 240, 110], "confidence": 0.94, "frame_ref": "frames/sh001_1500.png"}
            ],
            "caption": {
              "schema_version": "1.0",
              "timestamp_ms": 1500,
              "source": "vlm_caption.mlx_qwen2vl.v1",
              "shot_id": "sh001",
              "caption_text": "Robotic industrial manipulator arms operating in a dark modern research laboratory, spotlighting an illuminated sensory device inside a glass enclosure.",
              "model_id": "qwen2-vl-2b-instruct",
              "model_version": "1.0"
            }
          }
        ]
      },
      {
        "scene_id": "sc002",
        "start_ms": 3200,
        "end_ms": 7500,
        "dominant_caption": "3D isometric perception pipeline decomposing video into parallel glass timeline layers, real-time audio waveform telemetry, and schema-validated JSON bounding overlays.",
        "shots": [
          {
            "shot_id": "sh002",
            "start_ms": 3200,
            "end_ms": 7500,
            "frames": [
              {
                "schema_version": "1.0",
                "timestamp_ms": 5000,
                "source": "frame_extraction.pyav.v1",
                "shot_id": "sh002",
                "frame_path": "frames/sh002_5000.png",
                "frame_hash": "f_hash_sh002"
              }
            ],
            "asr_words": [
              {"schema_version": "1.0", "timestamp_ms": 3840, "source": "asr.faster_whisper.v1", "word": "Vindex", "start_ms": 3840, "end_ms": 4180, "confidence": 0.97},
              {"schema_version": "1.0", "timestamp_ms": 4180, "source": "asr.faster_whisper.v1", "word": "compiles", "start_ms": 4180, "end_ms": 4740, "confidence": 0.99},
              {"schema_version": "1.0", "timestamp_ms": 4740, "source": "asr.faster_whisper.v1", "word": "it", "start_ms": 4740, "end_ms": 5060, "confidence": 1.0},
              {"schema_version": "1.0", "timestamp_ms": 5060, "source": "asr.faster_whisper.v1", "word": "into", "start_ms": 5060, "end_ms": 5640, "confidence": 0.99},
              {"schema_version": "1.0", "timestamp_ms": 5640, "source": "asr.faster_whisper.v1", "word": "reusable", "start_ms": 5640, "end_ms": 6220, "confidence": 0.76},
              {"schema_version": "1.0", "timestamp_ms": 6220, "source": "asr.faster_whisper.v1", "word": "knowledge.", "start_ms": 6220, "end_ms": 6740, "confidence": 1.0}
            ],
            "ocr": [
              {"schema_version": "1.0", "timestamp_ms": 4200, "source": "ocr.paddleocr.v1", "text": "\"scenes\": [...]", "bbox": [142, 128, 260, 220], "confidence": 0.98, "frame_ref": "frames/sh002_5000.png"},
              {"schema_version": "1.0", "timestamp_ms": 4800, "source": "ocr.paddleocr.v1", "text": "\"ocr\"", "bbox": [285, 45, 380, 85], "confidence": 0.96, "frame_ref": "frames/sh002_5000.png"},
              {"schema_version": "1.0", "timestamp_ms": 5200, "source": "ocr.paddleocr.v1", "text": "00:00:00", "bbox": [132, 595, 205, 620], "confidence": 0.99, "frame_ref": "frames/sh002_5000.png"},
              {"schema_version": "1.0", "timestamp_ms": 5200, "source": "ocr.paddleocr.v1", "text": "00:04:05", "bbox": [485, 630, 560, 655], "confidence": 0.99, "frame_ref": "frames/sh002_5000.png"}
            ],
            "caption": {
              "schema_version": "1.0",
              "timestamp_ms": 5000,
              "source": "vlm_caption.mlx_qwen2vl.v1",
              "shot_id": "sh002",
              "caption_text": "3D isometric perception pipeline decomposing video into parallel glass timeline layers, real-time audio waveform telemetry, and schema-validated JSON bounding overlays.",
              "model_id": "qwen2-vl-2b-instruct",
              "model_version": "1.0"
            }
          }
        ]
      },
      {
        "scene_id": "sc003",
        "start_ms": 7500,
        "end_ms": 10026,
        "dominant_caption": "Architectural monolithic title sequence against dark textured panelling displaying the VINDEX brand lockup and core descriptor.",
        "shots": [
          {
            "shot_id": "sh003",
            "start_ms": 7500,
            "end_ms": 10026,
            "frames": [
              {
                "schema_version": "1.0",
                "timestamp_ms": 8500,
                "source": "frame_extraction.pyav.v1",
                "shot_id": "sh003",
                "frame_path": "frames/sh003_8500.png",
                "frame_hash": "f_hash_sh003"
              }
            ],
            "asr_words": [],
            "ocr": [
              {"schema_version": "1.0", "timestamp_ms": 8000, "source": "ocr.paddleocr.v1", "text": "VINDEX", "bbox": [330, 420, 670, 540], "confidence": 0.99, "frame_ref": "frames/sh003_8500.png"},
              {"schema_version": "1.0", "timestamp_ms": 8500, "source": "ocr.paddleocr.v1", "text": "Open-source video knowledge compiler.", "bbox": [332, 580, 668, 620], "confidence": 0.99, "frame_ref": "frames/sh003_8500.png"}
            ],
            "caption": {
              "schema_version": "1.0",
              "timestamp_ms": 8500,
              "source": "vlm_caption.mlx_qwen2vl.v1",
              "shot_id": "sh003",
              "caption_text": "Architectural monolithic title sequence against dark textured panelling displaying the VINDEX brand lockup and core descriptor.",
              "model_id": "qwen2-vl-2b-instruct",
              "model_version": "1.0"
            }
          }
        ]
      }
    ],
    "events": [
      {"event_id": "ev001", "event_type": "SceneBoundary", "start_ms": 0, "end_ms": 0, "source_shot_ids": ["sh001"]},
      {"event_id": "ev002", "event_type": "SpeakerChange", "start_ms": 3840, "end_ms": 3840, "source_shot_ids": ["sh002"]},
      {"event_id": "ev003", "event_type": "SceneBoundary", "start_ms": 3200, "end_ms": 3200, "source_shot_ids": ["sh002"]},
      {"event_id": "ev004", "event_type": "SlideTransition", "start_ms": 7500, "end_ms": 7500, "source_shot_ids": ["sh003"]},
      {"event_id": "ev005", "event_type": "SceneBoundary", "start_ms": 7500, "end_ms": 7500, "source_shot_ids": ["sh003"]}
    ],
    "relationships": [
      {"relationship_id": "rel001", "source_id": "ocr.paddleocr.v1", "target_id": "vlm_caption.mlx_qwen2vl.v1", "relationship_type": "temporal_overlap", "metadata": {"shot_id": "sh002", "timestamp_ms": 4200}},
      {"relationship_id": "rel002", "source_id": "ocr.paddleocr.v1", "target_id": "vlm_caption.mlx_qwen2vl.v1", "relationship_type": "ocr_caption_match", "metadata": {"shot_id": "sh002", "matched_words": ["scenes", "ocr"]}},
      {"relationship_id": "rel003", "source_id": "ocr.paddleocr.v1", "target_id": "vlm_caption.mlx_qwen2vl.v1", "relationship_type": "ocr_caption_match", "metadata": {"shot_id": "sh003", "matched_words": ["vindex", "compiler"]}}
    ]
  },
  "narration_md": `# Visual Memory Index

**Generated at:** 2026-11-08T13:45:00Z
**Video Hash:** 93738e5ac619146593940e2bd31060ce518c98df14f98556e42ea43114af515a
**Narration Model:** qwen2-vl-2b-instruct (version: 1.0)

> [!NOTE]
> The narration text below is non-deterministic LLM output strictly grounded in the compiled video index.

---

## Chronological Scenes

### Scene 1: sc001 (00:00.000 – 00:03.200)
- **Visual Description:** Robotic industrial manipulator arms operating in a dark modern research laboratory, spotlighting an illuminated sensory device inside a glass enclosure.
- **On-Screen Text (OCR):** "LAB STAGE 01" detected at 00:01.500 (bounding box: [110, 80, 240, 110]).
- **Spoken Audio (ASR):** "Stop making AI watch the same video twice." (00:00.000 – 00:02.960).
- **Key Events:** Scene boundary initialized at timestamp 0 ms across shot sh001.

### Scene 2: sc002 (00:03.200 – 00:07.500)
- **Visual Description:** 3D isometric perception pipeline decomposing video into parallel glass timeline layers, real-time audio waveform telemetry, and schema-validated JSON bounding overlays.
- **On-Screen Text (OCR):**
  - \`"scenes": [...]\` detected at 00:04.200 (bounding box: [142, 128, 260, 220])
  - \`"ocr"\` detected at 00:04.800 (bounding box: [285, 45, 380, 85])
  - \`00:00:00\` and \`00:04:05\` waveform telemetry markers detected at 00:05.200
- **Spoken Audio (ASR):** "Vindex compiles it into reusable knowledge." (00:03.840 – 00:06.740).
- **Key Events:** Speaker emphasis shift at 00:03.840; scene boundary established across shot sh002.
- **Relationships:** Temporal overlap and semantic match between OCR telemetry (\`scenes\`, \`ocr\`) and VLM caption.

### Scene 3: sc003 (00:07.500 – 00:10.026)
- **Visual Description:** Architectural monolithic title sequence against dark textured panelling displaying the VINDEX brand lockup and core descriptor.
- **On-Screen Text (OCR):**
  - "VINDEX" (00:08.000, bounding box: [330, 420, 670, 540], confidence: 0.99)
  - "Open-source video knowledge compiler." (00:08.500, bounding box: [332, 580, 668, 620], confidence: 0.99)
- **Key Events:** Slide transition and scene cut into closing title sequence at 00:07.500.`
};

if (typeof module !== 'undefined' && module.exports) {
  module.exports = DEMO_VINDEX_DATA;
}
