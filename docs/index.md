# vindex

vindex is an open-source, local-first video knowledge compiler. It processes video streams through multi-modal extractor pipelines and compiles them into structured, queryable knowledge indexes (Visual Memory).

## Key Features

- **Local-first & Privacy-preserving:** Heavy model inference runs entirely on local runtimes. Zero data leaks, zero external API dependencies for extraction.
- **Unified Schema:** Strictly structured observations and compiled artifacts (Shots, Scenes, Events, Timelines) defined via Pydantic v2.
- **Content-Addressed Caching:** Deterministic hashing allows skipping redundant model runs on previously processed videos.
- **Grounded Narration:** LLM-driven descriptions strictly trace back to visual and audio observations.
