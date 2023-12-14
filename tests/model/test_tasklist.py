import pytest
from PyQt5.QtCore import QDate

from model.tasklist import DeadlineType, Task, TasklistTableModel
from ui.importing import ReplaceOption

TEST_TASK = Task(
    name="Test task",
    value=7,
    cost=11,
    date_created=QDate(2019, 11, 13),
    deadline=QDate(2020, 11, 13),
    deadline_type=DeadlineType.STANDARD,
)

@pytest.fixture
def tasklist(database, config):
    return TasklistTableModel(None, database, config)

def test_adding_deleting(tasklist):
    tasklist.add_task()
    tasklist.add_tasks([Task(), Task()])
    tasklist.delete_tasks([0, 1, 2])

    assert tasklist.rowCount() == 0

def export_and_import(tasklist, path, import_options):
    tasklist.add_task(TEST_TASK)

    tasklist.export_tasks(path, [0])
    tasklist.import_tasks(path, import_options)

def equal_to_test_task(task):
    return (task.name == TEST_TASK.name
        and task.value == TEST_TASK.value
        and task.cost == TEST_TASK.cost
        and task.DATE_CREATED == TEST_TASK.DATE_CREATED
        and task.deadline == TEST_TASK.deadline
        and task.deadline_type == TEST_TASK.deadline_type)

def test_import_ignore(tasklist, tmp_path):
    export_and_import(
        tasklist,
        str(tmp_path / "tasklist.json"),
        { "replace_option": ReplaceOption.IGNORE }
    )

    assert tasklist.rowCount() == 1
    assert equal_to_test_task(tasklist.get_task(0))

def test_import_replace(tasklist, tmp_path):
    export_and_import(
        tasklist,
        str(tmp_path / "tasklist.json"),
        { "replace_option": ReplaceOption.REPLACE }
    )

    assert tasklist.rowCount() == 1
    assert equal_to_test_task(tasklist.get_task(0))

def test_import_add(tasklist, tmp_path):
    export_and_import(
        tasklist,
        str(tmp_path / "tasklist.json"),
        { "replace_option": ReplaceOption.ADD }
    )

    assert tasklist.rowCount() == 2
    assert tasklist.get_task(0).id != tasklist.get_task(1).id
    assert equal_to_test_task(tasklist.get_task(0))
    assert equal_to_test_task(tasklist.get_task(1))

@pytest.mark.parametrize(
    ("deadline_type", "date_created", "deadline", "expected_priority"),
    [
        (DeadlineType.STANDARD, QDate().currentDate().addDays(-10), QDate().currentDate().addDays(10), 0.5),
        (DeadlineType.STANDARD, QDate().currentDate().addDays(-0), QDate().currentDate().addDays(10), 0.0),
        (DeadlineType.STANDARD, QDate().currentDate().addDays(-10), QDate().currentDate().addDays(0), 1.0),
        (DeadlineType.STANDARD, QDate().currentDate().addDays(-20), QDate().currentDate().addDays(-10), 1.0),

        (DeadlineType.DECLINE, QDate().currentDate().addDays(-10), QDate().currentDate().addDays(10), 0.5),
        (DeadlineType.DECLINE, QDate().currentDate().addDays(-0), QDate().currentDate().addDays(10), 1.0),
        (DeadlineType.DECLINE, QDate().currentDate().addDays(-10), QDate().currentDate().addDays(0), 0.0),
        (DeadlineType.DECLINE, QDate().currentDate().addDays(-20), QDate().currentDate().addDays(-10), 0.0),

        (DeadlineType.POSTDATE, QDate().currentDate().addDays(-10), QDate().currentDate().addDays(10), 0.0),
        (DeadlineType.POSTDATE, QDate().currentDate().addDays(-0), QDate().currentDate().addDays(10), 0.0),
        (DeadlineType.POSTDATE, QDate().currentDate().addDays(-10), QDate().currentDate().addDays(0), 1.0),
        (DeadlineType.POSTDATE, QDate().currentDate().addDays(-20), QDate().currentDate().addDays(-10), 1.0),

        (DeadlineType.POSTDECLINE, QDate().currentDate().addDays(-10), QDate().currentDate().addDays(10), 1.0),
        (DeadlineType.POSTDECLINE, QDate().currentDate().addDays(-0), QDate().currentDate().addDays(10), 1.0),
        (DeadlineType.POSTDECLINE, QDate().currentDate().addDays(-10), QDate().currentDate().addDays(0), 1.0),
        (DeadlineType.POSTDECLINE, QDate().currentDate().addDays(-15), QDate().currentDate().addDays(-5), 0.5),
        (DeadlineType.POSTDECLINE, QDate().currentDate().addDays(-20), QDate().currentDate().addDays(-10), 0.0),
    ],
)
def test_deadline_functions(deadline_type, date_created, deadline, expected_priority):
    task = Task(
        value=1,
        cost=1,
        date_created=date_created,
        deadline=deadline,
        deadline_type=deadline_type,
    )

    assert task.get_priority() == pytest.approx(expected_priority)
