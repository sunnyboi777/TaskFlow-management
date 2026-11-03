
# pyright: reportMissingImports=false

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from ...core.database import get_db
from ...api.routes.auth import get_current_user
from ... import models
from ...schemas import TaskCreate, TaskOut, TaskUpdate

router = APIRouter()


# CREATE TASK
@router.post(
    "/tasks",
    response_model=TaskOut,
    status_code=status.HTTP_201_CREATED,
)
def create_task(
    task_data: TaskCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    task = models.Task(
        title=task_data.title,
        description=task_data.description,
        completed=False,
        user_id=current_user.id,
    )

    db.add(task)
    db.commit()
    db.refresh(task)

    return task


# GET ALL TASKS OF LOGGED-IN USER
@router.get("/tasks", response_model=list[TaskOut])
def get_tasks(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    return (
        db.query(models.Task)
        .filter(models.Task.user_id == current_user.id)
        .order_by(models.Task.id)
        .all()
    )


# GET ONE TASK
@router.get("/tasks/{task_id}", response_model=TaskOut)
def get_task(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    task = (
        db.query(models.Task)
        .filter(
            models.Task.id == task_id,
            models.Task.user_id == current_user.id,
        )
        .first()
    )

    if task is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found",
        )

    return task


# UPDATE TASK
@router.put("/tasks/{task_id}", response_model=TaskOut)
def update_task(
    task_id: int,
    task_data: TaskUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    task = (
        db.query(models.Task)
        .filter(
            models.Task.id == task_id,
            models.Task.user_id == current_user.id,
        )
        .first()
    )

    if task is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found",
        )

    task.title = task_data.title
    task.description = task_data.description
    task.completed = task_data.completed

    db.commit()
    db.refresh(task)

    return task


# DELETE TASK
@router.delete(
    "/tasks/{task_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_task(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    task = (
        db.query(models.Task)
        .filter(
            models.Task.id == task_id,
            models.Task.user_id == current_user.id,
        )
        .first()
    )

    if task is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found",
        )

    db.delete(task)
    db.commit()

    return Response(status_code=status.HTTP_204_NO_CONTENT)
