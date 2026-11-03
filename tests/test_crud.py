from sqlalchemy import text  # type: ignore[reportMissingImports]

from backend.core.database import engine, SessionLocal
from backend import models


def test_postgresql_crud():
    print("\n========== POSTGRESQL CRUD TESTS ==========")

    # 1. Verify the database connection.
    with engine.connect() as connection:
        database_name = connection.execute(
            text("SELECT current_database()")
        ).scalar_one()

    assert database_name == "taskproject", (
        f"Expected taskproject, got {database_name}"
    )

    print(f"PASS: Connected to database '{database_name}'")

    db = SessionLocal()
    task_id = None

    try:
        # 2. CREATE
        task = models.Task(
            title="CRUD Test Task",
            description="Testing PostgreSQL CRUD operations",
            completed=False,
        )

        db.add(task)
        db.commit()
        db.refresh(task)

        task_id = task.id

        assert task_id is not None
        print(f"PASS: CREATE - Task created with ID {task_id}")

        # 3. READ
        created_task = db.get(models.Task, task_id)

        assert created_task is not None
        assert created_task.title == "CRUD Test Task"
        assert created_task.completed is False

        print("PASS: READ - Task retrieved successfully")

        # 4. UPDATE
        created_task.title = "Updated CRUD Test Task"
        created_task.description = "Task updated successfully"
        created_task.completed = True

        db.commit()
        db.expire_all()

        updated_task = db.get(models.Task, task_id)

        assert updated_task is not None
        assert updated_task.title == "Updated CRUD Test Task"
        assert updated_task.description == "Task updated successfully"
        assert updated_task.completed is True

        print("PASS: UPDATE - Task updated successfully")

        # 5. DELETE
        db.delete(updated_task)
        db.commit()
        db.expire_all()

        deleted_task = db.get(models.Task, task_id)

        assert deleted_task is None

        print("PASS: DELETE - Task deleted successfully")

        print("\nSUCCESS: All CRUD tests passed!")

    finally:
        # Clean up the test task if an earlier assertion fails.
        if task_id is not None:
            try:
                task = db.get(models.Task, task_id)

                if task is not None:
                    db.delete(task)
                    db.commit()
            except Exception:
                db.rollback()
        db.close()

    print("========== CRUD TESTS COMPLETE ==========\n")


if __name__ == "__main__":
    test_postgresql_crud()
