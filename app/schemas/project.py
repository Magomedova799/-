from pydantic import BaseModel

class ProjectCreate(BaseModel):
    title: str
    description: str
    technologies: str
    category_id: int | None = None
    github_url: str | None = None
    demo_url: str | None = None
    image_url: str | None = None

class ProjectRead(BaseModel):
    id: int
    user_id: int
    title: str
    description: str
    technologies: str
    category_id: int | None = None
    github_url: str | None = None
    demo_url: str | None = None
    image_url: str | None = None

    model_config = {"from_attributes": True}