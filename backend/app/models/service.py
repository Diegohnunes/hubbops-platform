from typing import Optional, List
from sqlmodel import Field, SQLModel
from datetime import datetime
import json

class Service(SQLModel, table=True):
    id: str = Field(primary_key=True)
    name: str = Field(index=True)
    template: str
    status: str = Field(default="creating")
    created_at: datetime = Field(default_factory=datetime.now)
    namespace: str = Field(default="default")
    config_json: str = Field(default="{}")
    logs_json: str = Field(default="[]")
    deleted_at: Optional[datetime] = Field(default=None)

    @property
    def config(self):
        return json.loads(self.config_json)

    @config.setter
    def config(self, value):
        self.config_json = json.dumps(value)

    @property
    def logs(self):
        return json.loads(self.logs_json)

    @logs.setter
    def logs(self, value):
        self.logs_json = json.dumps(value)
