# PICKLEBALL TOURNAMENT PRO - With QR Check-in
# Home → Format Selection → Player Check-in (QR Code) → Play

import streamlit as st
import random
from itertools import combinations
from datetime import datetime
import qrcode
from io import BytesIO
import json
from pathlib import Path
import string

# ============================================
# PAGE CONFIGURATION
# ============================================
st.set_page_config(
    page_title="Pickleball Tournament Pro",
    page_icon="🏓",
    layout="wide"
)

# ============================================
# EVENT STORAGE FUNCTIONS
# ============================================

def get_data_dir():
    """Get or create the data directory for storing events"""
    data_dir = Path("/tmp/pickleball_events")
    data_dir.mkdir(exist_ok=True)
    return data_dir

def generate_event_code():
    """Generate a unique 6-character event code"""
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))

def save_event_data(event_code, data):
    """Save event data to JSON file"""
    data_dir = get_data_dir()
    file_path = data_dir / f"{event_code}.json"
    with open(file_path, 'w') as f:
        json.dump(data, f)

def load_event_data(event_code):
    """Load event data from JSON file"""
    data_dir = get_data_dir()
    file_path = data_dir / f"{event_code}.json"
    if file_path.exists():
        with open(file_path, 'r') as f:
            return json.load(f)
    return None

def add_player_to_event(event_code, player_name):
    """Add a player to an event"""
    data = load_event_data(event_code)
    if data and player_name and player_name.strip():
        if player_name not in data['players']:
            data['players'].append(player_name.strip())
            save_event_data(event_code, data)
            return True
    return False

# ============================================
# SESSION STATE INITIALIZATION
# ============================================
if 'page' not in st.session_state:
    st.session_state.page = 'home'

if 'event_name' not in st.session_state:
    st.session_state.event_name = ""

if 'event_code' not in st.session_state:
    st.session_state.event_code = None

if 'format_choice' not in st.session_state:
    st.session_state.format_choice = None

if 'game_score' not in st.session_state:
    st.session_state.game_score = 11

if 'player_cap' not in st.session_state:
    st.session_state.player_cap = 16

if 'num_courts' not in st.session_state:
    st.session_state.num_courts = 2

if 'num_rounds' not in st.session_state:
    st.session_state.num_rounds = 1

if 'players' not in st.session_state:
    st.session_state.players = []

if 'current_round' not in st.session_state:
    st.session_state.current_round = 0

if 'scores' not in st.session_state:
    st.session_state.scores = {}

if 'game_scores' not in st.session_state:
    st.session_state.game_scores = []

if 'players_on_break' not in st.session_state:
    st.session_state.players_on_break = []

if 'current_games' not in st.session_state:
    st.session_state.current_games = []

if 'sitting_out' not in st.session_state:
    st.session_state.sitting_out = []

if 'court_groups' not in st.session_state:
    st.session_state.court_groups = []

if 'court_game_index' not in st.session_state:
    st.session_state.court_game_index = {}

if 'court_points' not in st.session_state:
    st.session_state.court_points = {}

if 'partner_mode' not in st.session_state:
    st.session_state.partner_mode = 'Singles'

if 'fixed_partners' not in st.session_state:
    st.session_state.fixed_partners = {}

if 'gender_assignments' not in st.session_state:
    st.session_state.gender_assignments = {}

if 'partner_history' not in st.session_state:
    st.session_state.partner_history = {}

# ============================================
# HELPER FUNCTIONS
# ============================================

def calculate_win_percentage(wins, games):
    if games == 0:
        return 0
    return (wins / games) * 100

def create_classic_round_robin_matchups(players, num_courts):
    """Classic Round Robin"""
    if 'partner_history' not in st.session_state:
        st.session_state.partner_history = {}
    
    for player in players:
        if player not in st.session_state.partner_history:
            st.session_state.partner_history[player] = set()
    
    def get_unpartnered_pair(available_players):
        if len(available_players) < 2:
            return None
            
        for i, p1 in enumerate(available_players):
            for p2 in available_players[i+1:]:
                if p2 not in st.session_state.partner_history.get(p1, set()):
                    return (p1, p2)
        return (available_players[0], available_players[1])
    
    shuffled = players.copy()
    random.shuffle(shuffled)
    
    players_per_round = num_courts * 4
    playing = shuffled[:players_per_round]
    sitting = shuffled[players_per_round:]
    
    games = []
    used_players = set()
    
    for court in range(num_courts):
        available = [p for p in playing if p not in used_players]
        if len(available) < 4:
            break
            
        pair1 = get_unpartnered_pair(available)
        if not pair1:
            break
            
        used_players.add(pair1[0])
        used_players.add(pair1[1])
        
        available = [p for p in playing if p not in used_players]
        pair2 = get_unpartnered_pair(available)
        if not pair2:
            break
            
        used_players.add(pair2[0])
        used_players.add(pair2[1])
        
        games.append({
            'court': court + 1,
            'team1': [pair1[0], pair1[1]],
            'team2': [pair2[0], pair2[1]]
        })
        
        for p in [pair1[0], pair1[1], pair2[0], pair2[1]]:
            if p not in st.session_state.partner_history:
                st.session_state.partner_history[p] = set()
                
        st.session_state.partner_history[pair1[0]].add(pair1[1])
        st.session_state.partner_history[pair1[1]].add(pair1[0])
        st.session_state.partner_history[pair2[0]].add(pair2[1])
        st.session_state.partner_history[pair2[1]].add(pair2[0])
    
    return games, sitting

def create_popcorn_matchups(players, num_courts, fixed_partners=None):
    """Popcorn: Random matchups"""
    if fixed_partners:
        available_pairs = list(fixed_partners.items())
        random.shuffle(available_pairs)
        
        games = []
        for i in range(0, len(available_pairs) - 1, 2):
            if i + 1 < len(available_pairs):
                pair1 = available_pairs[i]
                pair2 = available_pairs[i + 1]
                
                if len(games) < num_courts:
                    games.append({
                        'court': len(games) + 1,
                        'team1': [pair1[0], pair1[1]],
                        'team2': [pair2[0], pair2[1]]
                    })
        
        sitting_out = []
        if len(available_pairs) % 2 == 1:
            last_pair = available_pairs[-1]
            sitting_out = [last_pair[0], last_pair[1]]
        
        return games, sitting_out
    else:
        shuffled = players.copy()
        random.shuffle(shuffled)
        
        players_per_round = num_courts * 4
        playing = shuffled[:players_per_round]
        sitting = shuffled[players_per_round:]
        
        games = []
        for i in range(0, len(playing), 4):
            if i + 3 < len(playing):
                four = playing[i:i+4]
                games.append({
                    'court': (i // 4) + 1,
                    'team1': [four[0], four[1]],
                    'team2': [four[2], four[3]]
                })
        
        return games, sitting

# Shortened helper functions for brevity - keeping only essential ones
def go_to_page(page_name):
    st.session_state.page = page_name
    st.rerun()

def reset_tournament():
    st.session_state.current_round = 0
    st.session_state.scores = {}
    st.session_state.game_scores = []
    st.session_state.current_games = []
    st.session_state.sitting_out = []
    st.session_state.court_groups = []
    st.session_state.partner_history = {}

def generate_new_round():
    """Generate matchups for a new round"""
    players = [p for p in st.session_state.players if p not in st.session_state.players_on_break]
    num_courts = st.session_state.num_courts
    format_choice = st.session_state.format_choice
    
    for player in players:
        if player not in st.session_state.scores:
            st.session_state.scores[player] = {
                'wins': 0,
                'losses': 0,
                'games_played': 0,
                'points_for': 0,
                'points_against': 0,
                'point_diff': 0
            }
    
    if format_choice == "Classic Round Robin":
        games, sitting = create_classic_round_robin_matchups(players, num_courts)
        st.session_state.current_games = games
        st.session_state.sitting_out = sitting
        st.session_state.court_groups = []
    else:
        games, sitting = create_popcorn_matchups(players, num_courts)
        st.session_state.current_games = games
        st.session_state.sitting_out = sitting
        st.session_state.court_groups = []

# ============================================
# PAGE 1: HOME / EVENT SETUP
# ============================================

def show_home_page():
    st.title("🏓 Pickleball Tournament Pro")
    
    st.markdown("---")
    
    st.markdown("### Event Setup")
    st.markdown("")
    
    # Section 1: Event Name
    st.markdown("#### 1. Event Name")
    event_name = st.text_input(
        "What's the name of your event?",
        value=st.session_state.event_name,
        placeholder="e.g., Summer Pickleball Tournament 2025"
    )
    st.session_state.event_name = event_name
    
    st.markdown("")
    
    # Section 2: Player Cap
    st.markdown("#### 2. Player Capacity")
    player_cap = st.number_input(
        "Maximum number of players allowed?",
        min_value=4,
        max_value=100,
        value=st.session_state.player_cap,
        step=2,
        help="Players will check in via QR code up to this limit"
    )
    st.session_state.player_cap = player_cap
    
    st.markdown("")
    
    # Section 3: Courts
    st.markdown("#### 3. Courts")
    num_courts = st.number_input(
        "How many courts are available?",
        min_value=1,
        max_value=20,
        value=st.session_state.num_courts,
        step=1
    )
    st.session_state.num_courts = num_courts
    
    st.markdown("")
    
    # Section 4: Partners
    st.markdown("#### 4. Partners")
    partner_type = st.checkbox(
        "Fixed Partners",
        value=st.session_state.partner_mode == "Fixed Partners",
        help="Check for fixed partners, uncheck for random partners"
    )
    
    if partner_type:
        st.session_state.partner_mode = "Fixed Partners"
        st.success("✅ Partners will stay together throughout the tournament")
    else:
        st.session_state.partner_mode = "Singles"
        st.success("✅ Partners will be randomly assigned each round")
    
    st.markdown("---")
    
    # Start button
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        if st.button("▶️ Next: Choose Format", type="primary", use_container_width=True):
            if not event_name or not event_name.strip():
                st.error("Please enter an event name")
            else:
                # Generate event code
                event_code = generate_event_code()
                st.session_state.event_code = event_code
                
                # Save initial event data
                event_data = {
                    'event_name': event_name,
                    'event_code': event_code,
                    'player_cap': player_cap,
                    'num_courts': num_courts,
                    'partner_mode': st.session_state.partner_mode,
                    'players': [],
                    'created_at': datetime.now().isoformat()
                }
                save_event_data(event_code, event_data)
                
                go_to_page('format_selection')

# ============================================
# PAGE 2: FORMAT SELECTION
# ============================================

def show_format_selection_page():
    st.title("🏓 " + st.session_state.event_name)
    
    if st.button("← Back"):
        go_to_page('home')
    
    st.markdown("---")
    st.markdown("## Choose Your Format")
    
    format_options = {
        "Classic Round Robin": {
            "icon": "🎯",
            "short": "Maximum Partner Variety",
            "description": "Priority is getting everyone to play with people who haven't been partners yet. Best for maximizing partner variety."
        },
        "Popcorn": {
            "icon": "🍿",
            "short": "Random & Social",
            "description": "Random matchups every round. Mix with as many players as possible. Great for social play!"
        },
    }
    
    selected_format = None
    
    for format_name, info in format_options.items():
        with st.container():
            col1, col2 = st.columns([4, 1])
            
            with col1:
                st.markdown(f"### {info['icon']} {format_name}")
                st.markdown(f"**{info['short']}**")
                st.markdown(info['description'])
            
            with col2:
                st.markdown("")
                if st.button("Select", key=f"select_{format_name}", use_container_width=True):
                    selected_format = format_name
            
            st.markdown("")
    
    if selected_format:
        st.session_state.format_choice = selected_format
        go_to_page('player_checkin')

# ============================================
# PAGE 3: PLAYER CHECK-IN (QR CODE)
# ============================================

def show_player_checkin_page():
    st.title("🏓 " + st.session_state.event_name)
    
    if st.button("← Back"):
        go_to_page('format_selection')
    
    st.markdown("---")
    
    # Get query parameters to check if this is a player check-in
    query_params = st.query_params
    is_player_view = 'join' in query_params and query_params.get('join') == st.session_state.event_code
    
    if is_player_view:
        # PLAYER CHECK-IN VIEW
        st.markdown("## Check In")
        st.markdown(f"### Event: {st.session_state.event_name}")
        
        player_name = st.text_input("Enter your name:", placeholder="First and Last Name")
        
        if st.button("✅ Check In", type="primary", use_container_width=True):
            if player_name and player_name.strip():
                if add_player_to_event(st.session_state.event_code, player_name):
                    st.success(f"✅ Welcome, {player_name}! You're checked in.")
                    st.balloons()
                else:
                    st.error("Unable to check in. Please try again.")
            else:
                st.error("Please enter your name")
        
        st.markdown("---")
        st.info("📱 You can close this page after checking in")
        
    else:
        # ORGANIZER VIEW
        st.markdown("## Player Check-In")
        
        # Generate QR Code
        col1, col2 = st.columns([1, 1])
        
        with col1:
            st.markdown("### QR Code for Players")
            
            # Get the current app URL
            # In production, this would be your deployed URL
            base_url = "https://pickleball-round-robin-generator-gdye9ixyhszt29qbtmsufy.streamlit.app"
            check_in_url = f"{base_url}/?join={st.session_state.event_code}"
            
            # Generate QR code
            qr = qrcode.QRCode(version=1, box_size=10, border=4)
            qr.add_data(check_in_url)
            qr.make(fit=True)
            
            img = qr.make_image(fill_color="#4A5568", back_color="white")
            
            # Convert to bytes
            buf = BytesIO()
            img.save(buf, format='PNG')
            buf.seek(0)
            
            st.image(buf, caption="Scan to Check In", width=300)
            
            st.markdown("---")
            st.markdown("### Event Code")
            st.code(st.session_state.event_code, language=None)
            st.caption("Players can also manually enter this code")
        
        with col2:
            # Load current players from event data
            event_data = load_event_data(st.session_state.event_code)
            if event_data:
                st.session_state.players = event_data['players']
            
            st.markdown(f"### Checked In Players ({len(st.session_state.players)}/{st.session_state.player_cap})")
            
            # Add player manually
            manual_name = st.text_input("Add player manually:", placeholder="Player name", key="manual_add")
            if st.button("➕ Add", key="add_manual"):
                if manual_name and manual_name.strip():
                    if add_player_to_event(st.session_state.event_code, manual_name):
                        st.success(f"Added {manual_name}")
                        st.rerun()
            
            st.markdown("")
            
            # Show player list
            if st.session_state.players:
                for i, player in enumerate(st.session_state.players):
                    col_a, col_b = st.columns([3, 1])
                    with col_a:
                        st.markdown(f"**{i+1}.** {player}")
                    with col_b:
                        if st.button("❌", key=f"remove_{i}"):
                            st.session_state.players.remove(player)
                            event_data = load_event_data(st.session_state.event_code)
                            event_data['players'] = st.session_state.players
                            save_event_data(st.session_state.event_code, event_data)
                            st.rerun()
            else:
                st.info("No players checked in yet")
        
        st.markdown("---")
        
        # Auto-refresh option
        if st.checkbox("Auto-refresh (updates every 5 seconds)", value=False):
            st.rerun()
        
        # Start tournament button
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if len(st.session_state.players) >= 4:
                if st.button("🎮 Start Tournament", type="primary", use_container_width=True):
                    go_to_page('play')
            else:
                st.warning("⚠️ Need at least 4 players to start")

# ============================================
# PAGE 4: PLAY TOURNAMENT  
# ============================================

def show_play_page():
    col_nav1, col_nav2, col_nav3 = st.columns([1, 2, 1])
    
    with col_nav1:
        if st.button("← Back"):
            go_to_page('player_checkin')
    
    with col_nav2:
        st.markdown(f"<h2 style='text-align: center;'>{st.session_state.event_name} - Round {st.session_state.current_round}</h2>", unsafe_allow_html=True)
    
    with col_nav3:
        if st.button("🏆 Standings"):
            go_to_page('standings')
    
    st.markdown("---")
    
    players = st.session_state.players
    num_courts = st.session_state.num_courts
    
    games_in_progress = st.session_state.current_games or st.session_state.court_groups
    
    if not games_in_progress:
        st.info("⚠️ No games generated. Click below to start Round 1.")
        if st.button("🎲 Generate Round 1", type="primary", use_container_width=True):
            st.session_state.current_round = 1
            generate_new_round()
            st.rerun()
        return
    
    if 'pending_scores' not in st.session_state:
        st.session_state.pending_scores = {}
    
    # DISPLAY GAMES
    if st.session_state.current_games:
        for game in st.session_state.current_games:
            court_num = game['court']
            
            # Court header with neutral blue
            st.markdown(f"""
            <div style='background-color: #4A90E2; padding: 12px; border-radius: 8px; margin-bottom: 15px;'>
                <h3 style='margin: 0; color: white;'>COURT {court_num}</h3>
            </div>
            """, unsafe_allow_html=True)
            
            col1, col2, col3 = st.columns([3, 1, 1])
            
            with col1:
                # Team 1 - Soft blue
                st.markdown(f"""
                <div style='background-color: #E3F2FD; padding: 18px; border-radius: 8px; margin-bottom: 8px; border: 2px solid #64B5F6;'>
                    <span style='font-size: 22px; font-weight: bold; color: #1976D2;'>{game['team1'][0]}</span>
                    <span style='font-size: 22px; font-weight: bold; color: #1976D2; margin-left: 50px;'>{game['team1'][1]}</span>
                </div>
                """, unsafe_allow_html=True)
                
                st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)
                
                # Team 2 - Soft gray
                st.markdown(f"""
                <div style='background-color: #F5F5F5; padding: 18px; border-radius: 8px; border: 2px solid #9E9E9E;'>
                    <span style='font-size: 22px; font-weight: bold; color: #424242;'>{game['team2'][0]}</span>
                    <span style='font-size: 22px; font-weight: bold; color: #424242; margin-left: 50px;'>{game['team2'][1]}</span>
                </div>
                """, unsafe_allow_html=True)
            
            with col2:
                st.markdown("##")
                st.markdown("<h3 style='text-align: center;'>VS</h3>", unsafe_allow_html=True)
            
            with col3:
                team1_score = st.number_input(
                    "Score",
                    min_value=0,
                    max_value=30,
                    value=None,
                    key=f"single_t1_c{court_num}_r{st.session_state.current_round}",
                    label_visibility="collapsed",
                    placeholder="Enter score"
                )
                
                st.markdown("---")
                
                team2_score = st.number_input(
                    "Score",
                    min_value=0,
                    max_value=30,
                    value=None,
                    key=f"single_t2_c{court_num}_r{st.session_state.current_round}",
                    label_visibility="collapsed",
                    placeholder="Enter score"
                )
                
                st.session_state.pending_scores[court_num] = {
                    'team1': game['team1'],
                    'team2': game['team2'],
                    'score1': team1_score,
                    'score2': team2_score
                }
            
            st.markdown("<br>", unsafe_allow_html=True)
        
        if st.session_state.sitting_out:
            st.markdown("---")
            st.markdown(f"""
            <div style='background-color: #f5f5f5; padding: 18px; border-radius: 8px; border-left: 4px solid #9e9e9e;'>
                <h4 style='margin: 0; color: #616161;'>🪑 Sitting Out This Round</h4>
                <p style='margin: 8px 0 0 0; font-size: 20px; font-weight: 500; color: #424242;'>{', '.join(st.session_state.sitting_out)}</p>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown("")
        st.markdown("")
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button("✅ SUBMIT ALL SCORES", type="primary", use_container_width=True, key="submit_all"):
                all_valid = True
                for court_num, score_data in st.session_state.pending_scores.items():
                    if (score_data['score1'] is None or score_data['score1'] == 0) and (score_data['score2'] is None or score_data['score2'] == 0):
                        all_valid = False
                        break
                
                if not all_valid:
                    st.error("⚠️ Please enter scores for all courts!")
                else:
                    for court_num, score_data in st.session_state.pending_scores.items():
                        team1_score = score_data['score1']
                        team2_score = score_data['score2']
                        team1 = score_data['team1']
                        team2 = score_data['team2']
                        
                        team1_won = team1_score > team2_score
                        
                        for player in team1:
                            st.session_state.scores[player]['games_played'] += 1
                            st.session_state.scores[player]['points_for'] += team1_score
                            st.session_state.scores[player]['points_against'] += team2_score
                            st.session_state.scores[player]['point_diff'] = (
                                st.session_state.scores[player]['points_for'] - 
                                st.session_state.scores[player]['points_against']
                            )
                            if team1_won:
                                st.session_state.scores[player]['wins'] += 1
                            else:
                                st.session_state.scores[player]['losses'] += 1
                        
                        for player in team2:
                            st.session_state.scores[player]['games_played'] += 1
                            st.session_state.scores[player]['points_for'] += team2_score
                            st.session_state.scores[player]['points_against'] += team1_score
                            st.session_state.scores[player]['point_diff'] = (
                                st.session_state.scores[player]['points_for'] - 
                                st.session_state.scores[player]['points_against']
                            )
                            if not team1_won:
                                st.session_state.scores[player]['wins'] += 1
                            else:
                                st.session_state.scores[player]['losses'] += 1
                        
                        st.session_state.game_scores.append({
                            'round': st.session_state.current_round,
                            'court': court_num,
                            'team1': team1,
                            'team2': team2,
                            'score': [team1_score, team2_score]
                        })
                    
                    st.session_state.pending_scores = {}
                    go_to_page('standings')

# ============================================
# PAGE 5: STANDINGS
# ============================================

def show_standings_page():
    col_nav1, col_nav2, col_nav3 = st.columns([1, 2, 1])
    
    with col_nav1:
        if st.button("← Back to Play"):
            go_to_page('play')
    
    with col_nav2:
        st.markdown(f"### 🏆 {st.session_state.event_name} - Standings")
    
    with col_nav3:
        if st.button("🏠 Home"):
            go_to_page('home')
    
    st.markdown("---")
    
    if st.session_state.scores:
        standings = []
        
        for player, stats in st.session_state.scores.items():
            win_pct = calculate_win_percentage(stats['wins'], stats['games_played'])
            
            standings.append({
                'Rank': 0,
                'Player': player,
                'Wins': stats['wins'],
                'Losses': stats['losses'],
                'Games': stats['games_played'],
                'Win %': f"{win_pct:.1f}%",
                'Points For': stats.get('points_for', 0),
                'Points Against': stats.get('points_against', 0),
                'Point Diff': stats.get('point_diff', 0)
            })
        
        standings.sort(key=lambda x: (x['Points For'], x['Point Diff'], x['Wins']), reverse=True)
        
        for i, standing in enumerate(standings):
            standing['Rank'] = i + 1
        
        if standings:
            st.markdown("## 🎉 Top Players")
            
            col1, col2, col3 = st.columns(3)
            
            if len(standings) >= 1:
                with col1:
                    st.markdown(f"### 🥇 1st Place")
                    st.markdown(f"## {standings[0]['Player']}")
                    st.markdown(f"**{standings[0]['Wins']} wins** | {standings[0]['Points For']} pts scored")
            
            if len(standings) >= 2:
                with col2:
                    st.markdown(f"### 🥈 2nd Place")
                    st.markdown(f"## {standings[1]['Player']}")
                    st.markdown(f"**{standings[1]['Wins']} wins** | {standings[1]['Points For']} pts scored")
            
            if len(standings) >= 3:
                with col3:
                    st.markdown(f"### 🥉 3rd Place")
                    st.markdown(f"## {standings[2]['Player']}")
                    st.markdown(f"**{standings[2]['Wins']} wins** | {standings[2]['Points For']} pts scored")
            
            st.markdown("---")
            st.markdown("## Full Standings")
            
            st.dataframe(standings, use_container_width=True, hide_index=True)
        else:
            st.info("No games played yet!")
    else:
        st.info("No scores recorded yet!")
    
    st.markdown("---")
    
    col_a, col_b, col_c = st.columns(3)
    
    with col_a:
        if st.button("➡️ Generate Next Round", type="primary", use_container_width=True):
            st.session_state.current_round += 1
            generate_new_round()
            go_to_page('play')
    
    with col_b:
        if st.button("🔄 Reset & Start New", use_container_width=True):
            reset_tournament()
            go_to_page('home')
    
    with col_c:
        if st.button("🏠 Home", use_container_width=True):
            go_to_page('home')

# ============================================
# MAIN APP ROUTER
# ============================================

def main():
    page = st.session_state.page
    
    if page == 'home':
        show_home_page()
    elif page == 'format_selection':
        show_format_selection_page()
    elif page == 'player_checkin':
        show_player_checkin_page()
    elif page == 'play':
        show_play_page()
    elif page == 'standings':
        show_standings_page()

if __name__ == "__main__":
    main()
