"""
TXT Exporter
"""
from typing import Union, List
from models.schemas import Movie, TVShow
from .base import BaseExporter


class TXTExporter(BaseExporter):
    """Export data to plain text format"""
    
    def _format_movie(self, movie: dict) -> str:
        lines = [
            f"{'='*60}",
            f"MOVIE: {movie.get('title', 'Unknown')}",
            f"{'='*60}",
            "",
            f"Original Title: {movie.get('original_title', 'N/A')}",
            f"Release Date: {movie.get('release_date', 'N/A')}",
            f"Runtime: {movie.get('runtime', 'N/A')} minutes",
            f"Status: {movie.get('status', 'N/A')}",
            "",
            f"Rating: {movie.get('vote_average', 'N/A')}/10 ({movie.get('vote_count', 0)} votes)",
            f"Popularity: {movie.get('popularity', 'N/A')}",
            "",
            f"Genres: {', '.join(g.get('name', '') for g in movie.get('genres', []))}",
            "",
            f"Tagline: {movie.get('tagline', 'N/A')}",
            "",
            "Overview:",
            movie.get('overview', 'No overview available.'),
            "",
        ]
        
        if movie.get('cast'):
            lines.append("Cast:")
            for c in movie['cast']:
                lines.append(f"  - {c.get('name', 'Unknown')} as {c.get('character', 'Unknown')}")
            lines.append("")
        
        if movie.get('budget'):
            lines.append(f"Budget: ${movie['budget']:,}")
        if movie.get('revenue'):
            lines.append(f"Revenue: ${movie['revenue']:,}")
        
        if movie.get('poster_path'):
            lines.append(f"\nPoster: {movie['poster_path']}")
        
        return '\n'.join(lines)
    
    def _format_tv(self, tv: dict) -> str:
        lines = [
            f"{'='*60}",
            f"TV SHOW: {tv.get('name', 'Unknown')}",
            f"{'='*60}",
            "",
            f"Original Name: {tv.get('original_name', 'N/A')}",
            f"First Air Date: {tv.get('first_air_date', 'N/A')}",
            f"Last Air Date: {tv.get('last_air_date', 'N/A')}",
            f"Status: {tv.get('status', 'N/A')}",
            f"Seasons: {tv.get('number_of_seasons', 'N/A')}",
            f"Episodes: {tv.get('number_of_episodes', 'N/A')}",
            "",
            f"Rating: {tv.get('vote_average', 'N/A')}/10 ({tv.get('vote_count', 0)} votes)",
            f"Popularity: {tv.get('popularity', 'N/A')}",
            "",
            f"Genres: {', '.join(g.get('name', '') for g in tv.get('genres', []))}",
            "",
            f"Tagline: {tv.get('tagline', 'N/A')}",
            "",
            "Overview:",
            tv.get('overview', 'No overview available.'),
            "",
        ]
        
        if tv.get('cast'):
            lines.append("Cast:")
            for c in tv['cast']:
                lines.append(f"  - {c.get('name', 'Unknown')} as {c.get('character', 'Unknown')}")
            lines.append("")
        
        if tv.get('seasons'):
            lines.append("Seasons:")
            for s in tv['seasons']:
                lines.append(f"  Season {s.get('season_number', 0)}: {s.get('name', 'Unknown')} ({s.get('episode_count', 0)} episodes)")
            lines.append("")
        
        if tv.get('episodes'):
            lines.append("Episodes:")
            current_season = -1
            for ep in tv['episodes']:
                if ep.get('season_number', 0) != current_season:
                    current_season = ep.get('season_number', 0)
                    lines.append(f"\n  Season {current_season}:")
                lines.append(f"    S{current_season:02d}E{ep.get('episode_number', 0):02d} - {ep.get('name', 'Unknown')} ({ep.get('air_date', 'N/A')})")
        
        if tv.get('poster_path'):
            lines.append(f"\nPoster: {tv['poster_path']}")
        
        return '\n'.join(lines)
    
    def export(self, data: Union[Movie, TVShow, List[Union[Movie, TVShow]]]) -> str:
        if isinstance(data, list):
            parts = []
            for item in data:
                prepared = self.prepare_data(item)
                if 'title' in prepared:  # Movie
                    parts.append(self._format_movie(prepared))
                else:  # TV
                    parts.append(self._format_tv(prepared))
            return '\n\n'.join(parts)
        else:
            prepared = self.prepare_data(data)
            if hasattr(data, 'title'):
                return self._format_movie(prepared)
            return self._format_tv(prepared)
    
    def get_file_extension(self) -> str:
        return "txt"
    
    def get_content_type(self) -> str:
        return "text/plain"
