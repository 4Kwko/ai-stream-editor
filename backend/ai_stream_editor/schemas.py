from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, FiniteFloat


class InputModel(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class ProjectCreate(InputModel):
    source_path: str = Field(min_length=1, max_length=32760)


class Caption(InputModel):
    id: str = Field(min_length=1, max_length=128)
    start_seconds: FiniteFloat = Field(ge=0)
    end_seconds: FiniteFloat = Field(gt=0)
    text: str = Field(min_length=1, max_length=1000)


class ClipPatch(InputModel):
    start_seconds: FiniteFloat | None = Field(default=None, ge=0)
    end_seconds: FiniteFloat | None = Field(default=None, gt=0)
    captions: list[Caption] | None = Field(default=None, max_length=5000)
    review_status: Literal["pending", "approved", "rejected"] | None = None
    expected_revision: int | None = Field(default=None, ge=1)


class ExportRequest(InputModel):
    output_directory: str = Field(min_length=1, max_length=32760)


class AutomationPatch(InputModel):
    enabled: bool | None = None
    channel_login: str | None = Field(default=None, pattern=r"^[a-z0-9_]{3,25}$")
    output_format: Literal["16:9", "9:16"] | None = None
