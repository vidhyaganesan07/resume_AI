from typing import Literal

from pydantic import BaseModel, EmailStr, Field, HttpUrl


class SignUpRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6, max_length=128)
    full_name: str | None = Field(default=None, max_length=200)


class SignInRequest(BaseModel):
    email: EmailStr
    password: str


class AuthResponse(BaseModel):
    access_token: str
    user: dict


class AnalyzeRequest(BaseModel):
    resumeId: str | None = None
    title: str = Field(min_length=1, max_length=200)
    rawText: str = Field(min_length=20, max_length=50000)
    fileName: str | None = Field(default=None, max_length=255)


class MatchRequest(BaseModel):
    resumeId: str
    jdTitle: str = Field(min_length=1, max_length=200)
    jdCompany: str | None = Field(default=None, max_length=200)
    jdText: str = Field(min_length=20, max_length=50000)


class AssistantRequest(BaseModel):
    resumeId: str | None = None
    question: str = Field(min_length=1, max_length=2000)


class RoleRequest(BaseModel):
    role: Literal["job_seeker", "recruiter"]


class RankFilters(BaseModel):
    seniority: str | None = Field(default=None, max_length=60)
    mustHaveSkills: str | None = Field(default=None, max_length=500)
    niceToHaveSkills: str | None = Field(default=None, max_length=500)
    minYears: float | None = Field(default=None, ge=0, le=40)
    workMode: str | None = Field(default=None, max_length=60)
    domain: str | None = Field(default=None, max_length=200)
    cultureNotes: str | None = Field(default=None, max_length=500)


class RankRequest(BaseModel):
    jdTitle: str = Field(min_length=1, max_length=200)
    jdText: str = Field(min_length=20, max_length=50000)
    limit: int | None = Field(default=None, ge=1, le=50)
    filters: RankFilters | None = None


class ImportUrlRequest(BaseModel):
    url: HttpUrl
    title: str | None = Field(default=None, max_length=200)
