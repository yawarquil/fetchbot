"""
CSV Exporter
"""
import csv
import io
from typing import Union, List
from models.schemas import Movie, TVShow
from .base import BaseExporter


class CSVExporter(BaseExporter):
    """Export data to CSV format"""
    
    def _movie_to_row(self, movie: dict) -> dict:
        return {
            'id': movie.get('id', ''),
            'title': movie.get('title', ''),
            'original_title': movie.get('original_title', ''),
            'release_date': movie.get('release_date', ''),
            'runtime': movie.get('runtime', ''),
            'genres': ', '.join(g.get('name', '') for g in movie.get('genres', [])),
            'vote_average': movie.get('vote_average', ''),
            'vote_count': movie.get('vote_count', ''),
            'popularity': movie.get('popularity', ''),
            'overview': movie.get('overview', ''),
            'tagline': movie.get('tagline', ''),
            'status': movie.get('status', ''),
            'budget': movie.get('budget', ''),
            'revenue': movie.get('revenue', ''),
            'poster_path': movie.get('poster_path', ''),
            'cast': ', '.join(c.get('name', '') for c in movie.get('cast', []))
        }
    
    def _tv_to_row(self, tv: dict) -> dict:
        return {
            'id': tv.get('id', ''),
            'name': tv.get('name', ''),
            'original_name': tv.get('original_name', ''),
            'first_air_date': tv.get('first_air_date', ''),
            'last_air_date': tv.get('last_air_date', ''),
            'number_of_seasons': tv.get('number_of_seasons', ''),
            'number_of_episodes': tv.get('number_of_episodes', ''),
            'genres': ', '.join(g.get('name', '') for g in tv.get('genres', [])),
            'vote_average': tv.get('vote_average', ''),
            'vote_count': tv.get('vote_count', ''),
            'popularity': tv.get('popularity', ''),
            'overview': tv.get('overview', ''),
            'tagline': tv.get('tagline', ''),
            'status': tv.get('status', ''),
            'poster_path': tv.get('poster_path', ''),
            'cast': ', '.join(c.get('name', '') for c in tv.get('cast', []))
        }
    
    def _episodes_to_csv(self, tv: dict) -> str:
        """Generate separate CSV for episodes"""
        if not tv.get('episodes'):
            return ""
        
        output = io.StringIO()
        fieldnames = ['tv_id', 'tv_name', 'season_number', 'episode_number', 'name', 'air_date', 'runtime', 'vote_average', 'overview']
        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()
        
        for ep in tv['episodes']:
            writer.writerow({
                'tv_id': tv.get('id', ''),
                'tv_name': tv.get('name', ''),
                'season_number': ep.get('season_number', ''),
                'episode_number': ep.get('episode_number', ''),
                'name': ep.get('name', ''),
                'air_date': ep.get('air_date', ''),
                'runtime': ep.get('runtime', ''),
                'vote_average': ep.get('vote_average', ''),
                'overview': ep.get('overview', '')
            })
        
        return output.getvalue()
    
    def export(self, data: Union[Movie, TVShow, List[Union[Movie, TVShow]]]) -> str:
        output = io.StringIO()
        
        if isinstance(data, list):
            if not data:
                return ""
            
            # Check if mixed or single type
            is_movie = hasattr(data[0], 'title')
            
            if is_movie:
                fieldnames = ['id', 'title', 'original_title', 'release_date', 'runtime', 'genres', 'vote_average', 'vote_count', 'popularity', 'overview', 'tagline', 'status', 'budget', 'revenue', 'poster_path', 'cast']
            else:
                fieldnames = ['id', 'name', 'original_name', 'first_air_date', 'last_air_date', 'number_of_seasons', 'number_of_episodes', 'genres', 'vote_average', 'vote_count', 'popularity', 'overview', 'tagline', 'status', 'poster_path', 'cast']
            
            writer = csv.DictWriter(output, fieldnames=fieldnames)
            writer.writeheader()
            
            for item in data:
                prepared = self.prepare_data(item)
                if is_movie:
                    writer.writerow(self._movie_to_row(prepared))
                else:
                    writer.writerow(self._tv_to_row(prepared))
        else:
            prepared = self.prepare_data(data)
            is_movie = hasattr(data, 'title')
            
            if is_movie:
                fieldnames = ['id', 'title', 'original_title', 'release_date', 'runtime', 'genres', 'vote_average', 'vote_count', 'popularity', 'overview', 'tagline', 'status', 'budget', 'revenue', 'poster_path', 'cast']
                writer = csv.DictWriter(output, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerow(self._movie_to_row(prepared))
            else:
                fieldnames = ['id', 'name', 'original_name', 'first_air_date', 'last_air_date', 'number_of_seasons', 'number_of_episodes', 'genres', 'vote_average', 'vote_count', 'popularity', 'overview', 'tagline', 'status', 'poster_path', 'cast']
                writer = csv.DictWriter(output, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerow(self._tv_to_row(prepared))
                
                # Add episodes section if present
                if prepared.get('episodes'):
                    output.write("\n\n--- EPISODES ---\n")
                    output.write(self._episodes_to_csv(prepared))
        
        return output.getvalue()
    
    def get_file_extension(self) -> str:
        return "csv"
    
    def get_content_type(self) -> str:
        return "text/csv"
