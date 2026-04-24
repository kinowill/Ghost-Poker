from ghost_poker.perception.stability import StableSnapshotEmitter, snapshot_signature


def test_snapshot_signature_is_order_independent() -> None:
    assert snapshot_signature({"street": "Flop", "hand_number": 3}) == snapshot_signature(
        {"hand_number": 3, "street": "Flop"}
    )


def test_stable_snapshot_emitter_waits_for_required_consecutive_reads() -> None:
    emitter = StableSnapshotEmitter(required_reads=2)
    snapshot = {"street": "Flop", "hand_number": 3}

    assert emitter.should_emit(snapshot) is False
    assert emitter.should_emit(snapshot) is True
    assert emitter.should_emit(snapshot) is False


def test_stable_snapshot_emitter_filters_single_read_noise() -> None:
    emitter = StableSnapshotEmitter(required_reads=2)
    stable_a = {"street": "Flop", "hand_number": 3}
    noise = {"street": None, "hand_number": 99}
    stable_b = {"street": "Turn", "hand_number": 3}

    assert emitter.should_emit(stable_a) is False
    assert emitter.should_emit(stable_a) is True
    assert emitter.should_emit(noise) is False
    assert emitter.should_emit(stable_b) is False
    assert emitter.should_emit(stable_b) is True


def test_stable_snapshot_emitter_keeps_immediate_mode_available() -> None:
    emitter = StableSnapshotEmitter(required_reads=1)

    assert emitter.should_emit({"street": "River"}) is True
