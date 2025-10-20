# PICKLEBALL TOURNAMENT PRO - Streamlined Flow
# Home → Round Robin Selection → Configuration → Play

import streamlit as st
import random
from itertools import combinations
from datetime import datetime
import time

# ============================================
# PAGE CONFIGURATION
# ============================================
st.set_page_config(
    page_title="Pickleball Tournament Pro",
    page_icon="🏓",
    layout="wide"
)

# ============================================
# SESSION STATE INITIALIZATION
# ============================================
if 'page' not in st.session_state:
    st.session_state.page = 'home'

if 'format_choice' not in st.session_state:
    st.session_state.format_choice = None

if 'num_players' not in st.session_state:
    st.session_state.num_players = 8

if 'num_courts' not in st.session_state:
    st.session_state.num_courts = 2

if 'players' not in st.session_state:
    st.session_state.players = []

if 'current_round' not in st.session_state:
    st.session_state.current_round = 0

if 'scores' not in st.session_state:
    st.session_state.scores = {}

if 'game_scores' not in st.session_state:
    # Track individual game scores for history
    st.session_state.game_scores = []

if 'round_start_time' not in st.session_state:
    st.session_state.round_start_time = None

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

# ============================================
# HELPER FUNCTIONS
# ============================================

def calculate_win_percentage(wins, games):
    if games == 0:
        return 0
    return (wins / games) * 100

def create_popcorn_matchups(players, num_courts, fixed_partners=None):
    """Popcorn: Random matchups every round"""
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

def create_gauntlet_matchups(players, num_courts, scores, fixed_partners=None):
    """Gauntlet: Winners face harder opponents"""
    player_rankings = []
    for player in players:
        if player in scores:
            wins = scores[player]['wins']
            games = scores[player]['games_played']
            win_pct = calculate_win_percentage(wins, games)
        else:
            win_pct = 0
        player_rankings.append((player, win_pct))
    
    player_rankings.sort(key=lambda x: x[1], reverse=True)
    sorted_players = [p[0] for p in player_rankings]
    
    if fixed_partners:
        pair_rankings = []
        processed = set()
        
        for player in sorted_players:
            if player not in processed and player in fixed_partners:
                partner = fixed_partners[player]
                if partner in scores and player in scores:
                    avg_win_pct = (
                        calculate_win_percentage(scores[player]['wins'], scores[player]['games_played']) +
                        calculate_win_percentage(scores[partner]['wins'], scores[partner]['games_played'])
                    ) / 2
                else:
                    avg_win_pct = 0
                
                pair_rankings.append(([player, partner], avg_win_pct))
                processed.add(player)
                processed.add(partner)
        
        pair_rankings.sort(key=lambda x: x[1], reverse=True)
        
        games = []
        for i in range(0, len(pair_rankings) - 1, 2):
            if i + 1 < len(pair_rankings) and len(games) < num_courts:
                games.append({
                    'court': len(games) + 1,
                    'team1': pair_rankings[i][0],
                    'team2': pair_rankings[i + 1][0]
                })
        
        sitting_out = []
        if len(pair_rankings) % 2 == 1:
            sitting_out = pair_rankings[-1][0]
        
        return games, sitting_out
    else:
        shuffled = sorted_players.copy()
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

def create_up_down_river_groups(players, num_courts, scores, fixed_partners=None):
    """Up & Down: Players seeded to courts, play multiple games"""
    player_rankings = []
    for player in players:
        if player in scores:
            win_pct = calculate_win_percentage(scores[player]['wins'], scores[player]['games_played'])
        else:
            win_pct = 0
        player_rankings.append((player, win_pct))
    
    player_rankings.sort(key=lambda x: x[1], reverse=True)
    sorted_players = [p[0] for p in player_rankings]
    
    if fixed_partners:
        pair_groups = []
        processed = set()
        
        for player in sorted_players:
            if player not in processed and player in fixed_partners:
                partner = fixed_partners[player]
                pair_groups.append([player, partner])
                processed.add(player)
                processed.add(partner)
        
        court_assignments = []
        for i in range(0, len(pair_groups), 2):
            if i + 1 < len(pair_groups) and len(court_assignments) < num_courts:
                court_assignments.append({
                    'court': len(court_assignments) + 1,
                    'pairs': [pair_groups[i], pair_groups[i + 1]]
                })
        
        return court_assignments
    else:
        players_per_court = max(4, len(sorted_players) // num_courts)
        
        court_assignments = []
        for i in range(num_courts):
            start = i * players_per_court
            if i == num_courts - 1:
                court_players = sorted_players[start:]
            else:
                court_players = sorted_players[start:start + players_per_court]
            
            if len(court_players) >= 4:
                court_assignments.append({
                    'court': i + 1,
                    'players': court_players
                })
        
        return court_assignments

def generate_court_games(court_players):
    """Generate all partnership combinations for a court"""
    games = []
    all_pairs = list(combinations(court_players, 2))
    
    used_games = set()
    for i, pair1 in enumerate(all_pairs):
        for pair2 in all_pairs[i+1:]:
            if len(set(pair1 + pair2)) == 4:
                game_id = tuple(sorted(pair1 + pair2))
                if game_id not in used_games:
                    games.append({
                        'team1': list(pair1),
                        'team2': list(pair2)
                    })
                    used_games.add(game_id)
    
    return games

def create_scramble_groups(players, num_courts):
    """Scramble: Random groups stay on court"""
    shuffled = players.copy()
    random.shuffle(shuffled)
    
    players_per_court = max(4, len(shuffled) // num_courts)
    
    groups = []
    for i in range(num_courts):
        start = i * players_per_court
        if i == num_courts - 1:
            court_players = shuffled[start:]
        else:
            court_players = shuffled[start:start + players_per_court]
        
        if len(court_players) >= 4:
            groups.append({
                'court': i + 1,
                'players': court_players
            })
    
    return groups

def create_mixed_madness_matchups(players, num_courts, gender_dict):
    """Mixed Madness: Random mixed doubles"""
    males = [p for p in players if gender_dict.get(p) == 'M']
    females = [p for p in players if gender_dict.get(p) == 'F']
    
    random.shuffle(males)
    random.shuffle(females)
    
    games = []
    sitting_out = []
    
    min_pairs = min(len(males), len(females))
    
    for i in range(0, min_pairs - 1, 2):
        if i + 1 < min_pairs and len(games) < num_courts:
            games.append({
                'court': len(games) + 1,
                'team1': [males[i], females[i]],
                'team2': [males[i + 1], females[i + 1]]
            })
    
    if min_pairs % 2 == 1 and min_pairs > 0:
        sitting_out.append(males[min_pairs - 1])
        sitting_out.append(females[min_pairs - 1])
    
    sitting_out.extend(males[min_pairs:])
    sitting_out.extend(females[min_pairs:])
    
    return games, sitting_out

# ============================================
# PAGE NAVIGATION FUNCTIONS
# ============================================

def go_to_page(page_name):
    st.session_state.page = page_name
    st.rerun()

def reset_tournament():
    st.session_state.current_round = 0
    st.session_state.scores = {}
    st.session_state.current_games = []
    st.session_state.sitting_out = []
    st.session_state.court_groups = []
    st.session_state.court_game_index = {}
    st.session_state.court_points = {}
    st.session_state.game_scores = []
    st.session_state.players_on_break = []
    st.session_state.round_start_time = None

# ============================================
# PAGE 1: HOME
# ============================================

def show_home_page():
    st.title("🏓 Pickleball Tournament Pro")
    st.markdown("### Professional Tournament Management")
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown("## Welcome!")
        st.markdown("""
        Manage your pickleball tournaments with ease:
        
        ✅ **8 Tournament Formats** - From casual to competitive  
        ✅ **Score Tracking** - Real points scored, not just wins  
        ✅ **Live Standings** - Updated in real-time  
        ✅ **12-Minute Timer** - Keep rounds on schedule  
        ✅ **8-70 Players** - Handles any group size  
        ✅ **Break Management** - Rotate players easily
        """)
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        if st.button("🚀 Start Tournament", use_container_width=True, type="primary", key="btn_start"):
            go_to_page('format_selection')
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Quick info
        with st.expander("📖 About Tournament Formats"):
            st.markdown("""
            **Social Formats:**
            - 🍿 Popcorn - Random mixing
            - 🎲 Scramble - Group play
            - 🎭 Mixed Madness - Mixed doubles
            
            **Competitive Formats:**
            - ⚔️ Gauntlet - Skill-based matching
            - 👑 Claim the Throne - Court progression
            - 🏔️ Up & Down the River - Multi-game courts
            - 🌟 Cream of the Crop - Rising stars
            - 🎯 Double Header - Extended sessions
            """)

# ============================================
# PAGE 2: FORMAT SELECTION
# ============================================

def show_format_selection_page():
    st.title("🔄 Round Robin Tournament")
    
    # Back button
    if st.button("← Back to Home"):
        go_to_page('home')
    
    st.markdown("---")
    st.markdown("## Step 1: Choose Your Format")
    
    # Format selection with descriptions
    format_options = {
        "Popcorn": {
            "icon": "🍿",
            "short": "Random & Social",
            "description": "Random matchups every round. Mix with as many players as possible. 1 game per round. Great for social play!"
        },
        "Gauntlet": {
            "icon": "⚔️",
            "short": "Competitive",
            "description": "Winners face harder opponents, losers face easier ones. Seeded matchups. Perfect for competitive balance."
        },
        "Up and Down the River": {
            "icon": "🏔️",
            "short": "Court Movement",
            "description": "Players seeded to courts, play 3-5 games, winners move up courts. Minimizes court switching."
        },
        "Claim the Throne": {
            "icon": "👑",
            "short": "Classic Weighted",
            "description": "Winners move up, losers move down. Higher courts worth more points. 1 game per round."
        },
        "Cream of the Crop": {
            "icon": "🌟",
            "short": "Rising Stars",
            "description": "Balanced groups initially, top performers rise to Court #1. Multiple games per round."
        },
        "Double Header": {
            "icon": "🎯",
            "short": "Everyone Partners Twice",
            "description": "Partner with everyone twice. 4 players per court. 6-9 games per round. Perfect for 2-hour sessions."
        },
        "Mixed Madness": {
            "icon": "🎭",
            "short": "Mixed Doubles",
            "description": "Random mixed doubles matchups. Handles uneven gender ratios. Social and fun!"
        },
        "Scramble": {
            "icon": "🎲",
            "short": "Group Play",
            "description": "Random groups stay on court for 3-5 games. Minimizes waiting and switching."
        }
    }
    
    # Display formats in a grid
    cols = st.columns(2)
    
    for idx, (format_name, details) in enumerate(format_options.items()):
        with cols[idx % 2]:
            with st.container():
                st.markdown(f"### {details['icon']} {format_name}")
                st.markdown(f"**{details['short']}**")
                st.caption(details['description'])
                
                if st.button(f"Select {format_name}", key=f"select_{format_name}", use_container_width=True):
                    st.session_state.format_choice = format_name
                    go_to_page('configuration')
                
                st.markdown("<br>", unsafe_allow_html=True)
    
# ============================================
# PAGE 3: CONFIGURATION
# ============================================

def show_configuration_page():
    st.title(f"🔄 {st.session_state.format_choice}")
    
    # Back button
    if st.button("← Back to Format Selection"):
        go_to_page('format_selection')
    
    st.markdown("---")
    st.markdown("## Step 2: Configure Tournament")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Basic Settings")
        
        num_players = st.number_input(
            "Number of Players:",
            min_value=4,
            max_value=70,
            value=st.session_state.num_players,
            step=1,
            help="How many people are playing?"
        )
        st.session_state.num_players = num_players
        
        num_courts = st.number_input(
            "Number of Courts:",
            min_value=1,
            max_value=20,
            value=st.session_state.num_courts,
            step=1,
            help="How many courts are available?"
        )
        st.session_state.num_courts = num_courts
        
        # Calculated info
        max_playing = num_courts * 4
        st.info(f"📊 Up to {max_playing} players can play simultaneously on {num_courts} court(s)")
    
    with col2:
        st.subheader("Partner Mode")
        
        partner_mode = st.radio(
            "How should partners be assigned?",
            ["Singles (Random Pairings)", "Fixed Partners"],
            help="Singles = new random partners each game. Fixed = same partner throughout tournament."
        )
        st.session_state.partner_mode = partner_mode
        
        if partner_mode == "Fixed Partners":
            st.info("💡 You'll assign partner pairs on the next page")
        
        # Special setting for Mixed Madness
        if st.session_state.format_choice == "Mixed Madness":
            st.info("🎭 You'll assign genders on the next page for mixed doubles")
    
    st.markdown("---")
    
    # Continue button
    col_a, col_b, col_c = st.columns([1, 1, 1])
    with col_b:
        if st.button("Continue to Player Entry →", type="primary", use_container_width=True):
            go_to_page('player_entry')

# ============================================
# PAGE 4: PLAYER ENTRY
# ============================================

def show_player_entry_page():
    st.title(f"🔄 {st.session_state.format_choice}")
    
    # Back button
    if st.button("← Back to Configuration"):
        go_to_page('configuration')
    
    st.markdown("---")
    st.markdown("## Step 3: Enter Players")
    
    # Create individual input boxes for each player
    num_players = st.session_state.num_players
    
    st.subheader(f"Enter {num_players} Player Names:")
    
    # Organize inputs in columns for better layout
    cols_per_row = 3
    players = []
    
    for i in range(0, num_players, cols_per_row):
        cols = st.columns(cols_per_row)
        for j in range(cols_per_row):
            player_num = i + j
            if player_num < num_players:
                with cols[j]:
                    player_name = st.text_input(
                        f"Player {player_num + 1}:",
                        key=f"player_input_{player_num}",
                        placeholder=f"Name {player_num + 1}"
                    )
                    if player_name.strip():
                        players.append(player_name.strip())
    
    st.session_state.players = players
    
    # Show progress
    if len(players) < num_players:
        st.warning(f"⚠️ Entered {len(players)} of {num_players} players")
    else:
        st.success(f"✅ All {num_players} players entered!")
    
    st.markdown("---")
    
    # Additional settings based on mode
    col1, col2 = st.columns(2)
    
    with col1:
        # Fixed partners assignment
        if st.session_state.partner_mode == "Fixed Partners" and len(players) >= 2:
            st.subheader("Assign Partner Pairs")
            
            available_players = players.copy()
            temp_partners = {}
            
            pair_num = 1
            while len(available_players) >= 2:
                col_a, col_b = st.columns(2)
                
                with col_a:
                    if available_players:
                        player1 = st.selectbox(
                            f"Pair {pair_num} - Player 1:",
                            options=[""] + available_players,
                            key=f"fp1_{pair_num}"
                        )
                
                with col_b:
                    filtered = [p for p in available_players if p != player1]
                    if filtered and player1:
                        player2 = st.selectbox(
                            f"Pair {pair_num} - Player 2:",
                            options=[""] + filtered,
                            key=f"fp2_{pair_num}"
                        )
                    else:
                        player2 = ""
                
                if player1 and player2:
                    temp_partners[player1] = player2
                    temp_partners[player2] = player1
                    available_players.remove(player1)
                    available_players.remove(player2)
                    pair_num += 1
                else:
                    break
            
            st.session_state.fixed_partners = temp_partners
    
    with col2:
        # Gender assignment for Mixed Madness
        if st.session_state.format_choice == "Mixed Madness" and len(players) >= 4:
            st.subheader("Assign Genders")
            
            for player in players:
                gender = st.radio(
                    f"{player}:",
                    ["Male", "Female"],
                    key=f"gender_entry_{player}",
                    horizontal=True
                )
                st.session_state.gender_assignments[player] = 'M' if gender == "Male" else 'F'
    
    st.markdown("---")
    
    # Start tournament button
    col_a, col_b, col_c = st.columns([1, 1, 1])
    with col_b:
        if len(players) >= 4:
            if st.button("Start Tournament! 🚀", type="primary", use_container_width=True):
                # Initialize scores
                reset_tournament()
                for player in players:
                    st.session_state.scores[player] = {
                        'wins': 0,
                        'losses': 0,
                        'games_played': 0,
                        'points_for': 0,      # Total points scored
                        'points_against': 0,  # Total points allowed
                        'point_diff': 0       # Differential
                    }
                
                # AUTO-GENERATE FIRST ROUND
                st.session_state.current_round = 1
                generate_new_round()
                
                go_to_page('play')
        else:
            st.warning("Need at least 4 players to start")

# ============================================
# ROUND GENERATION FUNCTION
# ============================================

def generate_new_round():
    """Generate a new round based on current format"""
    players = st.session_state.players
    
    # Filter out players on break
    if st.session_state.players_on_break:
        players = [p for p in players if p not in st.session_state.players_on_break]
    
    num_courts = st.session_state.num_courts
    format_choice = st.session_state.format_choice
    fixed_partners = st.session_state.fixed_partners if st.session_state.partner_mode == "Fixed Partners" else None
    
    # START TIMER FOR NEW ROUND
    st.session_state.round_start_time = time.time()
    
    # Generate based on format
    if format_choice == "Popcorn":
        games, sitting = create_popcorn_matchups(players, num_courts, fixed_partners)
        st.session_state.current_games = games
        st.session_state.sitting_out = sitting
        st.session_state.court_groups = []
    
    elif format_choice == "Gauntlet":
        games, sitting = create_gauntlet_matchups(players, num_courts, st.session_state.scores, fixed_partners)
        st.session_state.current_games = games
        st.session_state.sitting_out = sitting
        st.session_state.court_groups = []
    
    elif format_choice in ["Up and Down the River", "Cream of the Crop"]:
        if format_choice == "Up and Down the River":
            groups = create_up_down_river_groups(players, num_courts, st.session_state.scores, fixed_partners)
        else:
            groups = create_up_down_river_groups(players, num_courts, st.session_state.scores, fixed_partners)
        
        st.session_state.court_groups = groups
        st.session_state.current_games = []
        st.session_state.court_game_index = {g['court']: 0 for g in groups}
        
        # Set court points
        for i, group in enumerate(groups):
            st.session_state.court_points[group['court']] = num_courts - i
    
    elif format_choice == "Claim the Throne":
        games, sitting = create_gauntlet_matchups(players, num_courts, st.session_state.scores, fixed_partners)
        st.session_state.current_games = games
        st.session_state.sitting_out = sitting
        
        # Weighted points
        for game in games:
            st.session_state.court_points[game['court']] = num_courts - game['court'] + 1
    
    elif format_choice in ["Double Header", "Scramble"]:
        groups = create_scramble_groups(players, num_courts)
        st.session_state.court_groups = groups
        st.session_state.current_games = []
        st.session_state.court_game_index = {g['court']: 0 for g in groups}
    
    elif format_choice == "Mixed Madness":
        games, sitting = create_mixed_madness_matchups(players, num_courts, st.session_state.gender_assignments)
        st.session_state.current_games = games
        st.session_state.sitting_out = sitting
        st.session_state.court_groups = []

def check_round_complete():
    """Check if all games in current round are complete"""
    # For single-game formats, always considered complete after scores recorded
    if st.session_state.current_games:
        return True  # Will trigger next round button
    
    # For multi-game formats, check if all courts finished
    if st.session_state.court_groups:
        for group in st.session_state.court_groups:
            court_num = group['court']
            
            if 'players' in group:
                players_list = group['players']
                all_games = generate_court_games(players_list)
                current_idx = st.session_state.court_game_index.get(court_num, 0)
                
                if current_idx < len(all_games):
                    return False  # Still have games to play
        
        return True  # All courts finished
    
    return False

# ============================================
# PAGE 5: PLAY TOURNAMENT
# ============================================

def show_play_page():
    # Top navigation bar with TIMER
    col_nav1, col_nav2, col_nav3 = st.columns([1, 2, 1])
    
    with col_nav1:
        if st.button("⬅️ Back"):
            go_to_page('player_entry')
    
    with col_nav2:
        st.markdown(f"<h2 style='text-align: center;'>🎮 Round {st.session_state.current_round}</h2>", unsafe_allow_html=True)
    
    with col_nav3:
        if st.button("🏆 View Standings"):
            go_to_page('standings')
    
    # TIMER DISPLAY
    if st.session_state.round_start_time:
        elapsed = time.time() - st.session_state.round_start_time
        remaining = max(0, 720 - elapsed)  # 720 seconds = 12 minutes
        
        minutes = int(remaining // 60)
        seconds = int(remaining % 60)
        
        if remaining > 0:
            timer_color = "green" if remaining > 180 else "orange" if remaining > 60 else "red"
            st.markdown(f"<h1 style='text-align: center; color: {timer_color};'>⏱️ {minutes:02d}:{seconds:02d}</h1>", unsafe_allow_html=True)
        else:
            st.markdown(f"<h1 style='text-align: center; color: red;'>⏱️ TIME'S UP!</h1>", unsafe_allow_html=True)
        
        # Auto-refresh every second for timer
        time.sleep(0.1)
        st.rerun()
    
    st.markdown("---")
    
    players = st.session_state.players
    num_courts = st.session_state.num_courts
    format_choice = st.session_state.format_choice
    
    # Check if we need to show "Next Round" button
    games_in_progress = st.session_state.current_games or st.session_state.court_groups
    
    if not games_in_progress:
        # No games generated yet (shouldn't happen with auto-gen, but just in case)
        st.info("⚠️ No games generated. Click below to start Round 1.")
        if st.button("🎲 Generate Round 1", type="primary", use_container_width=True):
            st.session_state.current_round = 1
            generate_new_round()
            st.rerun()
        return
    
    # Show shuffle button for random formats
    if st.session_state.current_games and format_choice in ["Popcorn", "Mixed Madness"]:
        col_shuffle1, col_shuffle2, col_shuffle3 = st.columns([1, 1, 1])
        with col_shuffle2:
            if st.button("🔀 Shuffle Matchups", use_container_width=True):
                generate_new_round()  # Re-generate with same round number
                st.rerun()
        st.markdown("---")
    
    # Dictionary to store all scores before submission
    if 'pending_scores' not in st.session_state:
        st.session_state.pending_scores = {}
    
    # DISPLAY GAMES - Single game formats (Popcorn, Gauntlet, Claim the Throne, Mixed Madness)
    if st.session_state.current_games:
        st.markdown("### 📍 Enter Scores for All Courts")
        st.markdown("")
        
        for game in st.session_state.current_games:
            court_num = game['court']
            
            # Container for each game
            with st.container():
                st.markdown(f"#### 🏟️ Court {court_num}")
                
                # Create columns for score entry
                col_team1, col_score, col_team2 = st.columns([2, 1.5, 2])
                
                with col_team1:
                    st.markdown("### 🔵 Team 1")
                    st.markdown(f"**{game['team1'][0]}**")
                    st.markdown(f"**{game['team1'][1]}**")
                
                with col_score:
                    st.markdown("### Score")
                    
                    # Score input fields
                    col_s1, col_vs, col_s2 = st.columns([1, 0.3, 1])
                    
                    with col_s1:
                        team1_score = st.number_input(
                            "Team 1",
                            min_value=0,
                            max_value=30,
                            value=0,
                            key=f"score_t1_{court_num}_{st.session_state.current_round}",
                            label_visibility="collapsed"
                        )
                    
                    with col_vs:
                        st.markdown("## -")
                    
                    with col_s2:
                        team2_score = st.number_input(
                            "Team 2",
                            min_value=0,
                            max_value=30,
                            value=0,
                            key=f"score_t2_{court_num}_{st.session_state.current_round}",
                            label_visibility="collapsed"
                        )
                    
                    # Store scores in session state
                    st.session_state.pending_scores[court_num] = {
                        'team1': game['team1'],
                        'team2': game['team2'],
                        'score1': team1_score,
                        'score2': team2_score
                    }
                
                with col_team2:
                    st.markdown("### 🔴 Team 2")
                    st.markdown(f"**{game['team2'][0]}**")
                    st.markdown(f"**{game['team2'][1]}**")
                
                st.markdown("---")
        
        # Show who's sitting out
        if st.session_state.sitting_out:
            st.info(f"🪑 Sitting out this round: {', '.join(st.session_state.sitting_out)}")
        
        # BIG SUBMIT ALL BUTTON AT BOTTOM
        st.markdown("")
        st.markdown("")
        col_submit1, col_submit2, col_submit3 = st.columns([1, 2, 1])
        with col_submit2:
            if st.button("✅ SUBMIT ALL SCORES", type="primary", use_container_width=True, key="submit_all_scores"):
                # Validate all scores are entered
                all_valid = True
                for court_num, score_data in st.session_state.pending_scores.items():
                    if score_data['score1'] == 0 and score_data['score2'] == 0:
                        all_valid = False
                        break
                
                if not all_valid:
                    st.error("⚠️ Please enter scores for all courts before submitting!")
                else:
                    # Process all scores
                    for court_num, score_data in st.session_state.pending_scores.items():
                        team1_score = score_data['score1']
                        team2_score = score_data['score2']
                        team1 = score_data['team1']
                        team2 = score_data['team2']
                        
                        team1_won = team1_score > team2_score
                        
                        # Update all player stats
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
                        
                        # Save game to history
                        st.session_state.game_scores.append({
                            'round': st.session_state.current_round,
                            'court': court_num,
                            'team1': team1,
                            'team2': team2,
                            'score': [team1_score, team2_score]
                        })
                    
                    # Clear pending scores
                    st.session_state.pending_scores = {}
                    
                    # Go to standings page
                    go_to_page('standings')
    
    # DISPLAY GROUPS - Multi-game formats (Up/Down River, Scramble, Double Header, Cream of Crop)
    elif st.session_state.court_groups:
        st.markdown("### 📍 Court Groups")
        st.markdown("*Complete each game one at a time*")
        st.markdown("")
        
        all_complete = True
        
        for group in st.session_state.court_groups:
            court_num = group['court']
            
            if 'players' in group:
                players_list = group['players']
                all_games = generate_court_games(players_list)
                current_idx = st.session_state.court_game_index.get(court_num, 0)
                
                # Check if this court is done
                court_complete = current_idx >= len(all_games)
                if not court_complete:
                    all_complete = False
                
                with st.expander(
                    f"🏟️ Court {court_num} — {', '.join(players_list)}" + 
                    (" ✅ COMPLETE" if court_complete else f" — Game {current_idx + 1}/{len(all_games)}"),
                    expanded=not court_complete
                ):
                    if not court_complete:
                        game = all_games[current_idx]
                        
                        st.markdown(f"**Game {current_idx + 1} of {len(all_games)}**")
                        st.markdown("")
                        
                        col_team1, col_score, col_team2 = st.columns([2, 1.5, 2])
                        
                        with col_team1:
                            st.markdown("### 🔵 Team 1")
                            st.markdown(f"**{game['team1'][0]}**")
                            st.markdown(f"**{game['team1'][1]}**")
                        
                        with col_score:
                            st.markdown("### Score")
                            
                            col_s1, col_vs, col_s2 = st.columns([1, 0.3, 1])
                            
                            with col_s1:
                                team1_score = st.number_input(
                                    "Team 1",
                                    min_value=0,
                                    max_value=30,
                                    value=0,
                                    key=f"grp_score_t1_{court_num}_{current_idx}",
                                    label_visibility="collapsed"
                                )
                            
                            with col_vs:
                                st.markdown("## -")
                            
                            with col_s2:
                                team2_score = st.number_input(
                                    "Team 2",
                                    min_value=0,
                                    max_value=30,
                                    value=0,
                                    key=f"grp_score_t2_{court_num}_{current_idx}",
                                    label_visibility="collapsed"
                                )
                            
                            st.markdown("")
                            
                            if st.button("✅ Submit This Game", key=f"grp_submit_{court_num}_{current_idx}", type="primary", use_container_width=True):
                                if team1_score == 0 and team2_score == 0:
                                    st.error("Please enter scores!")
                                else:
                                    team1_won = team1_score > team2_score
                                    
                                    for player in game['team1']:
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
                                    
                                    for player in game['team2']:
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
                                        'team1': game['team1'],
                                        'team2': game['team2'],
                                        'score': [team1_score, team2_score]
                                    })
                                    
                                    st.session_state.court_game_index[court_num] += 1
                                    st.rerun()
                        
                        with col_team2:
                            st.markdown("### 🔴 Team 2")
                            st.markdown(f"**{game['team2'][0]}**")
                            st.markdown(f"**{game['team2'][1]}**")
                    else:
                        st.success("✅ All games completed on this court!")
            
            elif 'pairs' in group:
                # Similar handling for fixed partners
                pair1, pair2 = group['pairs']
                current_idx = st.session_state.court_game_index.get(court_num, 0)
                max_games = 5
                
                court_complete = current_idx >= max_games
                if not court_complete:
                    all_complete = False
                
                with st.expander(
                    f"🏟️ Court {court_num}" + 
                    (" ✅ COMPLETE" if court_complete else f" — Game {current_idx + 1}/{max_games}"),
                    expanded=not court_complete
                ):
                    st.markdown(f"**{pair1[0]} & {pair1[1]}** vs **{pair2[0]} & {pair2[1]}**")
                    st.markdown("")
                    
                    if not court_complete:
                        st.markdown(f"**Game {current_idx + 1} of {max_games}**")
                        
                        col_team1, col_score, col_team2 = st.columns([2, 1.5, 2])
                        
                        with col_team1:
                            st.markdown("### 🔵 Team 1")
                            st.markdown(f"**{pair1[0]}**")
                            st.markdown(f"**{pair1[1]}**")
                        
                        with col_score:
                            st.markdown("### Score")
                            
                            col_s1, col_vs, col_s2 = st.columns([1, 0.3, 1])
                            
                            with col_s1:
                                team1_score = st.number_input(
                                    "Team 1",
                                    min_value=0,
                                    max_value=30,
                                    value=0,
                                    key=f"pair_score_t1_{court_num}_{current_idx}",
                                    label_visibility="collapsed"
                                )
                            
                            with col_vs:
                                st.markdown("## -")
                            
                            with col_s2:
                                team2_score = st.number_input(
                                    "Team 2",
                                    min_value=0,
                                    max_value=30,
                                    value=0,
                                    key=f"pair_score_t2_{court_num}_{current_idx}",
                                    label_visibility="collapsed"
                                )
                            
                            st.markdown("")
                            
                            if st.button("✅ Submit This Game", key=f"pair_submit_{court_num}_{current_idx}", type="primary", use_container_width=True):
                                if team1_score == 0 and team2_score == 0:
                                    st.error("Please enter scores!")
                                else:
                                    team1_won = team1_score > team2_score
                                    
                                    for player in pair1:
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
                                    
                                    for player in pair2:
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
                                        'team1': pair1,
                                        'team2': pair2,
                                        'score': [team1_score, team2_score]
                                    })
                                    
                                    st.session_state.court_game_index[court_num] += 1
                                    st.rerun()
                        
                        with col_team2:
                            st.markdown("### 🔴 Team 2")
                            st.markdown(f"**{pair2[0]}**")
                            st.markdown(f"**{pair2[1]}**")
                    else:
                        st.success("✅ All games completed on this court!")
        
        # Show "Go to Standings" button when all courts complete
        if all_complete:
            st.markdown("")
            st.markdown("")
            col_next1, col_next2, col_next3 = st.columns([1, 2, 1])
            with col_next2:
                st.markdown("### ✅ All Courts Complete!")
                if st.button("📊 Go to Standings", type="primary", use_container_width=True, key="goto_standings"):
                    go_to_page('standings')
    
    # DISPLAY GAMES - Single game formats (Popcorn, Gauntlet, Claim the Throne, Mixed Madness)
    if st.session_state.current_games:
        st.markdown("### 📍 Current Matchups")
        st.markdown("")
        
        for game in st.session_state.current_games:
            court_num = game['court']
            
            # Container for each game
            with st.container():
                # Court header
                st.markdown(f"#### 🏟️ Court {court_num}")
                
                # Create columns for score entry
                col_team1, col_score, col_team2 = st.columns([2, 1.5, 2])
                
                with col_team1:
                    st.markdown("### 🔵 Team 1")
                    st.markdown(f"**{game['team1'][0]}**")
                    st.markdown(f"**{game['team1'][1]}**")
                
                with col_score:
                    st.markdown("### Score")
                    
                    # Score input fields
                    col_s1, col_vs, col_s2 = st.columns([1, 0.3, 1])
                    
                    with col_s1:
                        team1_score = st.number_input(
                            "Team 1",
                            min_value=0,
                            max_value=30,
                            value=0,
                            key=f"score_t1_{court_num}_{st.session_state.current_round}",
                            label_visibility="collapsed"
                        )
                    
                    with col_vs:
                        st.markdown("## -")
                    
                    with col_s2:
                        team2_score = st.number_input(
                            "Team 2",
                            min_value=0,
                            max_value=30,
                            value=0,
                            key=f"score_t2_{court_num}_{st.session_state.current_round}",
                            label_visibility="collapsed"
                        )
                    
                    st.markdown("")
                    
                    # Submit score button
                    if st.button("✅ Submit Score", key=f"submit_{court_num}_{st.session_state.current_round}", type="primary", use_container_width=True):
                        if team1_score == 0 and team2_score == 0:
                            st.error("Please enter scores!")
                        else:
                            # Determine winner
                            team1_won = team1_score > team2_score
                            
                            # Update all player stats
                            for player in game['team1']:
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
                            
                            for player in game['team2']:
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
                            
                            # Save game to history
                            st.session_state.game_scores.append({
                                'round': st.session_state.current_round,
                                'court': court_num,
                                'team1': game['team1'],
                                'team2': game['team2'],
                                'score': [team1_score, team2_score]
                            })
                            
                            st.rerun()
                
                with col_team2:
                    st.markdown("### 🔴 Team 2")
                    st.markdown(f"**{game['team2'][0]}**")
                    st.markdown(f"**{game['team2'][1]}**")
                
                st.markdown("---")
        
        # Show who's sitting out
        if st.session_state.sitting_out:
            st.info(f"🪑 Sitting out this round: {', '.join(st.session_state.sitting_out)}")
        
        # Big "Next Round" button after all games
        st.markdown("")
        st.markdown("")
        col_next1, col_next2, col_next3 = st.columns([1, 2, 1])
        with col_next2:
            st.markdown("### ✅ Round Complete!")
            if st.button("➡️ Generate Next Round", type="primary", use_container_width=True, key="next_round_single"):
                st.session_state.current_round += 1
                generate_new_round()
                st.rerun()
    
    # DISPLAY GROUPS - Multi-game formats (Up/Down River, Scramble, Double Header, Cream of Crop)
    elif st.session_state.court_groups:
        st.markdown("### 📍 Court Groups")
        st.markdown("")
        
        all_complete = True
        
        for group in st.session_state.court_groups:
            court_num = group['court']
            
            if 'players' in group:
                players_list = group['players']
                all_games = generate_court_games(players_list)
                current_idx = st.session_state.court_game_index.get(court_num, 0)
                
                # Check if this court is done
                court_complete = current_idx >= len(all_games)
                if not court_complete:
                    all_complete = False
                
                with st.expander(
                    f"🏟️ Court {court_num} — {', '.join(players_list)}" + 
                    (" ✅ COMPLETE" if court_complete else f" — Game {current_idx + 1}/{len(all_games)}"),
                    expanded=not court_complete
                ):
                    if not court_complete:
                        game = all_games[current_idx]
                        
                        points = st.session_state.court_points.get(court_num, 1)
                        st.markdown(f"**Game {current_idx + 1} of {len(all_games)} — Worth {points} pts**")
                        st.markdown("")
                        
                        cols = st.columns([2, 1, 0.3, 1, 2])
                        
                        with cols[0]:
                            st.markdown(f"**{game['team1'][0]}**")
                            st.markdown(f"**{game['team1'][1]}**")
                        
                        with cols[1]:
                            st.markdown("")
                            if st.button("✅ WIN", key=f"grp_t1_{court_num}_{current_idx}", type="primary", use_container_width=True):
                                for player in game['team1']:
                                    st.session_state.scores[player]['wins'] += 1
                                    st.session_state.scores[player]['games_played'] += 1
                                    st.session_state.scores[player]['points'] += points
                                
                                for player in game['team2']:
                                    st.session_state.scores[player]['losses'] += 1
                                    st.session_state.scores[player]['games_played'] += 1
                                
                                st.session_state.court_game_index[court_num] += 1
                                st.rerun()
                        
                        with cols[2]:
                            st.markdown("### VS")
                        
                        with cols[3]:
                            st.markdown("")
                            if st.button("✅ WIN", key=f"grp_t2_{court_num}_{current_idx}", type="primary", use_container_width=True):
                                for player in game['team2']:
                                    st.session_state.scores[player]['wins'] += 1
                                    st.session_state.scores[player]['games_played'] += 1
                                    st.session_state.scores[player]['points'] += points
                                
                                for player in game['team1']:
                                    st.session_state.scores[player]['losses'] += 1
                                    st.session_state.scores[player]['games_played'] += 1
                                
                                st.session_state.court_game_index[court_num] += 1
                                st.rerun()
                        
                        with cols[4]:
                            st.markdown(f"**{game['team2'][0]}**")
                            st.markdown(f"**{game['team2'][1]}**")
                    else:
                        st.success("✅ All games completed on this court!")
            
            elif 'pairs' in group:
                # Fixed partners format
                pair1, pair2 = group['pairs']
                current_idx = st.session_state.court_game_index.get(court_num, 0)
                max_games = 5
                
                court_complete = current_idx >= max_games
                if not court_complete:
                    all_complete = False
                
                with st.expander(
                    f"🏟️ Court {court_num}" + 
                    (" ✅ COMPLETE" if court_complete else f" — Game {current_idx + 1}/{max_games}"),
                    expanded=not court_complete
                ):
                    st.markdown(f"**{pair1[0]} & {pair1[1]}** vs **{pair2[0]} & {pair2[1]}**")
                    st.markdown("")
                    
                    if not court_complete:
                        points = st.session_state.court_points.get(court_num, 1)
                        st.markdown(f"**Game {current_idx + 1} of {max_games} — Worth {points} pts**")
                        
                        cols = st.columns([2, 1, 0.3, 1, 2])
                        
                        with cols[0]:
                            st.markdown(f"**{pair1[0]}**")
                            st.markdown(f"**{pair1[1]}**")
                        
                        with cols[1]:
                            st.markdown("")
                            if st.button("✅ WIN", key=f"pair_t1_{court_num}_{current_idx}", type="primary", use_container_width=True):
                                for player in pair1:
                                    st.session_state.scores[player]['wins'] += 1
                                    st.session_state.scores[player]['games_played'] += 1
                                    st.session_state.scores[player]['points'] += points
                                
                                for player in pair2:
                                    st.session_state.scores[player]['losses'] += 1
                                    st.session_state.scores[player]['games_played'] += 1
                                
                                st.session_state.court_game_index[court_num] += 1
                                st.rerun()
                        
                        with cols[2]:
                            st.markdown("### VS")
                        
                        with cols[3]:
                            st.markdown("")
                            if st.button("✅ WIN", key=f"pair_t2_{court_num}_{current_idx}", type="primary", use_container_width=True):
                                for player in pair2:
                                    st.session_state.scores[player]['wins'] += 1
                                    st.session_state.scores[player]['games_played'] += 1
                                    st.session_state.scores[player]['points'] += points
                                
                                for player in pair1:
                                    st.session_state.scores[player]['losses'] += 1
                                    st.session_state.scores[player]['games_played'] += 1
                                
                                st.session_state.court_game_index[court_num] += 1
                                st.rerun()
                        
                        with cols[4]:
                            st.markdown(f"**{pair2[0]}**")
                            st.markdown(f"**{pair2[1]}**")
                    else:
                        st.success("✅ All games completed on this court!")
        
        # Show "Next Round" button when all courts complete
        if all_complete:
            st.markdown("")
            st.markdown("")
            col_next1, col_next2, col_next3 = st.columns([1, 2, 1])
            with col_next2:
                st.markdown("### ✅ All Courts Complete!")
                if st.button("➡️ Generate Next Round (or press Enter)", type="primary", use_container_width=True, key="next_round_multi"):
                    st.session_state.current_round += 1
                    generate_new_round()
                    st.rerun()

# ============================================
# PAGE 6: STANDINGS
# ============================================

def show_standings_page():
    # Top navigation
    col_nav1, col_nav2, col_nav3 = st.columns([1, 2, 1])
    
    with col_nav1:
        if st.button("← Back to Play"):
            go_to_page('play')
    
    with col_nav2:
        st.markdown(f"### 🏆 Tournament Standings")
    
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
        
        # Sort by points scored first (most important), then point differential, then wins
        standings.sort(key=lambda x: (x['Points For'], x['Point Diff'], x['Wins']), reverse=True)
        
        # Add ranks
        for i, standing in enumerate(standings):
            standing['Rank'] = i + 1
        
        if standings:
            # Top 3 with medals
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
            
            # Full table
            st.dataframe(standings, use_container_width=True, hide_index=True)
        else:
            st.info("No games played yet!")
    else:
        st.info("No scores recorded yet!")
    
    st.markdown("---")
    
    # PLAYER BREAK SELECTION (if more players than can play simultaneously)
    players = st.session_state.players
    num_courts = st.session_state.num_courts
    max_playing = num_courts * 4
    
    if len(players) > max_playing:
        st.markdown("## 🪑 Manage Player Breaks")
        st.markdown(f"*You have {len(players)} players but only {max_playing} can play at once.*")
        st.markdown("**Select players who want to take a break next round:**")
        
        # Multi-select for players who want breaks
        break_players = st.multiselect(
            "Players on break:",
            options=players,
            default=st.session_state.players_on_break,
            help="These players will sit out the next round"
        )
        
        st.session_state.players_on_break = break_players
        
        active_count = len(players) - len(break_players)
        if active_count < 4:
            st.warning(f"⚠️ You need at least 4 active players to generate a round. Currently: {active_count}")
        elif active_count < max_playing:
            st.info(f"✅ {active_count} players will play next round")
        else:
            st.info(f"✅ {max_playing} players will play, {active_count - max_playing} will sit out randomly")
        
        st.markdown("---")
    
    # Action buttons
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
    elif page == 'configuration':
        show_configuration_page()
    elif page == 'player_entry':
        show_player_entry_page()
    elif page == 'play':
        show_play_page()
    elif page == 'standings':
        show_standings_page()

if __name__ == "__main__":
    main()
