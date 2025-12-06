"""
MovieFetchBot - Streamlit UI
A modern web application for fetching movie and TV data from TMDB
"""
import streamlit as st
import asyncio
import io
import zipfile
from datetime import datetime
import extra_streamlit_components as stx

# Import local modules
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from models.schemas import ExportFormat, ExportConfig, ContentType, UserCreate, UserLogin
from sources.tmdb import TMDBClient
from exporters import get_exporter
from utils.validators import sanitize_query, parse_batch_file, validate_export_filename
from utils.auth import create_user, authenticate_user, create_access_token, get_current_user

# Page config
st.set_page_config(
    page_title="MovieFetchBot",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# TMDB API Key
TMDB_API_KEY = "920654cb695ee99175e53d6da8dc2edf"

# Theme definitions
THEMES = {
    "Dark Neon": {
        "bg_primary": "#0f0f1a",
        "bg_secondary": "#1a1a2e",
        "bg_card": "rgba(255, 255, 255, 0.05)",
        "text_primary": "#ffffff",
        "text_secondary": "#b0b0b0",
        "accent": "#e94560",
        "accent_secondary": "#0f3460",
        "border": "rgba(255, 255, 255, 0.1)",
    },
    "Ocean Blue": {
        "bg_primary": "#0a192f",
        "bg_secondary": "#112240",
        "bg_card": "rgba(100, 255, 218, 0.05)",
        "text_primary": "#ccd6f6",
        "text_secondary": "#8892b0",
        "accent": "#64ffda",
        "accent_secondary": "#233554",
        "border": "rgba(100, 255, 218, 0.1)",
    },
    "Purple Dream": {
        "bg_primary": "#13111c",
        "bg_secondary": "#1d1a2f",
        "bg_card": "rgba(167, 139, 250, 0.05)",
        "text_primary": "#e2e8f0",
        "text_secondary": "#a0aec0",
        "accent": "#a78bfa",
        "accent_secondary": "#312e81",
        "border": "rgba(167, 139, 250, 0.1)",
    },
    "Light Mode": {
        "bg_primary": "#ffffff",
        "bg_secondary": "#f7f7f7",
        "bg_card": "rgba(0, 0, 0, 0.03)",
        "text_primary": "#1a1a1a",
        "text_secondary": "#666666",
        "accent": "#e94560",
        "accent_secondary": "#3b82f6",
        "border": "rgba(0, 0, 0, 0.1)",
    },
    "Midnight": {
        "bg_primary": "#000000",
        "bg_secondary": "#0d0d0d",
        "bg_card": "rgba(255, 255, 255, 0.03)",
        "text_primary": "#f0f0f0",
        "text_secondary": "#888888",
        "accent": "#ff6b6b",
        "accent_secondary": "#4ecdc4",
        "border": "rgba(255, 255, 255, 0.08)",
    },
}


def get_theme_css(theme_name: str) -> str:
    """Generate CSS for the selected theme"""
    t = THEMES.get(theme_name, THEMES["Dark Neon"])
    
    return f"""
<style>
    /* Root variables */
    :root {{
        --bg-primary: {t['bg_primary']};
        --bg-secondary: {t['bg_secondary']};
        --bg-card: {t['bg_card']};
        --text-primary: {t['text_primary']};
        --text-secondary: {t['text_secondary']};
        --accent: {t['accent']};
        --accent-secondary: {t['accent_secondary']};
        --border: {t['border']};
    }}
    
    /* Main app background */
    .stApp {{
        background: linear-gradient(135deg, {t['bg_primary']} 0%, {t['bg_secondary']} 100%);
    }}
    
    /* Hide deploy button only (keep menu for sidebar toggle) */
    .stDeployButton,
    [data-testid="stToolbar"] button[kind="header"] {{
        display: none !important;
        visibility: hidden !important;
    }}
    
    /* Sidebar styling */
    section[data-testid="stSidebar"] {{
        background: {t['bg_secondary']} !important;
    }}
    
    section[data-testid="stSidebar"] * {{
        color: {t['text_primary']} !important;
    }}
    
    /* All text elements */
    .stApp, .stApp p, .stApp span, .stApp div, .stApp label {{
        color: {t['text_primary']} !important;
    }}
    
    h1, h2, h3, h4, h5, h6 {{
        color: {t['text_primary']} !important;
    }}
    
    .stMarkdown, .stMarkdown p {{
        color: {t['text_primary']} !important;
    }}
    
    /* Caption/secondary text */
    .stCaption, small, .stApp small {{
        color: {t['text_secondary']} !important;
    }}
    
    /* Header styling */
    .main-header {{
        background: linear-gradient(90deg, {t['accent']}, {t['accent_secondary']});
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        font-size: 2.5rem;
        font-weight: 800;
        text-align: center;
        padding: 1rem 0;
        margin-bottom: 0.5rem;
    }}
    
    .subtitle {{
        text-align: center;
        color: {t['text_secondary']} !important;
        margin-bottom: 1rem;
    }}
    
    /* Button styling */
    .stButton > button {{
        background: linear-gradient(135deg, {t['accent']}, {t['accent_secondary']}) !important;
        color: white !important;
        border: none !important;
        border-radius: 12px !important;
        padding: 0.5rem 1.5rem !important;
        font-weight: 600 !important;
        transition: all 0.3s ease !important;
    }}
    
    .stButton > button:hover {{
        transform: scale(1.02);
        box-shadow: 0 8px 25px {t['accent']}40;
    }}
    
    /* Download button */
    .stDownloadButton > button {{
        background: linear-gradient(135deg, {t['accent']}, {t['accent_secondary']}) !important;
        color: white !important;
        border: none !important;
        border-radius: 12px !important;
    }}
    
    /* Input styling */
    .stTextInput > div > div > input {{
        background: {t['bg_card']} !important;
        border: 1px solid {t['border']} !important;
        border-radius: 10px !important;
        color: {t['text_primary']} !important;
        padding: 0.5rem 1rem !important;
    }}
    
    .stTextInput > div > div > input::placeholder {{
        color: {t['text_secondary']} !important;
    }}
    
    /* Selectbox styling */
    .stSelectbox > div > div {{
        background: {t['bg_card']} !important;
        border-radius: 10px !important;
    }}
    
    .stSelectbox > div > div > div {{
        color: {t['text_primary']} !important;
    }}
    
    /* Radio buttons */
    .stRadio > div {{
        color: {t['text_primary']} !important;
    }}
    
    .stRadio label {{
        color: {t['text_primary']} !important;
    }}
    
    /* Checkbox */
    .stCheckbox label {{
        color: {t['text_primary']} !important;
    }}
    
    /* Metric styling */
    [data-testid="stMetricValue"] {{
        color: {t['accent']} !important;
        font-weight: 700;
    }}
    
    [data-testid="stMetricLabel"] {{
        color: {t['text_secondary']} !important;
    }}
    
    /* Expander */
    .streamlit-expanderHeader {{
        background: {t['bg_card']} !important;
        border-radius: 10px !important;
        color: {t['text_primary']} !important;
    }}
    
    .streamlit-expanderContent {{
        background: {t['bg_card']} !important;
        border-radius: 0 0 10px 10px !important;
    }}
    
    /* Cards */
    .info-card {{
        background: {t['bg_card']};
        border-radius: 12px;
        padding: 1rem;
        margin: 0.5rem 0;
        border: 1px solid {t['border']};
    }}
    
    /* Episode list */
    .episode-item {{
        background: {t['bg_card']};
        padding: 0.75rem 1rem;
        border-radius: 8px;
        margin: 0.25rem 0;
        border-left: 3px solid {t['accent']};
        color: {t['text_primary']} !important;
    }}
    
    .episode-item strong {{
        color: {t['text_primary']} !important;
    }}
    
    .episode-item small {{
        color: {t['text_secondary']} !important;
    }}
    
    /* Welcome card */
    .welcome-card {{
        text-align: center;
        padding: 2rem;
        background: {t['bg_card']};
        border-radius: 20px;
        margin-top: 1rem;
        border: 1px solid {t['border']};
    }}
    
    .welcome-card h2, .welcome-card h3 {{
        color: {t['text_primary']} !important;
    }}
    
    .welcome-card p {{
        color: {t['text_secondary']} !important;
    }}
    
    /* Feature cards */
    .feature-grid {{
        display: flex;
        justify-content: center;
        gap: 1.5rem;
        flex-wrap: wrap;
        margin-top: 1rem;
    }}
    
    .feature-item {{
        background: {t['bg_secondary']};
        padding: 1rem 1.5rem;
        border-radius: 12px;
        border: 1px solid {t['border']};
        text-align: center;
        min-width: 120px;
    }}
    
    .feature-item h3 {{
        color: {t['accent']} !important;
        margin: 0;
    }}
    
    .feature-item p {{
        color: {t['text_secondary']} !important;
        margin: 0.5rem 0 0 0;
        font-size: 0.9rem;
    }}
    
    /* Info/Warning boxes - ensure text visibility */
    .stAlert > div {{
        color: {t['text_primary']} !important;
    }}
    
    /* Code blocks */
    .stCodeBlock {{
        background: {t['bg_secondary']} !important;
    }}
    
    code {{
        color: {t['accent']} !important;
    }}
    
    /* File uploader */
    .stFileUploader > div {{
        background: {t['bg_card']} !important;
        border-radius: 10px !important;
    }}
    
    /* Spinner */
    .stSpinner > div {{
        border-top-color: {t['accent']} !important;
    }}
    
    /* Progress bar */
    .stProgress > div > div {{
        background-color: {t['accent']} !important;
    }}
    
    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {{
        background: {t['bg_card']};
        border-radius: 10px;
    }}
    
    .stTabs [data-baseweb="tab"] {{
        color: {t['text_primary']} !important;
    }}
    
    /* Image captions */
    .stImage > div > div > p {{
        color: {t['text_secondary']} !important;
    }}
    
    /* Hide Streamlit branding */
    #MainMenu {{visibility: hidden;}}
    footer {{visibility: hidden;}}
    
    /* Scrollbar styling */
    ::-webkit-scrollbar {{
        width: 8px;
        height: 8px;
    }}
    
    ::-webkit-scrollbar-track {{
        background: {t['bg_primary']};
    }}
    
    ::-webkit-scrollbar-thumb {{
        background: {t['accent']};
        border-radius: 4px;
    }}
</style>
"""


@st.cache_resource
def get_cookie_manager():
    """Get or create cookie manager"""
    return stx.CookieManager()


def init_session_state():
    """Initialize session state variables"""
    defaults = {
        'authenticated': False,
        'user': None,
        'token': None,
        'search_results': None,
        'selected_item': None,
        'fetched_data': None,
        'theme': 'Dark Neon',
        'fetch_history': [],
        'show_history': False,
        'session_restored': False,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def restore_session_from_cookie():
    """Restore user session from cookie if available"""
    if st.session_state.session_restored or st.session_state.authenticated:
        return
    
    cookie_manager = get_cookie_manager()
    saved_token = cookie_manager.get("moviefetchbot_token")
    
    if saved_token:
        try:
            user = get_current_user(saved_token)
            if user:
                st.session_state.authenticated = True
                st.session_state.token = saved_token
                st.session_state.user = user
                load_user_history()
        except:
            # Invalid token, clear it
            cookie_manager.delete("moviefetchbot_token")
    
    st.session_state.session_restored = True


def save_session_to_cookie(token: str):
    """Save session token to cookie"""
    cookie_manager = get_cookie_manager()
    cookie_manager.set("moviefetchbot_token", token, expires_at=datetime.now().replace(hour=23, minute=59, second=59) + __import__('datetime').timedelta(days=7))


def clear_session_cookie():
    """Clear session cookie on logout"""
    cookie_manager = get_cookie_manager()
    cookie_manager.delete("moviefetchbot_token")




def run_async(coro):
    """Run async function in sync context"""
    try:
        loop = asyncio.get_event_loop()
        if loop.is_closed():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    return loop.run_until_complete(coro)


def render_auth_section():
    """Render authentication section in sidebar"""
    st.sidebar.markdown("### 🔐 Account")
    
    if st.session_state.authenticated:
        st.sidebar.success(f"Logged in as **{st.session_state.user.username}**")
        if st.sidebar.button("🚪 Logout", use_container_width=True):
            st.session_state.authenticated = False
            st.session_state.user = None
            st.session_state.token = None
            st.session_state.fetch_history = []
            clear_session_cookie()  # Clear the cookie
            st.rerun()
    else:
        auth_tab = st.sidebar.radio("Action", ["Login", "Register"], horizontal=True)
        
        if auth_tab == "Login":
            with st.sidebar.form("login_form"):
                username = st.text_input("Username")
                password = st.text_input("Password", type="password")
                submit = st.form_submit_button("🔑 Login", use_container_width=True)
                
                if submit:
                    user = authenticate_user(username, password)
                    if user:
                        token = create_access_token({"sub": user["username"]})
                        st.session_state.authenticated = True
                        st.session_state.token = token
                        st.session_state.user = get_current_user(token)
                        save_session_to_cookie(token)  # Save token to cookie
                        load_user_history()
                        st.rerun()
                    else:
                        st.error("Invalid credentials")
        else:
            with st.sidebar.form("register_form"):
                username = st.text_input("Username")
                email = st.text_input("Email")
                password = st.text_input("Password", type="password")
                submit = st.form_submit_button("✨ Register", use_container_width=True)
                
                if submit:
                    try:
                        user = create_user(UserCreate(username=username, email=email, password=password))
                        token = create_access_token({"sub": user.username})
                        st.session_state.authenticated = True
                        st.session_state.token = token
                        st.session_state.user = user
                        save_session_to_cookie(token)  # Save token to cookie
                        load_user_history()
                        st.rerun()
                    except ValueError as e:
                        st.error(str(e))


def render_search_section():
    """Render search section"""
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 🔍 Search")
    
    content_type = st.sidebar.radio(
        "Content Type",
        ["Movies & TV", "Movies Only", "TV Only"],
        horizontal=True
    )
    
    type_map = {
        "Movies & TV": "multi",
        "Movies Only": "movie",
        "TV Only": "tv"
    }
    
    search_query = st.sidebar.text_input("Search for movies or TV shows...", placeholder="e.g., The Matrix")
    
    if st.sidebar.button("🔎 Search", use_container_width=True):
        if search_query:
            with st.spinner("Searching..."):
                client = TMDBClient(TMDB_API_KEY)
                query = sanitize_query(search_query)
                results = run_async(client.search(query, type_map[content_type]))
                run_async(client.close())
                st.session_state.search_results = results
                st.session_state.selected_item = None
                st.session_state.fetched_data = None
    
    return content_type


def render_export_options():
    """Render export options"""
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 📁 Export Options")
    
    export_format = st.sidebar.selectbox(
        "Format",
        [f.value.upper() for f in ExportFormat],
        index=0
    )
    
    col1, col2 = st.sidebar.columns(2)
    with col1:
        include_cast = st.checkbox("Include Cast", value=True)
    with col2:
        include_images = st.checkbox("Include Images", value=True)
    
    include_episodes = st.sidebar.checkbox("Include Episodes (TV)", value=True)
    
    return ExportFormat(export_format.lower()), include_cast, include_episodes, include_images


def render_search_results():
    """Render search results in main area"""
    if not st.session_state.search_results:
        return
    
    results = st.session_state.search_results
    
    if not results.results:
        st.warning("No results found. Try a different search term.")
        return
    
    st.markdown(f"### 🎯 Found {results.total_results} results")
    
    # Display results in a grid
    cols = st.columns(4)
    for idx, result in enumerate(results.results[:12]):
        with cols[idx % 4]:
            with st.container():
                # Poster
                if result.poster_path:
                    st.image(result.poster_path, use_container_width=True)
                else:
                    st.markdown("""
                    <div style="background: rgba(255,255,255,0.1); height: 200px; border-radius: 8px; 
                    display: flex; align-items: center; justify-content: center; color: #888;">
                    No Poster
                    </div>
                    """, unsafe_allow_html=True)
                
                # Title
                st.markdown(f"**{result.title}**")
                st.caption(f"{'🎬 Movie' if result.media_type == ContentType.MOVIE else '📺 TV'} | {result.release_date or 'N/A'}")
                
                # Fetch button
                if st.button("Fetch Details", key=f"fetch_{result.id}_{idx}", use_container_width=True):
                    st.session_state.selected_item = result
                    with st.spinner("Fetching details..."):
                        client = TMDBClient(TMDB_API_KEY)
                        if result.media_type == ContentType.MOVIE:
                            data = run_async(client.get_movie(result.id))
                            is_movie = True
                        else:
                            data = run_async(client.get_tv_show(result.id, True))
                            is_movie = False
                        run_async(client.close())
                        st.session_state.fetched_data = data
                        # Add to history
                        add_to_history(data, is_movie)
                    st.rerun()


def render_detail_view(export_format, include_cast, include_episodes, include_images):
    """Render detailed view of fetched item with enhanced UI"""
    data = st.session_state.fetched_data
    if not data:
        return
    
    is_movie = hasattr(data, 'title')
    title = data.title if is_movie else data.name
    
    # Back button
    col_back, col_title = st.columns([1, 5])
    with col_back:
        if st.button("← Back"):
            st.session_state.fetched_data = None
            st.session_state.selected_item = None
            st.rerun()
    
    # Backdrop header
    if data.backdrop_path:
        st.markdown(f"""
        <div style="position: relative; margin: -1rem -1rem 1rem -1rem; border-radius: 12px; overflow: hidden;">
            <img src="{data.backdrop_path}" style="width: 100%; height: 300px; object-fit: cover; filter: brightness(0.6);">
            <div style="position: absolute; bottom: 20px; left: 20px; color: white;">
                <h1 style="margin: 0; font-size: 2.5rem; text-shadow: 2px 2px 8px rgba(0,0,0,0.8);">
                    {'🎬' if is_movie else '📺'} {title}
                </h1>
                {f'<p style="margin: 5px 0; font-style: italic; text-shadow: 1px 1px 4px rgba(0,0,0,0.8);">"{data.tagline}"</p>' if data.tagline else ''}
            </div>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f"## {'🎬' if is_movie else '📺'} {title}")
        if data.tagline:
            st.markdown(f"*\"{data.tagline}\"*")
    
    # Main layout: poster + info
    col1, col2 = st.columns([1, 3])
    
    with col1:
        if data.poster_path:
            st.image(data.poster_path, use_container_width=True)
        
        # Quick stats
        st.markdown("#### 📊 Quick Stats")
        if data.vote_average:
            st.metric("Rating", f"⭐ {data.vote_average:.1f}/10")
        if is_movie:
            if data.runtime:
                st.metric("Runtime", f"{data.runtime} min")
        else:
            if data.number_of_episodes:
                st.metric("Episodes", data.number_of_episodes)
            if data.number_of_seasons:
                st.metric("Seasons", data.number_of_seasons)
        
        # Export
        st.markdown("#### 📥 Export")
        config = ExportConfig(
            format=export_format,
            include_cast=include_cast,
            include_episodes=include_episodes,
            include_images=include_images
        )
        exporter = get_exporter(export_format, config)
        content = exporter.export(data)
        filename = validate_export_filename(f"{title}_{datetime.now().strftime('%Y%m%d')}")
        
        st.download_button(
            label=f"📥 {export_format.value.upper()}",
            data=content,
            file_name=f"{filename}.{exporter.get_file_extension()}",
            mime=exporter.get_content_type(),
            use_container_width=True
        )
    
    with col2:
        # Info tabs
        if is_movie:
            tabs = st.tabs(["📝 Overview", "🎭 Cast & Crew", "🎬 Production", "🎥 Videos"])
        else:
            tabs = st.tabs(["📝 Overview", "🎭 Cast & Crew", "📺 Episodes", "🎬 Production", "🎥 Videos"])
        
        # Overview Tab
        with tabs[0]:
            # Key info
            info_cols = st.columns(4)
            with info_cols[0]:
                if is_movie:
                    st.markdown(f"**Release:** {data.release_date or 'N/A'}")
                else:
                    st.markdown(f"**First Aired:** {data.first_air_date or 'N/A'}")
            with info_cols[1]:
                st.markdown(f"**Status:** {data.status or 'N/A'}")
            with info_cols[2]:
                lang = getattr(data, 'original_language', None)
                st.markdown(f"**Language:** {lang.upper() if lang else 'N/A'}")
            with info_cols[3]:
                if is_movie and data.imdb_id:
                    st.markdown(f"**IMDB:** [{data.imdb_id}](https://imdb.com/title/{data.imdb_id})")
                elif not is_movie and data.networks:
                    st.markdown(f"**Network:** {data.networks[0].name}")
            
            # Genres
            if data.genres:
                genre_tags = " ".join([f"`{g.name}`" for g in data.genres])
                st.markdown(f"**Genres:** {genre_tags}")
            
            st.markdown("---")
            st.markdown("### Overview")
            st.write(data.overview or "No overview available.")
            
            # Box Office for movies
            if is_movie and (data.budget or data.revenue):
                st.markdown("### 💰 Box Office")
                box_cols = st.columns(2)
                with box_cols[0]:
                    if data.budget and data.budget > 0:
                        st.metric("Budget", f"${data.budget:,}")
                with box_cols[1]:
                    if data.revenue and data.revenue > 0:
                        st.metric("Revenue", f"${data.revenue:,}")
            
            # TV Show specific info
            if not is_movie:
                if data.created_by:
                    st.markdown(f"**Created by:** {', '.join(data.created_by)}")
                if data.last_air_date:
                    st.markdown(f"**Last Aired:** {data.last_air_date}")
                if hasattr(data, 'in_production') and data.in_production is not None:
                    st.markdown(f"**In Production:** {'Yes' if data.in_production else 'No'}")
        
        # Cast & Crew Tab
        with tabs[1]:
            if data.cast and include_cast:
                st.markdown("### 🎭 Main Cast")
                cast_cols = st.columns(5)
                for idx, member in enumerate(data.cast[:15]):
                    with cast_cols[idx % 5]:
                        if member.profile_path:
                            st.image(member.profile_path, width=100)
                        else:
                            st.markdown("👤")
                        st.markdown(f"**{member.name}**")
                        st.caption(f"as {member.character}")
            
            # Crew (directors, writers)
            if hasattr(data, 'crew') and data.crew:
                st.markdown("### 🎬 Key Crew")
                for crew_member in data.crew[:8]:
                    st.markdown(f"• **{crew_member.name}** - {crew_member.job}")
        
        # Episodes Tab (TV only)
        if not is_movie:
            with tabs[2]:
                if data.episodes and include_episodes:
                    # Group by season
                    seasons_data = {}
                    for ep in data.episodes:
                        if ep.season_number not in seasons_data:
                            seasons_data[ep.season_number] = []
                        seasons_data[ep.season_number].append(ep)
                    
                    st.markdown(f"### 📺 All Episodes ({len(data.episodes)} total)")
                    
                    for season_num in sorted(seasons_data.keys()):
                        with st.expander(f"**Season {season_num}** ({len(seasons_data[season_num])} episodes)", expanded=season_num == 1):
                            for ep in seasons_data[season_num]:
                                # Episode card with thumbnail
                                ep_cols = st.columns([1, 4])
                                with ep_cols[0]:
                                    if ep.still_path:
                                        st.image(ep.still_path, use_container_width=True)
                                    else:
                                        st.markdown("🎬")
                                with ep_cols[1]:
                                    st.markdown(f"**E{ep.episode_number:02d}: {ep.name}**")
                                    info_parts = []
                                    if ep.air_date:
                                        info_parts.append(f"📅 {ep.air_date}")
                                    if ep.runtime:
                                        info_parts.append(f"⏱️ {ep.runtime}m")
                                    if ep.vote_average:
                                        info_parts.append(f"⭐ {ep.vote_average:.1f}")
                                    st.caption(" | ".join(info_parts))
                                    if ep.overview:
                                        st.caption(ep.overview[:150] + "..." if len(ep.overview or "") > 150 else ep.overview)
                                st.markdown("---")
                else:
                    st.info("Episode data not available or not included in fetch.")
        
        # Production Tab
        prod_tab_idx = 3 if not is_movie else 2
        with tabs[prod_tab_idx]:
            if hasattr(data, 'production_companies') and data.production_companies:
                st.markdown("### 🏢 Production Companies")
                for company in data.production_companies:
                    if company.logo_path:
                        st.image(company.logo_path, width=100)
                    st.markdown(f"• **{company.name}** {f'({company.origin_country})' if company.origin_country else ''}")
            
            if hasattr(data, 'production_countries') and data.production_countries:
                st.markdown("### 🌍 Countries")
                st.write(", ".join(data.production_countries))
            
            if hasattr(data, 'spoken_languages') and data.spoken_languages:
                st.markdown("### 🗣️ Languages")
                st.write(", ".join(data.spoken_languages))
            
            if not is_movie and hasattr(data, 'networks') and data.networks:
                st.markdown("### 📡 Networks")
                for network in data.networks:
                    if network.logo_path:
                        st.image(network.logo_path, width=80)
                    st.markdown(f"• **{network.name}**")
            
            if data.homepage:
                st.markdown(f"### 🔗 [Official Website]({data.homepage})")
        
        # Videos Tab
        video_tab_idx = 4 if not is_movie else 3
        with tabs[video_tab_idx]:
            if hasattr(data, 'videos') and data.videos:
                st.markdown("### 🎥 Videos & Trailers")
                for video in data.videos[:4]:
                    if video.site == "YouTube":
                        st.markdown(f"**{video.name}** ({video.type})")
                        st.markdown(f"[▶️ Watch on YouTube](https://www.youtube.com/watch?v={video.key})")
                        st.markdown("---")
            else:
                st.info("No videos available.")


def add_to_history(data, is_movie: bool):
    """Add fetched item to history and save to file"""
    from datetime import datetime
    import uuid
    
    title = data.title if is_movie else data.name
    history_item = {
        'id': str(uuid.uuid4()),
        'title': title,
        'media_type': 'movie' if is_movie else 'tv',
        'tmdb_id': data.id,
        'poster_path': data.poster_path,
        'fetched_at': datetime.now().strftime('%Y-%m-%d %H:%M'),
    }
    
    # Add to front, limit to 50 items
    st.session_state.fetch_history.insert(0, history_item)
    st.session_state.fetch_history = st.session_state.fetch_history[:50]
    
    # Save to file if logged in
    save_user_history()


def get_history_file_path():
    """Get path to history file for current user"""
    from pathlib import Path
    data_dir = Path(__file__).parent / "data"
    data_dir.mkdir(exist_ok=True)
    return data_dir / "history.json"


def load_all_history() -> dict:
    """Load all history from file"""
    import json
    history_file = get_history_file_path()
    if history_file.exists():
        try:
            return json.loads(history_file.read_text())
        except:
            return {}
    return {}


def save_user_history():
    """Save current user's history to file"""
    import json
    if not st.session_state.authenticated or not st.session_state.user:
        return
    
    username = st.session_state.user.username
    all_history = load_all_history()
    all_history[username] = st.session_state.fetch_history
    
    history_file = get_history_file_path()
    history_file.write_text(json.dumps(all_history, indent=2))


def load_user_history():
    """Load current user's history from file into session state"""
    if not st.session_state.authenticated or not st.session_state.user:
        return
    
    username = st.session_state.user.username
    all_history = load_all_history()
    st.session_state.fetch_history = all_history.get(username, [])


def render_history_section():
    """Render fetch history in sidebar"""
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 📜 Fetch History")
    
    if not st.session_state.authenticated:
        st.sidebar.caption("Login to see history")
        return
    
    if not st.session_state.fetch_history:
        st.sidebar.caption("No items fetched yet")
        return
    
    for item in st.session_state.fetch_history[:5]:
        col1, col2 = st.sidebar.columns([1, 3])
        with col1:
            if item.get('poster_path'):
                st.image(item['poster_path'], width=40)
            else:
                st.markdown("🎬" if item['media_type'] == 'movie' else "📺")
        with col2:
            st.caption(f"**{item['title'][:20]}...**" if len(item['title']) > 20 else f"**{item['title']}**")
            st.caption(f"{item['fetched_at']}")
    
    if len(st.session_state.fetch_history) > 5:
        st.sidebar.caption(f"+{len(st.session_state.fetch_history) - 5} more items")
    
    # Clear history button
    if st.sidebar.button("🗑️ Clear History", use_container_width=True):
        st.session_state.fetch_history = []
        save_user_history()
        st.rerun()



def render_batch_section():
    """Render batch upload section"""
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 📤 Batch Fetch")
    
    if not st.session_state.authenticated:
        st.sidebar.info("🔒 Login to use batch fetch")
        return
    
    # Input method selection
    input_method = st.sidebar.radio("Input Method", ["Text", "File"], horizontal=True)
    
    queries = []
    
    if input_method == "Text":
        # Direct text input
        batch_text = st.sidebar.text_area(
            "Enter titles (one per line)",
            placeholder="The Matrix\nBreaking Bad\nInception\nGame of Thrones",
            height=100,
            key="batch_text"
        )
        if batch_text:
            queries = [q.strip() for q in batch_text.strip().split('\n') if q.strip()]
    else:
        # File upload
        uploaded_file = st.sidebar.file_uploader(
            "Upload titles file",
            type=['txt', 'csv'],
            help="Text file with titles, one per line"
        )
        if uploaded_file:
            content = uploaded_file.read().decode('utf-8')
            queries = parse_batch_file(content)
    
    if queries:
        st.sidebar.caption(f"📋 {len(queries)} titles ready")
    
    # Options
    batch_type = st.sidebar.radio("Type", ["Movies", "TV Shows", "Both"], horizontal=True, key="batch_type")
    batch_format = st.sidebar.selectbox("Export Format", ["JSON", "CSV", "TXT"], key="batch_format")
    
    # Process button - always visible
    fetch_btn = st.sidebar.button("🚀 Fetch All", use_container_width=True, disabled=not queries)
    
    if not queries:
        st.sidebar.caption("↑ Enter titles above first")
    
    if fetch_btn and queries:
        st.session_state.batch_results = []
        st.session_state.batch_processing = True
        
        progress = st.progress(0)
        status = st.empty()
        
        results = []
        failed = []
        client = TMDBClient(TMDB_API_KEY)
        
        for idx, query in enumerate(queries):
            status.text(f"⏳ Fetching: {query}")
            progress.progress((idx + 1) / len(queries))
            
            try:
                # Determine search type
                if batch_type == "Movies":
                    search_type = "movie"
                elif batch_type == "TV Shows":
                    search_type = "tv"
                else:
                    search_type = "multi"
                
                search_results = run_async(client.search(query, search_type))
                
                if search_results.results:
                    result = search_results.results[0]
                    if result.media_type == ContentType.MOVIE:
                        data = run_async(client.get_movie(result.id))
                        is_movie = True
                    else:
                        data = run_async(client.get_tv_show(result.id, False))  # Skip episodes for speed
                        is_movie = False
                    results.append({'data': data, 'is_movie': is_movie, 'query': query})
                    add_to_history(data, is_movie)
                else:
                    failed.append(query)
            except Exception as e:
                failed.append(query)
        
        run_async(client.close())
        progress.empty()
        status.empty()
        
        if results:
            st.session_state.batch_results = results
            st.session_state.batch_failed = failed
            st.session_state.batch_export_format = batch_format  # Use different key
            st.success(f"✅ Fetched {len(results)}/{len(queries)} items")
            if failed:
                st.warning(f"⚠️ Failed: {', '.join(failed[:5])}" + ("..." if len(failed) > 5 else ""))
            st.rerun()


def render_batch_results():
    """Render batch results in main area"""
    if not hasattr(st.session_state, 'batch_results') or not st.session_state.batch_results:
        return
    
    results = st.session_state.batch_results
    batch_format = getattr(st.session_state, 'batch_export_format', 'JSON')
    
    st.markdown("## 📦 Batch Results")
    st.markdown(f"**{len(results)} items fetched** | Format: {batch_format}")
    
    # Clear button
    col1, col2 = st.columns([1, 3])
    with col1:
        if st.button("🗑️ Clear Results"):
            st.session_state.batch_results = []
            st.rerun()
    
    # Download all button
    with col2:
        fmt = ExportFormat(batch_format.lower())
        config = ExportConfig(format=fmt, include_cast=True, include_episodes=False)
        exporter = get_exporter(fmt, config)
        
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
            for item in results:
                data = item['data']
                name = data.title if item['is_movie'] else data.name
                content = exporter.export(data)
                filename = validate_export_filename(f"{name}.{exporter.get_file_extension()}")
                zf.writestr(filename, content)
        
        zip_buffer.seek(0)
        
        st.download_button(
            label=f"📥 Download All ({batch_format} ZIP)",
            data=zip_buffer,
            file_name=f"batch_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip",
            mime="application/zip"
        )
    
    st.markdown("---")
    
    # Display results grid
    cols = st.columns(4)
    for idx, item in enumerate(results):
        data = item['data']
        is_movie = item['is_movie']
        
        with cols[idx % 4]:
            if data.poster_path:
                st.image(data.poster_path, use_container_width=True)
            
            title = data.title if is_movie else data.name
            st.markdown(f"**{title[:25]}{'...' if len(title) > 25 else ''}**")
            st.caption(f"{'🎬 Movie' if is_movie else '📺 TV'} | ⭐ {data.vote_average or 'N/A'}")
            
            # Individual download
            content = exporter.export(data)
            st.download_button(
                label="📥",
                data=content,
                file_name=f"{validate_export_filename(title)}.{exporter.get_file_extension()}",
                mime=exporter.get_content_type(),
                key=f"dl_{idx}",
                use_container_width=True
            )


def render_preview_section(export_format, include_cast, include_episodes, include_images):
    """Render data preview section"""
    if not st.session_state.fetched_data:
        return
    
    data = st.session_state.fetched_data
    
    with st.expander("🔍 Preview Export Data"):
        config = ExportConfig(
            format=export_format,
            include_cast=include_cast,
            include_episodes=include_episodes,
            include_images=include_images
        )
        exporter = get_exporter(export_format, config)
        content = exporter.export(data)
        
        # Show preview (limited)
        preview = content[:3000] + ("..." if len(content) > 3000 else "")
        st.code(preview, language=export_format.value if export_format.value != "txt" else None)


def main():
    """Main application"""
    init_session_state()
    restore_session_from_cookie()  # Restore login from cookie on refresh
    
    # Theme selector at top of sidebar
    st.sidebar.markdown("### 🎨 Theme")
    selected_theme = st.sidebar.selectbox(
        "Choose theme",
        list(THEMES.keys()),
        index=list(THEMES.keys()).index(st.session_state.theme),
        key="theme_selector"
    )
    
    # Update theme in session state
    if selected_theme != st.session_state.theme:
        st.session_state.theme = selected_theme
        st.rerun()
    
    # Apply theme CSS
    st.markdown(get_theme_css(st.session_state.theme), unsafe_allow_html=True)
    
    # Header
    st.markdown('<h1 class="main-header">🎬 MovieFetchBot</h1>', unsafe_allow_html=True)
    st.markdown('<p class="subtitle">Fetch movie and TV data from TMDB with ease</p>', unsafe_allow_html=True)
    
    # Sidebar sections
    render_auth_section()
    content_type = render_search_section()
    export_format, include_cast, include_episodes, include_images = render_export_options()
    render_batch_section()
    render_history_section()
    
    # Main content
    # Check for batch results first
    if hasattr(st.session_state, 'batch_results') and st.session_state.batch_results:
        render_batch_results()
    elif st.session_state.fetched_data:
        render_detail_view(export_format, include_cast, include_episodes, include_images)
        render_preview_section(export_format, include_cast, include_episodes, include_images)
    elif st.session_state.search_results:
        render_search_results()
    else:
        # Welcome message with theme-aware styling
        st.markdown("""
        <div class="welcome-card">
            <h2>👋 Welcome to MovieFetchBot!</h2>
            <p>Search for any movie or TV show to get detailed information and export in multiple formats.</p>
            <div class="feature-grid">
                <div class="feature-item">
                    <h3>🔍</h3>
                    <p>Search movies & TV</p>
                </div>
                <div class="feature-item">
                    <h3>📊</h3>
                    <p>View full details</p>
                </div>
                <div class="feature-item">
                    <h3>📥</h3>
                    <p>Export data</p>
                </div>
                <div class="feature-item">
                    <h3>📤</h3>
                    <p>Batch process</p>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Quick start tips
        st.markdown("### 🚀 Quick Start")
        col1, col2 = st.columns(2)
        with col1:
            st.info("**Step 1:** Use the search bar in the sidebar to find a movie or TV show")
        with col2:
            st.info("**Step 2:** Click 'Fetch Details' on any result to see full information")


if __name__ == "__main__":
    main()

