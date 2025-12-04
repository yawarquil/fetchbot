"""
FastAPI Backend for MovieFetchBot
"""
import os
import io
import zipfile
from datetime import datetime
from typing import Optional, List
from fastapi import FastAPI, HTTPException, Depends, Header, UploadFile, File
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware

from models.schemas import (
    Movie, TVShow, SearchResponse, ExportFormat, ExportConfig,
    UserCreate, UserLogin, Token, User, ContentType
)
from sources.tmdb import TMDBClient
from exporters import get_exporter
from utils.auth import (
    create_user, authenticate_user, create_access_token,
    get_current_user
)
from utils.validators import sanitize_query, parse_batch_file, validate_export_filename

# Initialize FastAPI app
app = FastAPI(
    title="MovieFetchBot API",
    description="Fetch movie and TV data from TMDB",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# TMDB API Key
TMDB_API_KEY = os.getenv("TMDB_API_KEY", "920654cb695ee99175e53d6da8dc2edf")


def get_tmdb_client() -> TMDBClient:
    return TMDBClient(TMDB_API_KEY)


async def get_optional_user(authorization: Optional[str] = Header(None)) -> Optional[User]:
    """Get current user if token provided, else None"""
    if not authorization or not authorization.startswith("Bearer "):
        return None
    token = authorization.split(" ")[1]
    return get_current_user(token)


async def require_user(authorization: str = Header(...)) -> User:
    """Require authenticated user"""
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid authorization header")
    token = authorization.split(" ")[1]
    user = get_current_user(token)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    return user


# ============ Auth Routes ============

@app.post("/api/auth/register", response_model=Token)
async def register(user_data: UserCreate):
    """Register a new user"""
    try:
        user = create_user(user_data)
        access_token = create_access_token(data={"sub": user.username})
        return Token(access_token=access_token)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/auth/login", response_model=Token)
async def login(login_data: UserLogin):
    """Login and get access token"""
    user = authenticate_user(login_data.username, login_data.password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid username or password")
    access_token = create_access_token(data={"sub": user["username"]})
    return Token(access_token=access_token)


@app.get("/api/auth/me", response_model=User)
async def get_me(user: User = Depends(require_user)):
    """Get current user info"""
    return user


# ============ Search Routes ============

@app.get("/api/search", response_model=SearchResponse)
async def search(
    q: str,
    type: str = "multi",
    client: TMDBClient = Depends(get_tmdb_client)
):
    """Search for movies and TV shows"""
    query = sanitize_query(q)
    if not query:
        raise HTTPException(status_code=400, detail="Query cannot be empty")
    
    try:
        results = await client.search(query, type)
        return results
    finally:
        await client.close()


# ============ Fetch Routes ============

@app.get("/api/movie/{movie_id}", response_model=Movie)
async def get_movie(
    movie_id: int,
    client: TMDBClient = Depends(get_tmdb_client)
):
    """Get movie details by ID"""
    try:
        return await client.get_movie(movie_id)
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Movie not found: {str(e)}")
    finally:
        await client.close()


@app.get("/api/tv/{tv_id}", response_model=TVShow)
async def get_tv_show(
    tv_id: int,
    include_episodes: bool = True,
    client: TMDBClient = Depends(get_tmdb_client)
):
    """Get TV show details by ID"""
    try:
        return await client.get_tv_show(tv_id, include_episodes)
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"TV show not found: {str(e)}")
    finally:
        await client.close()


# ============ Export Routes ============

@app.get("/api/export/movie/{movie_id}")
async def export_movie(
    movie_id: int,
    format: ExportFormat = ExportFormat.JSON,
    include_cast: bool = True,
    include_images: bool = True,
    client: TMDBClient = Depends(get_tmdb_client)
):
    """Export movie data in specified format"""
    try:
        movie = await client.get_movie(movie_id)
        
        config = ExportConfig(
            format=format,
            include_cast=include_cast,
            include_images=include_images
        )
        exporter = get_exporter(format, config)
        content = exporter.export(movie)
        
        filename = validate_export_filename(f"{movie.title}_{datetime.now().strftime('%Y%m%d')}")
        
        return StreamingResponse(
            io.BytesIO(content.encode('utf-8')),
            media_type=exporter.get_content_type(),
            headers={
                "Content-Disposition": f'attachment; filename="{filename}.{exporter.get_file_extension()}"'
            }
        )
    finally:
        await client.close()


@app.get("/api/export/tv/{tv_id}")
async def export_tv(
    tv_id: int,
    format: ExportFormat = ExportFormat.JSON,
    include_cast: bool = True,
    include_episodes: bool = True,
    include_images: bool = True,
    client: TMDBClient = Depends(get_tmdb_client)
):
    """Export TV show data in specified format"""
    try:
        tv = await client.get_tv_show(tv_id, include_episodes)
        
        config = ExportConfig(
            format=format,
            include_cast=include_cast,
            include_episodes=include_episodes,
            include_images=include_images
        )
        exporter = get_exporter(format, config)
        content = exporter.export(tv)
        
        filename = validate_export_filename(f"{tv.name}_{datetime.now().strftime('%Y%m%d')}")
        
        return StreamingResponse(
            io.BytesIO(content.encode('utf-8')),
            media_type=exporter.get_content_type(),
            headers={
                "Content-Disposition": f'attachment; filename="{filename}.{exporter.get_file_extension()}"'
            }
        )
    finally:
        await client.close()


@app.post("/api/export/batch")
async def export_batch(
    file: UploadFile = File(...),
    format: ExportFormat = ExportFormat.JSON,
    content_type: ContentType = ContentType.MOVIE,
    user: User = Depends(require_user),
    client: TMDBClient = Depends(get_tmdb_client)
):
    """Export multiple items from uploaded file (requires auth)"""
    try:
        content = await file.read()
        queries = parse_batch_file(content.decode('utf-8'))
        
        if not queries:
            raise HTTPException(status_code=400, detail="No valid queries found in file")
        
        config = ExportConfig(format=format)
        exporter = get_exporter(format, config)
        
        # Create ZIP file
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            for query in queries:
                try:
                    # Search first
                    search_results = await client.search(query, content_type.value)
                    if not search_results.results:
                        continue
                    
                    result = search_results.results[0]
                    
                    # Fetch full data
                    if result.media_type == ContentType.MOVIE:
                        data = await client.get_movie(result.id)
                        name = data.title
                    else:
                        data = await client.get_tv_show(result.id)
                        name = data.name
                    
                    # Export
                    export_content = exporter.export(data)
                    filename = validate_export_filename(f"{name}.{exporter.get_file_extension()}")
                    zip_file.writestr(filename, export_content)
                except Exception:
                    continue  # Skip failed items
        
        zip_buffer.seek(0)
        
        return StreamingResponse(
            zip_buffer,
            media_type="application/zip",
            headers={
                "Content-Disposition": f'attachment; filename="batch_export_{datetime.now().strftime("%Y%m%d_%H%M%S")}.zip"'
            }
        )
    finally:
        await client.close()


@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}
