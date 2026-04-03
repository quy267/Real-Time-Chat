"""Integration tests for cleanup Celery tasks — verify they run without errors."""



def test_clean_expired_data_runs_without_error():
    """clean_expired_data should execute and return status ok without raising."""
    from src.adapters.celery_tasks.cleanup_tasks import clean_expired_data

    result = clean_expired_data()

    assert result["status"] == "ok"
    assert isinstance(result["actions"], list)
    assert len(result["actions"]) > 0


def test_clean_expired_data_reports_expected_actions():
    """clean_expired_data should report all expected maintenance actions."""
    from src.adapters.celery_tasks.cleanup_tasks import clean_expired_data

    result = clean_expired_data()

    actions = result["actions"]
    assert "stale_presence_keys_checked" in actions
    assert "expired_token_blacklist_checked" in actions
    assert "message_archival_checked" in actions


def test_clean_expired_data_is_idempotent():
    """Running cleanup multiple times should not raise or change behavior."""
    from src.adapters.celery_tasks.cleanup_tasks import clean_expired_data

    result1 = clean_expired_data()
    result2 = clean_expired_data()

    assert result1["status"] == result2["status"]
    assert result1["actions"] == result2["actions"]
