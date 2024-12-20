import streamlit as st
import json
import os
import datetime
import pandas as pd
import numpy as np
import random
import re
import time
import matplotlib.pyplot as plt
import hashlib

# --------------------- CONFIGURATION AND HELPER FUNCTIONS -----------------------

# Filenames
USER_CONFIG_FILE = "user_config_new.json"
WORKOUT_RESULTS_FILE = "workout_results_new.csv"
WOD_CALENDAR_FILE = "wod_calendar_new.json"
GLOBAL_CONFIG_FILE = "config_new.json"
WOD_DATABASE_FILE = "wod_database_new.json"

# Define all 80+ CrossFit Movements (including runs with distances and standard WODs)
ALL_CROSSFIT_MOVEMENTS = [
    # Foundational
    "Air Squat", "Front Squat", "Overhead Squat", "Back Squat", "Deadlift",
    "Sumo Deadlift High Pull", "Strict Press", "Push Press", "Push Jerk", "Thruster",
    "Bench Press",
    # Gymnastics
    "Strict Pull-Up", "Kipping Pull-Up", "Butterfly Pull-Up", "Chest-to-Bar Pull-Up",
    "Ring Muscle-Up", "Bar Muscle-Up", "Handstand Push-Up", "Deficit Handstand Push-Up",
    "Wall Walk", "Ring Dips", "Bar Dips", "Hanging Leg Raises", "Knees-to-Elbow",
    "GHD Sit-Ups", "V-Ups", "Hollow Rocks", "Superman Rocks", "Pistol Squat",
    "Standard Rope Climb", "Legless Rope Climb", "Box Jumps", "Box Step-Ups",
    "Burpee Box Jumps", "Standard Burpee", "Bar-Facing Burpee", "Lateral Burpee",
    # Olympic Lifting
    "Snatch", "Power Snatch", "Hang Snatch", "Clean", "Power Clean",
    "Hang Clean", "Split Jerk", "Push Jerk", "Snatch Balance",
    # Dumbbell/Kettlebell
    "Dumbbell Snatch", "Dumbbell Thruster", "Dumbbell Clean and Jerk",
    "Kettlebell Swing (Russian)", "Kettlebell Swing (American)", "Kettlebell Clean and Press",
    "Turkish Get-Up", "Farmer’s Carry",
    # Accessory
    "Bent-Over Rows", "Barbell Rows", "Lateral Raises", "Shrugs",
    "Banded Pull-Aparts", "Reverse Hypers", "Hip Extensions",
    # Cardio (with distances)
    "Run 400m", "Run 1km", "Run 5km",
    "Rowing", "Assault Bike", "Echo Bike", "SkiErg", "Swimming",
    "Single Unders", "Double Unders", "Triple Unders",
    # Strongman
    "Yoke Carry", "Sandbag Clean", "Sandbag Carry", "Sled Push",
    "Sled Pull", "Atlas Stone Lifts", "Tire Flips",
    # Additional Movements (to reach 80+)
    "Burpee", "Mountain Climbers", "Plank", "Russian Twists", "Sit-Ups",
    "Push-Up to T", "Lunges", "Step-Ups", "Burpees with Pull-Up",
    "Plyometric Push-Up", "Broad Jumps", "Jumping Lunges", "Tuck Jumps",
    "Medicine Ball Slams", "Battle Ropes", "Sled Drag", "Farmer's Walk",
    "Thrusters with Dumbbells", "Kettlebell Clean", "Kettlebell Press",
    # Standard CrossFit Workouts
    "Cindy",
    # ... add more as needed
]

# Define body parts targeted by movements (simplified for demonstration)
MOVEMENT_BODY_PART = {
    # Example mapping (to be filled as needed)
    # "Air Squat": "Legs",
    # ...
}

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(stored_password, provided_password):
    return stored_password == hash_password(provided_password)

def load_json_file(filename, default_value):
    if os.path.exists(filename):
        try:
            with open(filename, "r") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            st.warning(f"Could not load {filename}: {e}. Using defaults.")
            return default_value
    else:
        with open(filename, "w") as f:
            json.dump(default_value, f, indent=4)
        return default_value

def save_json_file(filename, data):
    try:
        with open(filename, "w") as f:
            json.dump(data, f, indent=4)
    except IOError as e:
        st.error(f"Could not save to {filename}: {e}")

def load_user_config():
    data = load_json_file(USER_CONFIG_FILE, {"users": {}})
    if "users" not in data:
        data["users"] = {}
        save_user_config(data)
    return data

def save_user_config(data):
    save_json_file(USER_CONFIG_FILE, data)

def load_workout_results():
    if os.path.exists(WORKOUT_RESULTS_FILE):
        try:
            return pd.read_csv(WORKOUT_RESULTS_FILE)
        except Exception as e:
            st.warning(f"Could not load {WORKOUT_RESULTS_FILE}: {e}. Starting fresh.")
            return pd.DataFrame(columns=["User", "Date", "Theme", "Warm-Up", "Strength", "WOD", "Result", "Calories Burned", "Average Heart Rate", "Max Heart Rate"])
    else:
        return pd.DataFrame(columns=["User", "Date", "Theme", "Warm-Up", "Strength", "WOD", "Result", "Calories Burned", "Average Heart Rate", "Max Heart Rate"])

def save_workout_result(user, date, wod, result, calories, avg_hr, max_hr):
    df = load_workout_results()
    new_row = {
        "User": user,
        "Date": date,
        "Theme": wod.get("Theme", "N/A"),
        "Warm-Up": wod.get("Warm-Up", "N/A"),
        "Strength": wod.get("Strength", "N/A"),
        "WOD": wod.get("WOD", "N/A"),
        "Result": result,
        "Calories Burned": calories,
        "Average Heart Rate": avg_hr,
        "Max Heart Rate": max_hr
    }
    new_df = pd.DataFrame([new_row])
    df = pd.concat([df, new_df], ignore_index=True)
    try:
        df.to_csv(WORKOUT_RESULTS_FILE, index=False)
    except IOError as e:
        st.error(f"Could not save workout results: {e}")

def load_wod_calendar():
    return load_json_file(WOD_CALENDAR_FILE, {})

def save_wod_calendar(calendar):
    save_json_file(WOD_CALENDAR_FILE, calendar)

def load_wod_database():
    return load_json_file(WOD_DATABASE_FILE, [])

def save_wod_database(database):
    save_json_file(WOD_DATABASE_FILE, database)

def load_global_config():
    return load_json_file(GLOBAL_CONFIG_FILE, {
        "cluster_centers": [
            [300, 900, 200, 600, 500],
            [200, 600, 150, 400, 300],
            [100, 300, 80, 200, 100]
        ],
        "recommended_wods": {
            "0": {
                "Theme": "Leg Day",
                "Warm-Up": "10 minutes light cardio (e.g., jogging) followed by dynamic leg stretches.",
                "Strength": "3 sets of 5 Back Squats with light weight to build foundational leg strength.",
                "WOD": "AMRAP 10 minutes: 5 Push-Ups, 10 Air Squats, 15 Single Unders (jump rope)"
            },
            "1": {
                "Theme": "Back & Core",
                "Warm-Up": "10 minutes rowing and mobility exercises for the back.",
                "Strength": "4 sets of 6 Deadlifts focusing on form and controlled motion.",
                "WOD": "For Time: 3 Rounds of 10 Pull-Ups, 20 GHD Sit-Ups, 30 Double Unders (jump rope)"
            },
            "2": {
                "Theme": "Upper Body Strength",
                "Warm-Up": "10 minutes of shoulder mobility drills and band work.",
                "Strength": "5 sets of 5 Bench Press with progressive overload.",
                "WOD": "EMOM 12 minutes: 3 Power Cleans + 12 Push-Ups (goal: maintain consistent pacing)"
            },
            "3": {
                "Theme": "Cindy",
                "Warm-Up": "10 minutes of light cardio and dynamic stretching.",
                "Strength": "N/A",
                "WOD": "20 Minute AMRAP: 5 Pull-Ups, 10 Push-Ups, 15 Air Squats"
            }
            # Add more predefined WODs or logic to generate themed WODs
        },
        "themes": [
            "Leg Day",
            "Back & Core",
            "Upper Body Strength",
            "Cardio Blast",
            "Full Body",
            "Olympic Lifting",
            "Gymnastics Skills",
            "Strongman",
            "Cindy",  # Standard WOD
            # ... add more themes as needed
        ]
    })

def save_global_config(data):
    save_json_file(GLOBAL_CONFIG_FILE, data)

def is_username_taken(username, user_data):
    return username in user_data.get("users", {})

def is_email_taken(email, user_data):
    for user in user_data.get("users", {}).values():
        if user.get("email") == email:
            return True
    return False

def register_user(username, email, password, user_data):
    user_data["users"][username] = {
        "email": email,
        "password": hash_password(password),
        "preferred_movements": [],
        "skill_level": 3,
        "intensity": 3,
        "variety": 3
    }
    save_user_config(user_data)

def authenticate_user(email, password, user_data):
    for username, user in user_data.get("users", {}).items():
        if user.get("email") == email:
            if verify_password(user.get("password"), password):
                return username
            else:
                return None
    return None

def generate_warm_up(theme):
    warm_up_options = [
        f"10 minutes of dynamic stretching and light {random.choice(['cardio', 'mobility drills', 'foam rolling'])} focusing on {theme.lower()}.",
        f"5 minutes of jump rope followed by mobility drills targeting {theme.lower()}.",
        f"10 minutes of foam rolling and light kettlebell swings to prepare for {theme.lower()}.",
        f"10 minutes of dynamic stretching and activation exercises for {theme.lower()}."
    ]
    return random.choice(warm_up_options)

def generate_strength(theme, skill_level, intensity):
    # Adjust strength based on skill and intensity
    strength_movement = random.choice(['Front Squat', 'Deadlift', 'Overhead Squat', 'Bench Press', 'Power Clean', 'Snatch'])
    sets = random.randint(3, 5) + (intensity // 2)
    reps = random.randint(3, 8) + (skill_level // 2)
    strength_options = [
        f"{sets} sets of {reps} {strength_movement} at {random.randint(70, 85)}% 1RM.",
        f"{sets} sets of {reps} {strength_movement} focusing on form and control.",
        f"{sets} sets of {reps} {strength_movement} increasing weight each set.",
        f"{sets} sets of {reps} {strength_movement} with short rest periods."
    ]
    return random.choice(strength_options)

def generate_wod(wod_format, movements, skill_level, intensity):
    try:
        if wod_format == "AMRAP":
            duration = random.randint(10, 20) + intensity  # Higher intensity could mean longer duration
            exercises = random.sample(movements, min(4, len(movements)))
            reps = [random.randint(5, 15) + skill_level for _ in range(len(exercises))]
            wod = f"{wod_format} {duration} minutes: " + ", ".join([f"{rep} {ex}" for rep, ex in zip(reps, exercises)])
        elif wod_format == "EMOM":
            duration = random.randint(10, 20) + intensity
            exercises = random.sample(movements, min(3, len(movements)))
            reps = [random.randint(3, 10) + skill_level for _ in range(len(exercises))]
            wod = f"{wod_format} {duration} minutes: " + " + ".join([f"{rep} {ex}" for rep, ex in zip(reps, exercises)])
        elif wod_format == "For Time":
            rounds = random.randint(3, 5) + (intensity // 2)
            exercises = random.sample(movements, min(4, len(movements)))
            reps = [random.randint(5, 15) + skill_level for _ in range(len(exercises))]
            wod = f"For Time: {rounds} Rounds of " + ", ".join([f"{rep} {ex}" for rep, ex in zip(reps, exercises)])
        elif wod_format == "Chipper":
            num_exercises = random.randint(5, 7) + skill_level
            num_exercises = min(num_exercises, len(movements))
            exercises = random.sample(movements, num_exercises)
            reps = [random.randint(10, 20) + intensity for _ in range(num_exercises)]
            wod = f"Chipper: " + ", ".join([f"{rep} {ex}" for rep, ex in zip(reps, exercises)])
        elif wod_format == "Rounds For Time":
            rounds = random.randint(4, 6) + (intensity // 2)
            exercises = random.sample(movements, min(4, len(movements)))
            reps = [random.randint(5, 15) + skill_level for _ in range(len(exercises))]
            wod = f"{rounds} Rounds For Time of: " + ", ".join([f"{rep} {ex}" for rep, ex in zip(reps, exercises)])
        else:
            wod = "Complete the workout as described."
        return wod
    except ValueError as e:
        st.error(f"Error generating WOD: {e}")
        return "Complete the workout as described."

def get_wod_scheme(wod):
    wod_line = wod.get("WOD", "")
    if ":" in wod_line:
        scheme_part = wod_line.split(":", 1)[0].strip()
        return scheme_part
    return None

def prompt_for_result(scheme):
    if scheme is None:
        return "Enter your result (time MM:SS or reps):"
    scheme_lower = scheme.lower()
    if "amrap" in scheme_lower:
        time_match = re.search(r"amrap\s*(\d+)", scheme_lower)
        if time_match:
            time = time_match.group(1)
            return f"AMRAP {time} minutes: Enter total rounds/reps completed"
        else:
            return "AMRAP: Enter total rounds/reps completed"
    elif "for time" in scheme_lower:
        return "For Time: Enter finishing time (MM:SS)"
    elif "emom" in scheme_lower:
        return "EMOM: Enter total reps completed or time taken (MM:SS)"
    elif "chipper" in scheme_lower:
        return "Chipper: Enter finishing time (MM:SS) or how far you got"
    elif "rounds for time" in scheme_lower:
        return "Rounds For Time: Enter completion time (MM:SS)"
    else:
        return "Enter your result (time MM:SS or reps):"

def parse_result_str(result_str):
    if isinstance(result_str, str):
        # Check time format MM:SS
        time_pattern = re.compile(r"^(\d+):(\d+)$")
        match = time_pattern.match(result_str)
        if match:
            minutes, seconds = int(match.group(1)), int(match.group(2))
            return minutes * 60 + seconds
        # Check if it's reps or rounds (e.g., "120 reps", "5 rounds")
        words = result_str.lower().split()
        for w in words:
            if w.isdigit():
                return int(w)
    return np.nan

def extract_movements_from_wod(wod):
    """
    Extracts movement names from the WOD string.
    Example WOD: "AMRAP 13 minutes: 17 Atlas Stone Lifts, 10 Chest-to-Bar Pull-Up, 18 Assault Bike, 14 Tuck Jumps"
    Returns: ['Atlas Stone Lifts', 'Chest-to-Bar Pull-Up', 'Assault Bike', 'Tuck Jumps']
    """
    try:
        movements_part = wod['WOD'].split(':', 1)[1]
        movements = [item.strip().split(' ', 1)[1] for item in movements_part.split(',')]
        return movements
    except Exception as e:
        return []

def suggest_ai_wod(user, intensity, skill, variety, wod_database, user_preferences):
    """
    Generates a highly varied and interesting AI-generated WOD based on user preferences and sliders.
    Includes standard CrossFit workouts like "Cindy" periodically.
    """
    themes = load_global_config().get("themes", ["Full Body"])
    theme = random.choice(themes)
    
    warm_up = generate_warm_up(theme)
    
    # Tailor strength based on skill and intensity
    strength = generate_strength(theme, skill, intensity)
    
    # Determine number of movements based on variety
    num_movements = min(variety + 1, len(user_preferences))  # Ensuring at least variety +1 movements
    
    if num_movements <= 0:
        return {
            "Theme": theme,
            "Warm-Up": warm_up,
            "Strength": strength,
            "WOD": "No WOD available. Please update your movement preferences.",
            "Format": "N/A"
        }
    
    # Select unique movements based on user preferences
    selected_movements = random.sample(user_preferences, num_movements)
    
    # Choose WOD format based on skill level
    if skill >= 4:
        wod_format = "For Time"
        rounds = random.randint(3, 5) + (intensity // 2)
        wod = f"For Time: {rounds} Rounds of " + ", ".join([f"{random.randint(5, 15) + skill} {ex}" for ex in selected_movements])
    elif skill >= 2:
        wod_format = "Rounds For Time"
        rounds = random.randint(4, 6) + (intensity // 2)
        wod = f"{rounds} Rounds For Time of: " + ", ".join([f"{random.randint(5, 15) + skill} {ex}" for ex in selected_movements])
    else:
        wod_format = "AMRAP"
        duration = random.randint(12, 20) + intensity
        wod = f"AMRAP {duration} minutes: " + ", ".join([f"{random.randint(5, 15) + skill} {ex}" for ex in selected_movements])
    
    # Occasionally include standard CrossFit WODs like "Cindy"
    if random.random() < 0.1:  # 10% chance
        standard_wods = [w for w in wod_database if w['Theme'] in ["Cindy"]]
        if standard_wods:
            standard_wod = random.choice(standard_wods)
            wod = standard_wod['WOD']
            theme = standard_wod['Theme']
    
    return {
        "Theme": theme,
        "Warm-Up": warm_up,
        "Strength": strength,
        "WOD": wod,
        "Format": wod_format
    }

def ensure_user(user, user_data):
    if user not in user_data.get("users", {}):
        user_data["users"][user] = {
            "email": "",
            "password": "",
            "preferred_movements": [],
            "skill_level": 3,
            "intensity": 3,
            "variety": 3
        }
        save_user_config(user_data)

def initialize_wod_database():
    """
    Generates a diverse WOD database with 10 years' worth of workouts.
    Each WOD has a unique combination of themes, movements, and formats.
    Includes standard CrossFit workouts like "Cindy".
    """
    if not os.path.exists(WOD_DATABASE_FILE):
        st.info("Generating WOD Database. This may take a moment...")
        themes = load_global_config().get("themes", ["Full Body"])
        database = []
        formats = ["AMRAP", "EMOM", "For Time", "Chipper", "Rounds For Time"]
        movements = ALL_CROSSFIT_MOVEMENTS

        # Include standard WODs
        recommended_wods = load_global_config().get("recommended_wods", {})
        for key, wod in recommended_wods.items():
            database.append({
                "Theme": wod["Theme"],
                "Warm-Up": wod["Warm-Up"],
                "Strength": wod["Strength"],
                "WOD": wod["WOD"],
                "Format": "Standard"
            })

        total_wods = len(themes) * 500  # Adjust as needed
        progress_bar = st.progress(0)
        progress = len(database)

        for theme in themes:
            for _ in range(500):  # Number of WODs per theme to reach ~10 years
                wod_format = random.choice(formats)
                # For initial generation, set default skill and intensity
                skill_level = 3
                intensity = 3
                warm_up = generate_warm_up(theme)
                strength = generate_strength(theme, skill_level, intensity)
                wod = generate_wod(wod_format, movements, skill_level, intensity)
                database.append({
                    "Theme": theme,
                    "Warm-Up": warm_up,
                    "Strength": strength,
                    "WOD": wod,
                    "Format": wod_format
                })
                progress += 1
                if progress % 100 == 0:
                    progress_bar.progress(progress / total_wods)
                    time.sleep(0.01)  # Slight delay to update progress bar
        save_wod_database(database)
        if database:
            st.success("WOD Database generated successfully!")
        else:
            st.error("Failed to generate WOD Database.")
    else:
        database = load_wod_database()
        if not database:
            st.error("WOD Database file exists but is empty. Regenerating...")
            os.remove(WOD_DATABASE_FILE)
            initialize_wod_database()
            database = load_wod_database()
    return database

def initialize_wod_calendar(user_preferences, flush=False):
    """
    Generates or regenerates the WOD Calendar based on user preferences.
    If flush=True, existing WOD Calendar is cleared before regeneration.
    Assigns AI-generated WODs to each date based on user preferences.
    """
    if flush or not os.path.exists(WOD_CALENDAR_FILE):
        st.info("Generating WOD Calendar. This may take a moment...")
        calendar = {}
        today = datetime.date.today()
        start_date = today
        database = load_wod_database()
        if not database:
            st.error("WOD Database is empty. Please regenerate the WOD Database first.")
            return calendar
        
        # Filter WODs based on user preferences
        filtered_database = []
        for wod in database:
            movements = extract_movements_from_wod(wod)
            if all(mov in user_preferences for mov in movements):
                filtered_database.append(wod)
        
        if not filtered_database:
            st.error("No WODs match your preferred movements. Please adjust your preferences.")
            return calendar
        
        total_days = 3650  # 10 years
        progress_bar = st.progress(0)
        for i in range(total_days):
            current_date = start_date + datetime.timedelta(days=i)
            date_str = str(current_date)
            if date_str not in calendar:
                # Generate AI WOD based on user preferences
                user_config = load_user_config()
                user = st.session_state.user
                intensity = user_config["users"][user]["intensity"]
                skill = user_config["users"][user]["skill_level"]
                variety = user_config["users"][user]["variety"]
                wod = suggest_ai_wod(
                    user=user,
                    intensity=intensity,
                    skill=skill,
                    variety=variety,
                    wod_database=database,
                    user_preferences=user_preferences
                )
                calendar[date_str] = wod
            if (i+1) % 500 == 0:
                progress_bar.progress((i+1) / total_days)
                time.sleep(0.01)
        save_wod_calendar(calendar)
        st.success("WOD Calendar generated successfully!")
    else:
        calendar = load_wod_calendar()
    return calendar

# --------------------- STREAMLIT UI -----------------------

# IMPORTANT: set_page_config must be the first Streamlit command
st.set_page_config(page_title="CrossFit WOD App", layout="wide")

# Initialize session state for user
if "user" not in st.session_state:
    st.session_state.user = None

# Sidebar Navigation
st.sidebar.title("Navigation")
page = st.sidebar.radio("Go to", [
    "Login",
    "User Configuration",
    "WOD Calendar",
    "WOD History",
    "AI WOD Generator",
    "Performance Charts"  # New Navigation Option
])

# --------------------- LOGIN SCREEN -----------------------
if page == "Login":
    st.title("Login / Register")
    st.write("Please select an option below to continue.")

    options = ["Login", "Register"]
    choice = st.radio("Choose an option", options)

    user_config = load_user_config()

    if choice == "Register":
        st.subheader("Create a New Account")
        new_username = st.text_input("Username")
        new_email = st.text_input("Email")
        new_password = st.text_input("Password", type="password")
        confirm_password = st.text_input("Confirm Password", type="password")

        if st.button("Register"):
            if not new_username or not new_email or not new_password:
                st.error("Please fill out all fields.")
            elif new_password != confirm_password:
                st.error("Passwords do not match.")
            elif is_username_taken(new_username, user_config):
                st.error("Username is already taken.")
            elif is_email_taken(new_email, user_config):
                st.error("Email is already registered.")
            else:
                register_user(new_username, new_email, new_password, user_config)
                st.success(f"Account created successfully! Logged in as '{new_username}'.")
                st.session_state.user = new_username

    elif choice == "Login":
        st.subheader("Login to Your Account")
        login_email = st.text_input("Email")
        login_password = st.text_input("Password", type="password")

        if st.button("Login"):
            if not login_email or not login_password:
                st.error("Please enter both email and password.")
            else:
                authenticated_user = authenticate_user(login_email, login_password, user_config)
                if authenticated_user:
                    st.success(f"Logged in as '{authenticated_user}'.")
                    st.session_state.user = authenticated_user
                else:
                    st.error("Invalid email or password.")

# --------------------- USER CONFIGURATION SCREEN -----------------------
elif page == "User Configuration":
    if st.session_state.user is None:
        st.warning("Please log in first.")
    else:
        st.title("User Configuration")
        st.write("Select your preferred CrossFit movements. Selecting a movement implies you have the necessary equipment.")
        
        user_config = load_user_config()
        user_prefs = user_config["users"][st.session_state.user].get("preferred_movements", [])
        user_skill = user_config["users"][st.session_state.user].get("skill_level", 3)
        user_intensity = user_config["users"][st.session_state.user].get("intensity", 3)
        user_variety = user_config["users"][st.session_state.user].get("variety", 3)
        
        # Display all movements as checkboxes, organized by category for better UX
        categories = {
            "Foundational": [
                "Air Squat", "Front Squat", "Overhead Squat", "Back Squat", "Deadlift",
                "Sumo Deadlift High Pull", "Strict Press", "Push Press", "Push Jerk", "Thruster",
                "Bench Press"
            ],
            "Gymnastics": [
                "Strict Pull-Up", "Kipping Pull-Up", "Butterfly Pull-Up", "Chest-to-Bar Pull-Up",
                "Ring Muscle-Up", "Bar Muscle-Up", "Handstand Push-Up", "Deficit Handstand Push-Up",
                "Wall Walk", "Ring Dips", "Bar Dips", "Hanging Leg Raises", "Knees-to-Elbow",
                "GHD Sit-Ups", "V-Ups", "Hollow Rocks", "Superman Rocks", "Pistol Squat",
                "Standard Rope Climb", "Legless Rope Climb", "Box Jumps", "Box Step-Ups",
                "Burpee Box Jumps", "Standard Burpee", "Bar-Facing Burpee", "Lateral Burpee"
            ],
            "Olympic Lifting": [
                "Snatch", "Power Snatch", "Hang Snatch", "Clean", "Power Clean",
                "Hang Clean", "Split Jerk", "Push Jerk", "Snatch Balance"
            ],
            "Dumbbell/Kettlebell": [
                "Dumbbell Snatch", "Dumbbell Thruster", "Dumbbell Clean and Jerk",
                "Kettlebell Swing (Russian)", "Kettlebell Swing (American)", "Kettlebell Clean and Press",
                "Turkish Get-Up", "Farmer’s Carry"
            ],
            "Accessory": [
                "Bent-Over Rows", "Barbell Rows", "Lateral Raises", "Shrugs",
                "Banded Pull-Aparts", "Reverse Hypers", "Hip Extensions"
            ],
            "Cardio": [
                "Run 400m", "Run 1km", "Run 5km",
                "Rowing", "Assault Bike", "Echo Bike", "SkiErg", "Swimming",
                "Single Unders", "Double Unders", "Triple Unders"
            ],
            "Strongman": [
                "Yoke Carry", "Sandbag Clean", "Sandbag Carry", "Sled Push",
                "Sled Pull", "Atlas Stone Lifts", "Tire Flips"
            ],
            "Additional Movements": [
                "Burpee", "Mountain Climbers", "Plank", "Russian Twists", "Sit-Ups",
                "Push-Up to T", "Lunges", "Step-Ups", "Burpees with Pull-Up",
                "Plyometric Push-Up", "Broad Jumps", "Jumping Lunges", "Tuck Jumps",
                "Medicine Ball Slams", "Battle Ropes", "Sled Drag", "Farmer's Walk",
                "Thrusters with Dumbbells", "Kettlebell Clean", "Kettlebell Press"
                # ... add more as needed
            ]
        }
        
        # Initialize a list to hold selected movements
        selected_movements = user_prefs.copy()
        
        # Display checkboxes categorized
        for category, movements in categories.items():
            with st.expander(category):
                for movement in movements:
                    checkbox_key = f"{category}_{movement}"
                    if st.checkbox(movement, value=movement in user_prefs, key=checkbox_key):
                        if movement not in selected_movements:
                            selected_movements.append(movement)
                    else:
                        if movement in selected_movements:
                            selected_movements.remove(movement)
        
        st.markdown("---")
        
        # Add Skill Level, Intensity, and Variety sliders
        st.subheader("Workout Preferences")
        skill_level = st.slider("Skill Level (1-5)", 1, 5, user_skill, help="Determines the complexity and technicality of the workouts.")
        intensity = st.slider("Intensity (1-5)", 1, 5, user_intensity, help="Determines the overall difficulty and workload of the workouts.")
        variety = st.slider("Variety (1-5)", 1, 5, user_variety, help="Determines the diversity of movements within the workouts.")
        
        if st.button("Save Preferences"):
            user_config["users"][st.session_state.user]["preferred_movements"] = selected_movements
            user_config["users"][st.session_state.user]["skill_level"] = skill_level
            user_config["users"][st.session_state.user]["intensity"] = intensity
            user_config["users"][st.session_state.user]["variety"] = variety
            save_user_config(user_config)
            st.success("Preferences saved successfully.")
        
        st.markdown("---")
        st.subheader("Regenerate WOD Catalog")
        st.write("Click the button below to regenerate your future WOD schedule based on your updated preferences. **This will flush existing WOD data and create a new catalog.**")
        if st.button("Regenerate WOD Catalog"):
            # Regenerate WOD Calendar for the user from today onwards with flushing
            initialize_wod_calendar(selected_movements, flush=True)
            st.success("WOD Catalog regenerated successfully based on your updated preferences.")

# --------------------- WOD CALENDAR SCREEN -----------------------
elif page == "WOD Calendar":
    if st.session_state.user is None:
        st.warning("Please log in first.")
    else:
        st.title("30-Day WOD Calendar")
        st.write("Below is your next 30 days of WODs. Click on today's WOD to enter your results.")
        
        user_config = load_user_config()
        user_prefs = user_config["users"][st.session_state.user].get("preferred_movements", [])
        skill_level = user_config["users"][st.session_state.user].get("skill_level", 3)
        intensity = user_config["users"][st.session_state.user].get("intensity", 3)
        variety = user_config["users"][st.session_state.user].get("variety", 3)
        
        # Load WOD Calendar
        calendar = load_wod_calendar()
        
        # If calendar is empty, initialize it based on user preferences
        if not calendar:
            calendar = initialize_wod_calendar(user_prefs, flush=True)
        
        today = datetime.date.today()
        calendar_items = []
        
        for i in range(30):
            current_date = today + datetime.timedelta(days=i)
            date_str = str(current_date)
            wod = calendar.get(date_str, None)
            if not wod:
                # Assign an AI-generated WOD based on user preferences
                database = load_wod_database()
                if not database:
                    st.error("WOD Database is empty. Please regenerate the WOD Database first.")
                    break
                wod = suggest_ai_wod(
                    user=st.session_state.user,
                    intensity=intensity,
                    skill=skill_level,
                    variety=variety,
                    wod_database=database,
                    user_preferences=user_prefs
                )
                calendar[date_str] = wod
                save_wod_calendar(calendar)
            calendar_items.append((current_date, wod))
        
        # Display calendar as a table with expandable WODs
        for date, wod in calendar_items:
            with st.expander(f"{date} - {wod['Theme']}"):
                st.write(f"**Warm-Up:** {wod['Warm-Up']}")
                st.write(f"**Strength:** {wod['Strength']}")
                st.write(f"**WOD:** {wod['WOD']}")
                
                if date == today:
                    user_df = load_workout_results()
                    user_today = user_df[(user_df["User"] == st.session_state.user) & (user_df["Date"] == date_str)]
                    if not user_today.empty:
                        st.info("You have already recorded results for today.")
                    else:
                        st.subheader("Enter Your Results")
                        # Depending on WOD scheme, customize input
                        wod_scheme = get_wod_scheme(wod)
                        result_prompt = prompt_for_result(wod_scheme)
                        result_input = st.text_input(result_prompt)
                        calories_input = st.number_input("Enter Calories Burned:", min_value=0, step=10)
                        avg_hr_input = st.number_input("Enter Average Heart Rate:", min_value=40, max_value=200, step=1)
                        max_hr_input = st.number_input("Enter Max Heart Rate:", min_value=40, max_value=220, step=1)
                        
                        if st.button(f"Save Result for {date}"):
                            parsed_result = parse_result_str(result_input)
                            if not np.isnan(parsed_result):
                                save_workout_result(
                                    user=st.session_state.user,
                                    date=date_str,
                                    wod=wod,
                                    result=result_input,
                                    calories=calories_input,
                                    avg_hr=avg_hr_input,
                                    max_hr=max_hr_input
                                )
                                st.success("Result saved successfully!")
                            else:
                                st.error("Invalid input format. Please enter time as MM:SS or a number for reps.")
                elif date < today:
                    # Archived WODs
                    user_df = load_workout_results()
                    user_past = user_df[(user_df["User"] == st.session_state.user) & (user_df["Date"] == date_str)]
                    if not user_past.empty:
                        st.subheader("Archived Results")
                        st.write(f"**Result:** {user_past.iloc[0]['Result']}")
                        st.write(f"**Calories Burned:** {user_past.iloc[0]['Calories Burned']}")
                        st.write(f"**Average Heart Rate:** {user_past.iloc[0]['Average Heart Rate']}")
                        st.write(f"**Max Heart Rate:** {user_past.iloc[0]['Max Heart Rate']}")
                    else:
                        st.info("No results recorded for this archived WOD.")
                else:
                    # Future WODs
                    st.info("Results can only be entered for today's WOD.")

# --------------------- WOD HISTORY SCREEN -----------------------
elif page == "WOD History":
    if st.session_state.user is None:
        st.warning("Please log in first.")
    else:
        st.title("WOD History")
        st.write("Here is your workout history.")
        
        df = load_workout_results()
        user_df = df[df["User"] == st.session_state.user]
        
        if user_df.empty:
            st.write("You have no workout history yet.")
        else:
            # Display history
            st.dataframe(user_df[['Date', 'Theme', 'Warm-Up', 'Strength', 'WOD', 'Result', 'Calories Burned', 'Average Heart Rate', 'Max Heart Rate']].sort_values(by="Date", ascending=False))
            
            st.markdown("---")
            st.subheader("Update/View Past Results")
            selected_date = st.selectbox("Select a date to update/view result", user_df["Date"].tolist())
            selected_wod = user_df[user_df["Date"] == selected_date].iloc[0]
            
            st.write(f"**WOD on {selected_date}:**")
            st.write(f"**Theme:** {selected_wod['Theme']}")
            st.write(f"**Warm-Up:** {selected_wod['Warm-Up']}")
            st.write(f"**Strength:** {selected_wod['Strength']}")
            st.write(f"**WOD:** {selected_wod['WOD']}")
            st.write(f"**Result:** {selected_wod['Result']}")
            st.write(f"**Calories Burned:** {selected_wod['Calories Burned']}")
            st.write(f"**Average Heart Rate:** {selected_wod['Average Heart Rate']}")
            st.write(f"**Max Heart Rate:** {selected_wod['Max Heart Rate']}")
            
            st.subheader("Update Result")
            new_result = st.text_input("Enter new result (time MM:SS or reps):", value=selected_wod['Result'])
            new_calories = st.number_input("Enter Calories Burned:", min_value=0, step=10, value=int(selected_wod['Calories Burned']) if not pd.isna(selected_wod['Calories Burned']) else 0)
            new_avg_hr = st.number_input("Enter Average Heart Rate:", min_value=40, max_value=200, step=1, value=int(selected_wod['Average Heart Rate']) if not pd.isna(selected_wod['Average Heart Rate']) else 0)
            new_max_hr = st.number_input("Enter Max Heart Rate:", min_value=40, max_value=220, step=1, value=int(selected_wod['Max Heart Rate']) if not pd.isna(selected_wod['Max Heart Rate']) else 0)
            
            if st.button("Update Result"):
                if parse_result_str(new_result) is not np.nan:
                    # Update the CSV
                    df.loc[(df['User'] == st.session_state.user) & (df['Date'] == selected_date), 'Result'] = new_result
                    df.loc[(df['User'] == st.session_state.user) & (df['Date'] == selected_date), 'Calories Burned'] = new_calories
                    df.loc[(df['User'] == st.session_state.user) & (df['Date'] == selected_date), 'Average Heart Rate'] = new_avg_hr
                    df.loc[(df['User'] == st.session_state.user) & (df['Date'] == selected_date), 'Max Heart Rate'] = new_max_hr
                    try:
                        df.to_csv(WORKOUT_RESULTS_FILE, index=False)
                        st.success("Result updated successfully!")
                    except IOError as e:
                        st.error(f"Could not update workout results: {e}")
                else:
                    st.error("Invalid input format. Please enter time as MM:SS or a number for reps.")

# --------------------- AI WOD GENERATOR SCREEN -----------------------
elif page == "AI WOD Generator":
    if st.session_state.user is None:
        st.warning("Please log in first.")
    else:
        st.title("AI-Generated WOD")
        st.write("Adjust the sliders to set your desired intensity, skill level, and variety, then generate a custom WOD.")

        # Load user preferences
        user_config = load_user_config()
        user_prefs = user_config["users"][st.session_state.user].get("preferred_movements", [])
        user_skill = user_config["users"][st.session_state.user].get("skill_level", 3)
        user_intensity = user_config["users"][st.session_state.user].get("intensity", 3)
        user_variety = user_config["users"][st.session_state.user].get("variety", 3)

        # Sliders for WOD customization
        ai_skill = st.slider("AI Skill Level (1-5)", 1, 5, user_skill)
        ai_intensity = st.slider("AI Intensity (1-5)", 1, 5, user_intensity)
        ai_variety = st.slider("AI Variety (1-5)", 1, 5, user_variety)

        # Initialize generated WOD
        generated_wod = None

        if st.button("Generate WOD"):
            wod_database = load_wod_database()
            if not wod_database:
                st.error("WOD Database is empty. Please regenerate the WOD Database.")
            elif not user_prefs:
                st.error("No preferred movements selected. Please update your preferences in the User Configuration.")
            else:
                generated_wod = suggest_ai_wod(
                    user=st.session_state.user,
                    intensity=ai_intensity,
                    skill=ai_skill,
                    variety=ai_variety,
                    wod_database=wod_database,
                    user_preferences=user_prefs
                )

                st.success("AI-generated WOD created successfully!")

                # Save to WOD history
                history_entry = {
                    "Date": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "Theme": generated_wod["Theme"],
                    "Warm-Up": generated_wod["Warm-Up"],
                    "Strength": generated_wod["Strength"],
                    "WOD": generated_wod["WOD"]
                }
                history = load_json_file("wod_history.json", [])
                history.append(history_entry)
                save_json_file("wod_history.json", history)

        # Display Generated WOD
        if generated_wod:
            st.markdown("---")
            st.subheader("Generated WOD")
            with st.expander(f"{generated_wod['Theme']}"):
                st.write(f"**Warm-Up:** {generated_wod['Warm-Up']}")
                st.write(f"**Strength:** {generated_wod['Strength']}")
                st.write(f"**WOD:** {generated_wod['WOD']}")

            # Result Entry
            st.subheader("Enter Your Results")
            result_prompt = prompt_for_result(get_wod_scheme(generated_wod))
            result_input = st.text_input(result_prompt)
            calories_input = st.number_input("Enter Calories Burned:", min_value=0, step=10)
            avg_hr_input = st.number_input("Enter Average Heart Rate:", min_value=40, max_value=200, step=1)
            max_hr_input = st.number_input("Enter Max Heart Rate:", min_value=40, max_value=220, step=1)

            if st.button("Save Result"):
                parsed_result = parse_result_str(result_input)
                if not np.isnan(parsed_result):
                    save_workout_result(
                        user=st.session_state.user,
                        date=datetime.date.today().strftime("%Y-%m-%d"),
                        wod=generated_wod,
                        result=result_input,
                        calories=calories_input,
                        avg_hr=avg_hr_input,
                        max_hr=max_hr_input
                    )
                    st.success("Result saved successfully!")
                else:
                    st.error("Invalid input format. Please enter time as MM:SS or a number for reps.")

        # Display WOD History
        st.markdown("---")
        st.subheader("WOD History")
        history = load_json_file("wod_history.json", [])
        if history:
            history_df = pd.DataFrame(history)
            st.dataframe(history_df[['Date', 'Theme', 'Warm-Up', 'Strength', 'WOD']])
        else:
            st.info("No WOD history found.")


# --------------------- PERFORMANCE CHARTS SCREEN -----------------------
elif page == "Performance Charts":
    if st.session_state.user is None:
        st.warning("Please log in first.")
    else:
        st.title("Performance Charts")
        st.write("Visualize your workout metrics over time.")
        
        df = load_workout_results()
        user_df = df[df["User"] == st.session_state.user].copy()
        
        if user_df.empty:
            st.write("You have no workout history to display.")
        else:
            # List of metrics available
            metrics = ["Calories Burned", "Average Heart Rate", "Max Heart Rate"]
            
            # Include 'Result' if applicable
            if 'Result' in user_df.columns:
                metrics.append("Result")
            
            selected_metric = st.selectbox("Select a metric to visualize:", metrics)
            
            # Process data based on selected metric
            if selected_metric in ["Calories Burned", "Average Heart Rate", "Max Heart Rate"]:
                # Ensure numeric data
                user_df[selected_metric] = pd.to_numeric(user_df[selected_metric], errors='coerce')
                user_df = user_df.dropna(subset=[selected_metric])
                if user_df.empty:
                    st.write(f"No data available for {selected_metric}.")
                else:
                    # Sort by date
                    user_df['Date'] = pd.to_datetime(user_df['Date'])
                    user_df = user_df.sort_values('Date')
                    
                    # Plotting
                    fig, ax = plt.subplots()
                    ax.plot(user_df['Date'], user_df[selected_metric], marker='o', linestyle='-')
                    ax.set_xlabel('Date')
                    ax.set_ylabel(selected_metric)
                    ax.set_title(f'{selected_metric} Over Time')
                    ax.grid(True)
                    st.pyplot(fig)
            elif selected_metric == "Result":
                # Parse 'Result' to numeric values
                def parse_result(result):
                    if isinstance(result, str):
                        time_pattern = re.compile(r"^(\d+):(\d+)$")
                        match = time_pattern.match(result)
                        if match:
                            minutes, seconds = int(match.group(1)), int(match.group(2))
                            return minutes * 60 + seconds
                        else:
                            # Assume reps
                            parts = result.lower().split()
                            for part in parts:
                                if part.isdigit():
                                    return int(part)
                    return np.nan
                
                user_df['Parsed Result'] = user_df['Result'].apply(parse_result)
                user_df = user_df.dropna(subset=['Parsed Result'])
                if user_df.empty:
                    st.write("No valid data available for Result.")
                else:
                    # Sort by date
                    user_df = user_df.sort_values('Date')
                    
                    # Plotting
                    fig, ax = plt.subplots()
                    ax.plot(user_df['Date'], user_df['Parsed Result'], marker='o', linestyle='-')
                    ax.set_xlabel('Date')
                    ax.set_ylabel('Result (Seconds/Reps)')
                    ax.set_title('Result Over Time')
                    ax.grid(True)
                    st.pyplot(fig)
            else:
                st.write("Selected metric is not available for visualization.")

# --------------------- END OF APP -----------------------
