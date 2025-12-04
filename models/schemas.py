"""
Pydantic models for MovieFetchBot
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum


class ContentType(str, Enum):
    MOVIE = "movie"
    TV = "tv"


class ExportFormat(str, Enum):
    JSON = "json"
    TXT = "txt"
    SQL = "sql"
    CSV = "csv"
    XML = "xml"


# ============ User Authentication Models ============

class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: str
    password: str = Field(..., min_length=6)


class UserLogin(BaseModel):
    username: str
    password: str


class User(BaseModel):
    id: str
    username: str
    email: str
    created_at: str


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    username: Optional[str] = None


# ============ Movie/TV Data Models ============

class ProductionCompany(BaseModel):
    id: int
    name: str
    logo_path: Optional[str] = None
    origin_country: Optional[str] = None


class Network(BaseModel):
    id: int
    name: str
    logo_path: Optional[str] = None
    origin_country: Optional[str] = None


class CastMember(BaseModel):
    id: Optional[int] = None
    name: str
    character: str
    profile_path: Optional[str] = None
    order: Optional[int] = None


class CrewMember(BaseModel):
    id: Optional[int] = None
    name: str
    job: str
    department: str
    profile_path: Optional[str] = None


class Genre(BaseModel):
    id: int
    name: str


class Video(BaseModel):
    id: str
    key: str
    name: str
    site: str
    type: str  # Trailer, Teaser, Clip, etc.


class Movie(BaseModel):
    id: int
    title: str
    original_title: Optional[str] = None
    original_language: Optional[str] = None
    overview: Optional[str] = None
    release_date: Optional[str] = None
    runtime: Optional[int] = None
    genres: List[Genre] = []
    vote_average: Optional[float] = None
    vote_count: Optional[int] = None
    popularity: Optional[float] = None
    poster_path: Optional[str] = None
    backdrop_path: Optional[str] = None
    cast: List[CastMember] = []
    crew: List[CrewMember] = []
    tagline: Optional[str] = None
    budget: Optional[int] = None
    revenue: Optional[int] = None
    status: Optional[str] = None
    imdb_id: Optional[str] = None
    homepage: Optional[str] = None
    production_companies: List[ProductionCompany] = []
    production_countries: List[str] = []
    spoken_languages: List[str] = []
    videos: List[Video] = []


class Episode(BaseModel):
    id: int
    episode_number: int
    season_number: int
    name: str
    overview: Optional[str] = None
    air_date: Optional[str] = None
    runtime: Optional[int] = None
    vote_average: Optional[float] = None
    vote_count: Optional[int] = None
    still_path: Optional[str] = None
    guest_stars: List[CastMember] = []
    crew: List[CrewMember] = []
    production_code: Optional[str] = None


class Season(BaseModel):
    id: int
    season_number: int
    name: str
    episode_count: int
    air_date: Optional[str] = None
    overview: Optional[str] = None
    poster_path: Optional[str] = None
    vote_average: Optional[float] = None


class TVShow(BaseModel):
    id: int
    name: str
    original_name: Optional[str] = None
    original_language: Optional[str] = None
    overview: Optional[str] = None
    first_air_date: Optional[str] = None
    last_air_date: Optional[str] = None
    number_of_episodes: Optional[int] = None
    number_of_seasons: Optional[int] = None
    episode_run_time: List[int] = []
    genres: List[Genre] = []
    vote_average: Optional[float] = None
    vote_count: Optional[int] = None
    popularity: Optional[float] = None
    poster_path: Optional[str] = None
    backdrop_path: Optional[str] = None
    cast: List[CastMember] = []
    crew: List[CrewMember] = []
    seasons: List[Season] = []
    status: Optional[str] = None
    type: Optional[str] = None  # Scripted, Reality, etc.
    tagline: Optional[str] = None
    homepage: Optional[str] = None
    in_production: Optional[bool] = None
    networks: List[Network] = []
    production_companies: List[ProductionCompany] = []
    origin_country: List[str] = []
    spoken_languages: List[str] = []
    episodes: List[Episode] = []
    videos: List[Video] = []
    created_by: List[str] = []


class SearchResult(BaseModel):
    id: int
    title: str
    media_type: ContentType
    release_date: Optional[str] = None
    poster_path: Optional[str] = None
    backdrop_path: Optional[str] = None
    overview: Optional[str] = None
    vote_average: Optional[float] = None


class SearchResponse(BaseModel):
    results: List[SearchResult]
    total_results: int
    total_pages: int


# ============ Export Configuration ============

class ExportConfig(BaseModel):
    format: ExportFormat = ExportFormat.JSON
    include_cast: bool = True
    include_episodes: bool = True
    include_images: bool = True
    max_cast: int = 10
    filename_pattern: str = "{title}_{date}"


class BatchItem(BaseModel):
    query: str
    media_type: Optional[ContentType] = None


# ============ Fetch History ============

class FetchHistoryItem(BaseModel):
    id: str
    title: str
    media_type: ContentType
    tmdb_id: int
    poster_path: Optional[str] = None
    fetched_at: str
    user_id: Optional[str] = None

