from sqlalchemy import Column, Integer, String, Boolean
from db import Base

class TaskDB(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    description = Column(String, default="")
    done = Column(Boolean, default=False)