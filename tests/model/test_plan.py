import pytest
from PyQt5.QtCore import QTime
from PyQt5.QtWidgets import QApplication

from model.plan import Activity, PlanTableModel
from ui.importing import ReplaceOption

TEST_ACTIVITY = Activity(
    name="Test activity",
    length=42,
    start_time=QTime(2, 30, 0),
    is_fixed=True,
    is_rigid=True,
)

@pytest.fixture
def plan(database, config):
    return PlanTableModel(None, database, config)

def test_inserting_deleting(plan):
    plan.insert_activity(0)
    plan.insert_activities(0, [Activity(), Activity()])
    plan.delete_activities([0, 1, 2])

    assert plan.rowCount() == 0

@pytest.fixture
def application():
    return QApplication([])

def test_copying_pasting(plan, application):
    plan.insert_activity(0)
    plan.insert_activity(0)

    plan.copy_activities([0, 1])
    plan.paste_activities(0)

    assert plan.rowCount() == 4

def test_cutting_pasting(plan, application):
    plan.insert_activity(0)
    plan.insert_activity(0)

    plan.cut_activities([0, 1])
    plan.paste_activities(0)

    assert plan.rowCount() == 2

def test_plan_calculations(plan):
    # Test data from https://help.supermemo.org/images/thumb/b/bf/SuperMemo_Schedule_Plan.png/800px-SuperMemo_Schedule_Plan.png
    # Expected data is slightly different due to custom tweaks to calculation methods
    # Schema: [("is_fixed", "is_rigid", "start_time", "name", "length"), ("actual_length", "optimal_length")]
    TEST_PLAN = [
        [(True, False, QTime(7, 0, 0), "Breakfast and news", 22), (20, 21)],
        [(False, False, QTime(), "Incremental reading", 90), (84, 86)],
        [(False, False, QTime(), "Jobs: Planning the day", 10), (9, 9)],
        [(False, False, QTime(), "Work: DBT programming", 240), (225, 231)],
        [(False, False, QTime(), "Work: e-mail, phone calls", 35), (32, 33)],
        [(False, True, QTime(), "Sport: warm up", 27), (27, 27)],
        [(False, False, QTime(), "Sport: jogging", 54), (50, 52)],
        [(False, False, QTime(), "Meal: Dinner and Netflix", 40), (37, 38)],
        [(False, False, QTime(), "Rest", 54), (50, 52)],
        [(True, False, QTime(16, 0, 0), "Family", 116), (115, 111)],
        [(False, False, QTime(), "Meal: Supper with Family", 44), (43, 42)],
        [(False, False, QTime(), "Work: DBT report", 120), (119, 115)],
        [(False, False, QTime(), "Work: Tasklist", 58), (57, 55)],
        [(False, False, QTime(), "WWW: sport new, Brexit", 15), (14, 14)],
        [(False, False, QTime(), "Shower", 15), (14, 14)],
        [(False, False, QTime(), "YouTube: evening lectures", 116), (115, 111)],
        [(True, False, QTime(23, 59, 59), "sleep", 0), (0, 0)],
    ]

    activities = [
        Activity(
            is_fixed=activity[0],
            is_rigid=activity[1],
            start_time=activity[2],
            name=activity[3],
            length=activity[4],
        )
        for activity, _ in TEST_PLAN
    ]
    plan.insert_activities(0, activities)

    for activity, (_, expecteds) in zip(activities, TEST_PLAN):
        assert activity.actual_length == expecteds[0]
        assert activity.optimal_length == expecteds[1]

def export_and_import(plan, path, import_options):
    plan.insert_activity(0, TEST_ACTIVITY)

    plan.export_activities(path, [0])
    plan.import_activities(path, import_options)

def equal_to_test_activity(activity):
    return (activity.name == TEST_ACTIVITY.name
        and activity.length == TEST_ACTIVITY.length
        and activity.start_time == TEST_ACTIVITY.start_time
        and activity.is_fixed == TEST_ACTIVITY.is_fixed
        and activity.is_rigid == TEST_ACTIVITY.is_rigid)

def test_import_ignore(plan, tmp_path):
    export_and_import(
        plan,
        str(tmp_path / "plan.json"),
        { "replace_option": ReplaceOption.IGNORE }
    )

    assert plan.rowCount() == 1
    assert equal_to_test_activity(plan.get_activity(0))

def test_import_replace(plan, tmp_path):
    export_and_import(
        plan,
        str(tmp_path / "plan.json"),
        { "replace_option": ReplaceOption.REPLACE }
    )

    assert plan.rowCount() == 1
    assert equal_to_test_activity(plan.get_activity(0))

def test_import_add(plan, tmp_path):
    export_and_import(
        plan,
        str(tmp_path / "plan.json"),
        { "replace_option": ReplaceOption.ADD }
    )

    assert plan.rowCount() == 2
    assert plan.get_activity(0).id != plan.get_activity(1).id
    assert equal_to_test_activity(plan.get_activity(0))
    assert equal_to_test_activity(plan.get_activity(1))
