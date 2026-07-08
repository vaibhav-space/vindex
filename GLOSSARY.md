# GLOSSARY.md — vindex

These terms are canonical across the entire project. All schema field names, class names, and documentation must use these terms exactly.

| Term | Definition |
|---|---|
| **Shot** | A single continuous camera take between two cuts. The raw unit output by scene detection tools. Never derived. |
| **Scene** | A semantically coherent group of one or more Shots. Always derived by the compiler — never raw. |
| **Segment** | An abstract, generic time-range container used as the base type when the Shot/Scene distinction does not matter. Used in schema and interface design; not user-facing. |
| **Observation** | The atomic fact unit emitted by an extractor: one OCR reading, one shot boundary, one ASR word, one VLM caption. One thing one stage noticed at one point in time. |
| **Event** | A specific, named occurrence derived from one or more Observations (e.g., "speaker change," "slide transition"). One level of interpretation above a raw Observation. |
| **Relationship** | A structured link between two Observations, Entities, or Events (e.g., caption-overlaps-graph, speaker-mentions-entity). |
| **Entity** | A named thing with a stable ID recognized across scenes (a person, a logo, a recurring on-screen element). The anchor that makes Relationships possible across time. |
| **Timeline** | The ordered spine of Shots, Scenes, and Events across the whole video. The master index other artifacts reference by position. |
| **Clip** | Reserved exclusively for rendered, byte-level video output — an actual exported mp4 sub-range. Never use "Clip" for metadata-only time ranges. |
| **Frame Group** | Internal-only term for the sampled keyframes representing one Shot. Not user-facing. |
| **visual_memory.json** | The top-level compiled output artifact. The product-facing name. Internal class and module names use Index, not Memory. |

## Terms to Avoid

- **Moment** — too vague, too marketing-flavored. Avoid in code and schemas entirely.
- **Memory** (as an internal class or module name) — reserved for the product-facing filename only. Internal names use `Index` and `Observation`/`Event`. This prevents contributors from accidentally importing mutable-agent-memory semantics (decay, merge, forget) into what must remain a stable, re-derivable compilation artifact.

## Recommended Mental Hierarchy

```
Shot (raw)
  └── Scene (compiled group of Shots)
        └── Timeline (ordered sequence of Scenes and Events)

Observations attach at the Shot/Scene level.
Observations roll up into Events and Relationships.
Events and Relationships are anchored by persistent Entity identities.
```
