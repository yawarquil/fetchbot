"""
TMDB API Client for MovieFetchBot
"""
import httpx
from typing import Optional, List
import asyncio

from models.schemas import (
    Movie, TVShow, Episode, Season, SearchResult, SearchResponse,
    CastMember, CrewMember, Genre, ContentType, ProductionCompany,
    Network, Video
)


class TMDBClient:
    """Client for The Movie Database API"""
    
    BASE_URL = "https://api.themoviedb.org/3"
    IMAGE_BASE_URL = "https://image.tmdb.org/t/p"
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self._client: Optional[httpx.AsyncClient] = None
    
    def _img(self, path: str, size: str = "w500") -> Optional[str]:
        """Get full image URL"""
        if not path:
            return None
        return f"{self.IMAGE_BASE_URL}/{size}{path}"
    
    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(timeout=30.0)
        return self._client
    
    async def close(self):
        if self._client and not self._client.is_closed:
            await self._client.aclose()
    
    async def _request(self, endpoint: str, params: dict = None) -> dict:
        """Make a request to TMDB API with retry logic"""
        client = await self._get_client()
        params = params or {}
        params["api_key"] = self.api_key
        
        for attempt in range(3):
            try:
                response = await client.get(f"{self.BASE_URL}{endpoint}", params=params)
                response.raise_for_status()
                return response.json()
            except httpx.HTTPStatusError as e:
                if e.response.status_code == 429:  # Rate limit
                    await asyncio.sleep(2 ** attempt)
                    continue
                raise
            except httpx.RequestError:
                if attempt < 2:
                    await asyncio.sleep(1)
                    continue
                raise
        
        raise Exception("Max retries exceeded for TMDB API")
    
    def _parse_cast(self, credits: dict, max_cast: int = 15) -> List[CastMember]:
        """Parse cast from credits response"""
        cast_list = credits.get("cast", [])[:max_cast]
        return [
            CastMember(
                id=c.get("id"),
                name=c.get("name", "Unknown"),
                character=c.get("character", "Unknown"),
                profile_path=self._img(c.get("profile_path")),
                order=c.get("order")
            )
            for c in cast_list
        ]
    
    def _parse_crew(self, credits: dict, jobs: List[str] = None) -> List[CrewMember]:
        """Parse crew from credits response, optionally filtering by job"""
        crew_list = credits.get("crew", [])
        if jobs:
            crew_list = [c for c in crew_list if c.get("job") in jobs]
        return [
            CrewMember(
                id=c.get("id"),
                name=c.get("name", "Unknown"),
                job=c.get("job", "Unknown"),
                department=c.get("department", "Unknown"),
                profile_path=self._img(c.get("profile_path"))
            )
            for c in crew_list[:10]
        ]
    
    def _parse_genres(self, genres: list) -> List[Genre]:
        """Parse genres from response"""
        return [Genre(id=g["id"], name=g["name"]) for g in genres]
    
    def _parse_production_companies(self, companies: list) -> List[ProductionCompany]:
        """Parse production companies"""
        return [
            ProductionCompany(
                id=c["id"],
                name=c["name"],
                logo_path=self._img(c.get("logo_path"), "w200"),
                origin_country=c.get("origin_country")
            )
            for c in companies
        ]
    
    def _parse_networks(self, networks: list) -> List[Network]:
        """Parse TV networks"""
        return [
            Network(
                id=n["id"],
                name=n["name"],
                logo_path=self._img(n.get("logo_path"), "w200"),
                origin_country=n.get("origin_country")
            )
            for n in networks
        ]
    
    def _parse_videos(self, videos: dict) -> List[Video]:
        """Parse videos (trailers, clips, etc.)"""
        video_list = videos.get("results", [])
        return [
            Video(
                id=v["id"],
                key=v["key"],
                name=v["name"],
                site=v["site"],
                type=v["type"]
            )
            for v in video_list if v.get("site") == "YouTube"
        ][:5]  # Limit to 5 videos
    
    async def search(self, query: str, media_type: str = "multi") -> SearchResponse:
        """Search for movies and TV shows"""
        endpoint = f"/search/{media_type}"
        data = await self._request(endpoint, {"query": query})
        
        results = []
        for item in data.get("results", [])[:20]:
            # Determine media type
            item_type = item.get("media_type", media_type)
            if item_type not in ["movie", "tv"]:
                continue
            
            results.append(SearchResult(
                id=item["id"],
                title=item.get("title") or item.get("name", "Unknown"),
                media_type=ContentType.MOVIE if item_type == "movie" else ContentType.TV,
                release_date=item.get("release_date") or item.get("first_air_date"),
                poster_path=self._img(item.get("poster_path")),
                backdrop_path=self._img(item.get("backdrop_path"), "w1280"),
                overview=item.get("overview"),
                vote_average=item.get("vote_average")
            ))
        
        return SearchResponse(
            results=results,
            total_results=data.get("total_results", 0),
            total_pages=data.get("total_pages", 0)
        )
    
    async def get_movie(self, movie_id: int) -> Movie:
        """Fetch detailed movie information"""
        data = await self._request(
            f"/movie/{movie_id}",
            {"append_to_response": "credits,videos"}
        )
        
        credits = data.get("credits", {})
        
        return Movie(
            id=data["id"],
            title=data["title"],
            original_title=data.get("original_title"),
            original_language=data.get("original_language"),
            overview=data.get("overview"),
            release_date=data.get("release_date"),
            runtime=data.get("runtime"),
            genres=self._parse_genres(data.get("genres", [])),
            vote_average=data.get("vote_average"),
            vote_count=data.get("vote_count"),
            popularity=data.get("popularity"),
            poster_path=self._img(data.get("poster_path")),
            backdrop_path=self._img(data.get("backdrop_path"), "w1280"),
            cast=self._parse_cast(credits),
            crew=self._parse_crew(credits, ["Director", "Writer", "Screenplay", "Producer"]),
            tagline=data.get("tagline"),
            budget=data.get("budget"),
            revenue=data.get("revenue"),
            status=data.get("status"),
            imdb_id=data.get("imdb_id"),
            homepage=data.get("homepage"),
            production_companies=self._parse_production_companies(data.get("production_companies", [])),
            production_countries=[c.get("name") for c in data.get("production_countries", [])],
            spoken_languages=[l.get("english_name") or l.get("name") for l in data.get("spoken_languages", [])],
            videos=self._parse_videos(data.get("videos", {}))
        )
    
    async def get_tv_show(self, tv_id: int, include_episodes: bool = True) -> TVShow:
        """Fetch detailed TV show information"""
        data = await self._request(
            f"/tv/{tv_id}",
            {"append_to_response": "credits,videos"}
        )
        
        credits = data.get("credits", {})
        
        seasons = [
            Season(
                id=s["id"],
                season_number=s["season_number"],
                name=s["name"],
                episode_count=s["episode_count"],
                air_date=s.get("air_date"),
                overview=s.get("overview"),
                poster_path=self._img(s.get("poster_path")),
                vote_average=s.get("vote_average")
            )
            for s in data.get("seasons", [])
        ]
        
        episodes = []
        if include_episodes:
            for season in seasons:
                if season.season_number > 0:  # Skip specials (season 0)
                    season_episodes = await self.get_season_episodes(tv_id, season.season_number)
                    episodes.extend(season_episodes)
        
        return TVShow(
            id=data["id"],
            name=data["name"],
            original_name=data.get("original_name"),
            original_language=data.get("original_language"),
            overview=data.get("overview"),
            first_air_date=data.get("first_air_date"),
            last_air_date=data.get("last_air_date"),
            number_of_episodes=data.get("number_of_episodes"),
            number_of_seasons=data.get("number_of_seasons"),
            episode_run_time=data.get("episode_run_time", []),
            genres=self._parse_genres(data.get("genres", [])),
            vote_average=data.get("vote_average"),
            vote_count=data.get("vote_count"),
            popularity=data.get("popularity"),
            poster_path=self._img(data.get("poster_path")),
            backdrop_path=self._img(data.get("backdrop_path"), "w1280"),
            cast=self._parse_cast(credits),
            crew=self._parse_crew(credits, ["Executive Producer", "Creator"]),
            seasons=seasons,
            status=data.get("status"),
            type=data.get("type"),
            tagline=data.get("tagline"),
            homepage=data.get("homepage"),
            in_production=data.get("in_production"),
            networks=self._parse_networks(data.get("networks", [])),
            production_companies=self._parse_production_companies(data.get("production_companies", [])),
            origin_country=data.get("origin_country", []),
            spoken_languages=[l.get("english_name") or l.get("name") for l in data.get("spoken_languages", [])],
            episodes=episodes,
            videos=self._parse_videos(data.get("videos", {})),
            created_by=[c.get("name") for c in data.get("created_by", [])]
        )
    
    async def get_season_episodes(self, tv_id: int, season_number: int) -> List[Episode]:
        """Fetch all episodes for a specific season with full details"""
        data = await self._request(f"/tv/{tv_id}/season/{season_number}")
        
        return [
            Episode(
                id=ep["id"],
                episode_number=ep["episode_number"],
                season_number=season_number,
                name=ep["name"],
                overview=ep.get("overview"),
                air_date=ep.get("air_date"),
                runtime=ep.get("runtime"),
                vote_average=ep.get("vote_average"),
                vote_count=ep.get("vote_count"),
                still_path=self._img(ep.get("still_path"), "w300"),
                production_code=ep.get("production_code"),
                guest_stars=[
                    CastMember(
                        id=g.get("id"),
                        name=g.get("name", "Unknown"),
                        character=g.get("character", "Unknown"),
                        profile_path=self._img(g.get("profile_path"))
                    )
                    for g in ep.get("guest_stars", [])[:8]
                ],
                crew=[
                    CrewMember(
                        id=c.get("id"),
                        name=c.get("name", "Unknown"),
                        job=c.get("job", "Unknown"),
                        department=c.get("department", "Unknown"),
                        profile_path=self._img(c.get("profile_path"))
                    )
                    for c in ep.get("crew", []) if c.get("job") in ["Director", "Writer"]
                ][:5]
            )
            for ep in data.get("episodes", [])
        ]

