from vindex.core.interfaces.extractor import Extractor
from vindex.core.interfaces.runtimes import ASRRuntime
from vindex.core.schemas.observations import ShotObservation


def test_schema_import():
    obs = ShotObservation(
        timestamp_ms=1000,
        source="test",
        shot_id="sh001",
        start_ms=0,
        end_ms=2000,
    )
    assert obs.shot_id == "sh001"
    assert obs.timestamp_ms == 1000


def test_interface_exists():
    assert issubclass(Extractor, object)
    assert issubclass(ASRRuntime, object)
