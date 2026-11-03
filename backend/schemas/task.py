from pydantic import BaseModel, ConfigDict, Field  # pyright: ignore[reportMissingImports]


class TaskCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    description: str = Field(default="", max_length=2000)


class TaskUpdate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    description: str = Field(default="", max_length=2000)
    completed: bool = False


class TaskOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    description: str
    completed: bool
