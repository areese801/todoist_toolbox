def test_import_todoist_tasks():
    """Smoke test: verify the existing module is importable."""
    from todoist import todoist_tasks

    assert hasattr(todoist_tasks, "get_active_tasks")
    assert hasattr(todoist_tasks, "get_overdue_recurring_tasks")
    assert hasattr(todoist_tasks, "_is_overdue")
    assert hasattr(todoist_tasks, "_make_due_datetime")
    assert hasattr(todoist_tasks, "_get_api_token")
