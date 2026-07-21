import time
from mastodon import Mastodon
from mastodon.errors import MastodonBadGatewayError, MastodonInternalServerError, MastodonServiceUnavailableError
from dotenv import load_dotenv
import os
import random
import re
import json
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo
from PIL import Image, ImageDraw, ImageFont
import logging
from pathlib import Path
from enum import Enum
from color_schemes import THEMES
import traceback

DEBUG_MODE = False
MOCK_DAY_IDX = 0
current_day_idx = MOCK_DAY_IDX


class BracketState(Enum):
    INTRO = 1
    CHARTQ1 = 2
    MATCHQ1 = 3    
    POLL_Q1 = 4
    CHARTQ2 = 5
    MATCHQ2 = 6
    POLL_Q2 = 7
    CHARTQ3 = 8
    MATCHQ3 = 9
    POLL_Q3 = 10
    CHARTQ4 = 11
    MATCHQ4 = 12
    POLL_Q4 = 13
    CHARTS1 = 14
    MATCHS1 = 15
    POLL_S1 = 16
    CHARTS2 = 17
    MATCHS2 = 18
    POLL_S2 = 19
    CHARTFI = 20
    MATCHFI = 21
    POLL_FI = 22
    WRAP_UP = 23

# Automatically detect the directory where mars_madness.py is actually stored
SCRIPT_DIR = Path(__file__).parent.resolve()

# Force all file targets to use exact, absolute paths
ENV_FILE = SCRIPT_DIR / ".env"
STATE_FILE = SCRIPT_DIR / "bracket_state.json"
GRAPHIC_FILE = SCRIPT_DIR / "bracket.png"
LOG_FILE = SCRIPT_DIR / "master_jeff_errors.log"

master_jeff_list = [
    {"name": "Jeff Corwin", "image": "jeff_corwin.jpg"},
    {"name": "Jeff Probst", "image": "jeff_probst.jpg"},
    {"name": "Jeff Dunham", "image": "jeff_dunham.jpg"},
    {"name": "Jeff Foxworthy", "image": "jeff_foxworthy.jpg"},
    {"name": "Jeff Goldblum", "image": "jeff_goldblum.jpg"},
    {"name": "Jeff Gordon", "image": "jeff_gordon.jpg"},
    {"name": "Jeffrey Cranor", "image": "jeffrey_cranor.jpg"},
    {"name": "Jeff Daniels", "image": "jeff_daniels.jpg"},
    {"name": "Jeff Bridges", "image": "jeff_bridges.jpg"},
    {"name": "Jeff Tweedy", "image": "jeff_tweedy.jpg"},
    {"name": "Jeff Winger", "image": "jeff_winger.jpg"},
    {"name": "Geoffrey the Giraffe", "image": "geoffrey_the_giraffe.jpg"},
    {"name": "DJ Jazzy Jeff", "image": "dj_jazzy_jeff.jpg"},
]

# master_jeff_list = [
#     {"name": "Jeff Corwin", "image": "jeff_corwin.jpg"},
#     {"name": "Jeff Probst", "image": "jeff_probst.jpg"},
#     {"name": "Jeff Dunham", "image": "jeff_dunham.jpg"},
#     {"name": "Jeff Foxworthy", "image": "jeff_foxworthy.jpg"},
#     {"name": "Jeff Goldblum", "image": "jeff_goldblum.jpg"},
#     {"name": "Jeff Gordon", "image": "jeff_gordon.jpg"},
#     {"name": "Jeffrey Cranor", "image": "jeffrey_cranor.jpg"},
#     {"name": "Jeff Daniels", "image": "jeff_daniels.jpg"},
#     {"name": "Jeff Bridges", "image": "jeff_bridges.jpg"},
#     {"name": "Jeff Tweedy", "image": "jeff_tweedy.jpg"},
#     {"name": "Jeff Winger", "image": "jeff_winger.jpg"},
#     {"name": "Geoffrey the Giraffe", "image": "geoffrey_the_giraffe.jpg"},
#     {"name": "DJ Jazzy Jeff", "image": "dj_jazzy_jeff.jpg"},
#     {"name": "Geoffrey Chaucer", "image": "geoffrey_chaucer.jpg"},
#     {"name": "Jeff Hardy", "image": "jeff_hardy.jpg"},
#     {"name": "Geoffrey the Butler", "image": "geoffrey_the_butler.jpg"},
#     {"name": "Jeffy", "image": "jeffy.jpg"},
#     {"name": "Jeff Lynne", "image": "jeff_lynne.jpg"},
#     {"name": "Jeff Beck", "image": "jeff_beck.jpg"},
#     {"name": "Jeff the Wiggle", "image": "jeff_the_wiggle.jpg"},
#     {"name": "Jeff Boomhauer", "image": "jeff_boomhauer.jpg"},
#     {"name": "Jeffrey Dean Morgan", "image": "jeffrey_dean_morgan.jpg"},
#     {"name": "Jeffrey Osborne", "image": "jeffrey_osborne.jpg"},
#     {"name": "Jeff Lebowski", "image": "jeff_lebowski.jpg"},
#     {"name": "Jeff the Mannequin", "image": "jeff_the_mannequin.jpg"},
#     {"name": "Jeffrey Wright", "image": "jeffrey_wright.jpg"},
#     {"name": "Jeff the Land Shark", "image": "jeff_the_land_shark.jpg"},
#     {"name": "Jeff Davis", "image": "jeff_davis.jpg"},
#     {"name": "Jeff Cohen", "image": "jeff_cohen.jpg"},
#     {"name": "Jeff Buckley", "image": "jeff_buckley.jpg"},
#     {"name": "Jeff Mangum", "image": "jeff_mangum.jpg"},
#     {"name": "Jeff Koons", "image": "jeff_koons.jpg"},
#     {"name": "Jeff Bezos", "image": "jeff_bezos.jpg"},
#     {"name": "Geoffrey Rush", "image": "geoffrey_rush.jpg"},
#     {"name": "Jeff Garlin", "image": "jeff_garlin.jpg"},
#     {"name": "Jeff Smith", "image": "jeff_smith.jpg"},
#     {"name": "Geoff Rowley", "image": "geoff_rowley.jpg"},
#     {"name": "Geoff Emerick", "image": "geoff_emerick.jpg"},
#     {"name": "Jefferson Starship", "image": "jefferson_starship.jpg"},
#     {"name": "Jefferson Airplane", "image": "jefferson_airplane.jpg"},
#     {"name": "Thomas Jefferson", "image": "thomas_jefferson.jpg"},
#     {"name": "Blind Lemon Jefferson", "image": "blind_lemon_jefferson.jpg"},
#     {"name": "George Jefferson", "image": "george_jefferson.jpg"},
#     {"name": "Jeffrey Katzenberg", "image": "jeffrey_katzenberg.jpg"},
#     {"name": "Jeff Porcaro", "image": "jeff_porcaro.jpg"},
#     {"name": "Jeff Lemire", "image": "jeff_lemire.jpg"},
#     {"name": "Jeff Kinney", "image": "jeff_kinney.jpg"}
# ]

# Explicitly load the .env file from its exact absolute path
load_dotenv(dotenv_path=ENV_FILE)

# Update your logging setup to point to the exact log file path
logging.basicConfig(
    filename=LOG_FILE,
    level=logging.ERROR,
    format="%(asctime)s - %(levelname)s - %(message)s",
)

# Only initialize Mastodon if we are in production mode
if DEBUG_MODE:
    mastodon = None
    print(
        f"🤖 RUNNING IN DEBUG MODE: Simulating Day Index {current_day_idx} (No live API calls)"
    )
else:
    current_day_idx = datetime.now().weekday()
    mastodon = Mastodon(
        client_id=os.getenv("client_key"),
        client_secret=os.getenv("client_secret"),
        access_token=os.getenv("access_token"),
        api_base_url="https://mastodon.social",
    )

jeff_categories = [
    "Biggest JILF",
    "Most Majeffstic",
    "Most Accessible",
    "Most Approachable",
    "Most Casual",
    "Best Style",
    "Scrappiest",
    "Jeff of All Trades",
    "Seems Tallest",
    "Most Actualized",
    "Biggest Jeff Booster",
    "Most Aerodynamic",
    "Most Likely to Vape",
    "Wisest Jeff",
    "Sudden Jeff",
    "Most Satisfying Surname",
    "Most Nurturing",
    "Best Dressed",
    "Best Entertainer",
    "Best Eyes",
    "Most Friendly",
    "Best Hair",
    "Best Laugh",
    "Best Personality",
    "Best Smile",
    "Class Clown",
    "Most Likely to Succeed",
    "Most Changed",
    "Most Athletic",
    "Most Stubborn",
    "Most Scary",
    "Most Quotable",
    "Life of the Party",
    "Biggest Gamer",
    "Most likely to win on Jeopardy",
    "Most Creative",
    "JILF: Jeff I'd Like to Fight",
    "JILF: Jeff I'd Like to Forget",
    "Most Un-Majeffstic",
    "Most Inaccessible",
    "Most Unapproachable",
    "Most Formal",
    "Worst Style",
    "Least Scrappy",
    "Master of None Jeff",
    "Seems Shortest",
    "Least Actualized",
    "Biggest Hater",
    "Least Aerodynamic",
    "Least Likely to Vape",
    "Silliest Jeff",
    "Slowest Jeff",
    "Most Awkward Surname",
    "Most Neglectful",
    "Worst Dressed",
    "Most Boring",
    "Worst Eyes",
    "Most Hostile",
    "Worst Hair",
    "Worst Laugh",
    "Worst Personality",
    "Worst Smile",
    "Ultimate Buzzkill",
    "Most Likely to Fail",
    "Least Dynamic",
    "Least Athletic",
    "Most Compliant",
    "Least Scary",
    "Most Forgettable",
    "Wallflower of the Party",
    "Least Likely to be a Gamer",
    "Most Likely to Lose on Jeopardy",
    "Most Mainstream"
]

def addEllipsisIfTooLong(word, max_len=50):
    if len(word) > max_len:
        word = word[: max_len - 1] + "…"
    return word

def advance_state(current_state):
    """Calculates the next chronological step in the state pattern."""
    try:
        return BracketState(current_state.value + 1)
    except ValueError:
        return BracketState.INTRO

def date_to_integer(dt_time):
    return 10000*dt_time.year + 100*dt_time.month + dt_time.day

def draw_bracket_text_node(
    drawing_object,
    x,
    y,
    text,
    font,
    font_size,
    color_scheme,
    node_line_length,
    track_offset,
    title_text="???",
):
    display_text = addEllipsisIfTooLong(text or title_text, max_len=31)

    # LIGHT MODE TEXT: Dark slate for populated items, muted gray for empty slots
    color = color_scheme["text_color"] if text else color_scheme["muted_text_color"]

    # Draw horizontal bracket line
    drawing_object.line(
        [(x, y + track_offset), (x + node_line_length, y + track_offset)],
        fill=color_scheme["track_color"],
        width=color_scheme["track_width"],
    )

    # Render text cleanly above line with background outline stroke
    drawing_object.text(
        (x, y - (font_size // 2) - 4),
        display_text,
        fill=color,
        font=font,
        stroke_width=4,
        stroke_fill=color_scheme["canvas_color"],
    )

def draw_missing_image_fallback(
    draw, name, box_rect, font, border_color="#ff5555"
):
    """Draws an error border box and missing name label if an image fails to load."""
    draw.rectangle(box_rect, outline=border_color, width=4)

    box_left, box_top, box_right, box_bottom = box_rect
    center_x = box_left + (box_right - box_left) // 2
    center_y = box_top + (box_bottom - box_top) // 2

    error_msg = f"[missing image for\n{name}]"
    draw.text(
        (center_x, center_y),
        error_msg,
        fill=border_color,
        font=font,
        anchor="mm",
        align="center",
    )

def draw_single_line_layered(
    draw_obj,
    position,
    text,
    font,
    main_color,
    stroke_color,
    stroke_width,
    bg_padding=(18, 8),
    bg_color=(15, 15, 22),
    anchor="mm",
):
    """Draws a line of text with its own individual backing box to block underlying image details."""
    x, y = position

    # 1. Measure the exact line width and height for a tight per-line box
    bbox = font.getbbox(text)
    text_w = bbox[2] - bbox[0]

    try:
        ascent, descent = font.getmetrics()
        text_h = ascent + descent
    except AttributeError:
        text_h = bbox[3] - bbox[1]

    # pad_x, pad_y = int(bg_padding[0] * 0), int(bg_padding[1] * 0)
    # box_left = x - (text_w // 2) - pad_x - stroke_width*0
    # box_top = y - (text_h // 2) - pad_y
    # box_right = x + (text_w // 2) + pad_x + stroke_width*0
    # box_bottom = y + (text_h // 2) + pad_y

    box_left = x - (text_w // 2) *0.95
    box_top = y - (text_h // 2) *0.75
    box_right = x + (text_w // 2) *0.95
    box_bottom = y + (text_h // 2) *0.75

    # 2. Draw tight individual backing box
    draw_obj.rounded_rectangle(
        [box_left, box_top, box_right, box_bottom],
        radius=8,
        fill=bg_color,
        outline="#000000",
        width=1,
    )

    # 3. Outer Outline Stroke
    draw_obj.text(
        (x, y),
        text,
        font=font,
        fill=main_color,
        anchor=anchor,
        stroke_width=stroke_width,
        stroke_fill=stroke_color,
    )

    # 4. Solid Black Inner Fill
    draw_obj.text(
        (x, y),
        text,
        font=font,
        fill=stroke_color,
        anchor=anchor,
        stroke_width=0,
    )

    # 5. Top Text Color
    draw_obj.text(
        (x, y), text, font=font, fill=main_color, anchor=anchor, stroke_width=0
    )


def draw_multiline_text_layered(
    draw_obj,
    center_position,
    lines,
    font,
    main_color,
    stroke_color,
    stroke_width,
    line_spacing=1.2,
    bg_padding=(20, 10),
    bg_color=(15, 15, 22),
):
    """Renders multiline text where every line gets its own custom-fit backing box."""
    center_x, center_y = center_position

    try:
        ascent, descent = font.getmetrics()
        line_height = int((ascent + descent) * line_spacing)
    except AttributeError:
        line_height = int(50 * line_spacing)

    total_lines = len(lines)
    start_y = center_y - ((total_lines - 1) * line_height // 2)

    for i, line_text in enumerate(lines):
        if not line_text.strip():  # Skip empty spacing lines
            continue
        line_y = start_y + (i * line_height)
        draw_single_line_layered(
            draw_obj=draw_obj,
            position=(center_x, line_y),
            text=line_text,
            font=font,
            main_color=main_color,
            stroke_color=stroke_color,
            stroke_width=stroke_width,
            bg_padding=bg_padding,
            bg_color=bg_color,
            anchor="mm",
        )




def generate_bracket_graphic(state, color_scheme):
    width, height = 1200, 800

    # LIGHT MODE: Crisp cream/off-white canvas color
    img = Image.new("RGB", (width, height), color=color_scheme["canvas_color"])
    draw = ImageDraw.Draw(img)

    # Font sizing control variable
    font_size = 30

    try:
        # Load the unique high-readability font assigned to this specific color profile
        my_font = ImageFont.truetype(color_scheme["font_path"], size=font_size)
    except Exception as font_err:
        # Graceful logging fallback if execution occurs outside standard Mac desktop environments
        print(f"⚠️ Custom legibility font not found, falling back to system default: {font_err}")
        try:
            my_font = ImageFont.load_default(size=font_size)
        except Exception:
            my_font = ImageFont.load_default()

    # Increased line length from 180 to 260 to give titles room and spread the layout
    node_line_length = 260
    color_scheme["track_width"]
    track_offset = 22

    match_list = state["matches"]

    # BORDER BOX
    border_track_width = color_scheme["track_width"] * 4
        # north border
    draw.line([(0, 0), (1200, 0)], fill=color_scheme["border_color"], width=border_track_width)
    # east border
    draw.line([(1200-2, 0), (1200-2, 800) ],fill=color_scheme["border_color"],width=border_track_width)
    # south border
    draw.line([(0, 800-2), (1200, 800-2)],fill=color_scheme["border_color"],width=border_track_width)
    # west border
    draw.line([(0, 0), (0, 800)],fill=color_scheme["border_color"],width=border_track_width)
    border_track_width = color_scheme["track_width"] * 2
    # north border
    draw.line([(0, 0), (1200, 0)], fill=color_scheme["track_color"], width=border_track_width)
    # east border
    draw.line([(1200-2, 0), (1200-2, 800) ],fill=color_scheme["track_color"],width=border_track_width)
    # south border
    draw.line([(0, 800-2), (1200, 800-2)],fill=color_scheme["track_color"],width=border_track_width)
    # west border
    draw.line([(0, 0), (0, 800)],fill=color_scheme["track_color"],width=border_track_width)

    # CONNECTING LINES (Recalculated paths to bridge the new node coordinates seamlessly)
   
    # Q1 & Q2 -> S1 Lines (From end of Col 1 line [60 + 260 = 320] to start of Col 2 [450])
    # draw.line(
    #     [(320, 110), (385, 110), (385, 190), (450, 190)], fill=track_color, width=track_width
    # )
    draw.line([(60 + 260, height * 3/17 + track_offset), (60 + 260 + 60, height * 4/17 + track_offset)], fill=color_scheme["track_color"], width=color_scheme["track_width"])
    # draw.line(
    #     [(320, 330), (385, 330), (385, 250), (450, 250)], fill=track_color, width=track_width
    # )
    draw.line([(60 + 260 , height * 6/17 + track_offset), (60 + 260 + 60, height * 5/17 + track_offset)], fill=color_scheme["track_color"], width=color_scheme["track_width"])

    # Q3 & Q4 -> S2 Lines (From end of Col 1 line [320] to start of Col 2 [450])
    # draw.line(
    #     [(320, 470), (385, 470), (385, 550), (450, 550)], fill=track_color, width=track_width
    # )
    draw.line([(60 + 260 , height * 11/17 + track_offset), (60 + 260 + 60, height * 12/17 + track_offset)], fill=color_scheme["track_color"], width=color_scheme["track_width"])
    # draw.line(
    #     [(320, 690), (385, 690), (385, 610), (450, 610)], fill=track_color, width=track_width
    # )
    draw.line([(60 + 260 , height * 14/17 + track_offset), (60 + 260 + 60, height * 13/17 + track_offset)], fill=color_scheme["track_color"], width=color_scheme["track_width"])

    # S1 & S2 -> Finals Lines (From end of Col 2 line [450 + 260 = 710] to start of Col 3 [840])
    # draw.line(
    #     [(710, 190), (775, 190), (775, 370), (840, 370)], fill=track_color, width=track_width
    # )
    draw.line([(60 + 260 + 60 + 260 , height * 5/17 + track_offset), (60 + 260 + 60 + 260 + 60, height * 8/17 + track_offset)], fill=color_scheme["track_color"], width=color_scheme["track_width"])
    # draw.line(
    #     [(710, 610), (775, 610), (775, 430), (840, 430)], fill=track_color, width=track_width
    # )
    draw.line([(60 + 260 + 60 + 260 , height * 12/17 + track_offset), (60 + 260 + 60 + 260 + 60, height * 9/17 + track_offset)], fill=color_scheme["track_color"], width=color_scheme["track_width"])

    # --- ADJUSTED HORIZONTAL SPACING MAP ---
    # Col 1 (Quarterfinals) X = 60
    # Col 2 (Semifinals)    X = 450  (60 + 260 line length + 130 connector gap)
    # Col 3 (Finals)        X = 840  (450 + 260 line length + 130 connector gap)
    # Right-most edge ends cleanly near X = 1100 (leaving a nice 100px right margin)

    text_nodes = [
        # QUARTERFINALS (Col 1: X = 60)
        {"x": 60, "y": height *  2/17, "text": match_list["0"]["home"], "title_text": "Seed 1"},
        {"x": 60, "y": height *  3/17, "text": match_list["0"]["away"], "title_text": "Seed 8"},
        {"x": 60, "y": height *  6/17, "text": match_list["1"]["home"], "title_text": "Seed 4"},
        {"x": 60, "y": height *  7/17, "text": match_list["1"]["away"], "title_text": "Seed 5"},
        {"x": 60, "y": height * 10/17, "text": match_list["2"]["home"], "title_text": "Seed 2"},
        {"x": 60, "y": height * 11/17, "text": match_list["2"]["away"], "title_text": "Seed 7"},
        {"x": 60, "y": height * 14/17, "text": match_list["3"]["home"], "title_text": "Seed 3"},
        {"x": 60, "y": height * 15/17, "text": match_list["3"]["away"], "title_text": "Seed 6"},
        # SEMIFINALS (Col 2: X = 450)
        {
            "x": 60 + 260 + 60,
            "y": height * 4/17,
            "text": match_list["4"]["home"],
            "title_text": "Winner Q1",
        },
        {
            "x": 60 + 260 + 60,
            "y": height * 5/17,
            "text": match_list["4"]["away"],
            "title_text": "Winner Q2",
        },
        {
            "x": 60 + 260 + 60,
            "y": height * 12/17,
            "text": match_list["5"]["home"],
            "title_text": "Winner Q3",
        },
        {
            "x": 60 + 260 + 60,
            "y": height * 13/17,
            "text": match_list["5"]["away"],
            "title_text": "Winner Q4",
        },
        # FINALS (Col 3: X = 840)
        {
            "x": 60 + 260 + 60 + 260 + 60,
            "y": height * 8/17,
            "text": match_list["6"]["home"],
            "title_text": "Winner S1",
        },
        {
            "x": 60 + 260 + 60 + 260 + 60,
            "y": height * 9/17,
            "text": match_list["6"]["away"],
            "title_text": "Winner S2",
        },
    ]

    for each in text_nodes:
        # draw_bracket_text_node(drawing_object, x, y, text, font, font_size, node_line_length, track_color, track_width, title_text="???")
        draw_bracket_text_node(
            draw,
            each["x"],
            each["y"],
            each["text"],
            my_font,
            font_size,
            color_scheme,
            node_line_length,
            track_offset,
            each["title_text"],
        )

    # Header text 
    draw.text(
        (1200 - 40, height * 1/17),
        f"MASTER JEFF BRACKET: WEEK OF {state['week_start']}",
        fill=color_scheme["text_color"],
        font=my_font,
        anchor="rm",
        stroke_width=2,
        stroke_fill=color_scheme["canvas_color"]
    )

    img.save(GRAPHIC_FILE)

    # DYNAMIC ALT TEXT GENERATION
    alt_text = (
        f"Master Jeff Bracket for the week of {state['week_start']}. "
    )
    alt_text += f"Quarterfinals: 1) {match_list['0']['home'] or 'Seed 1'} vs {match_list['0']['away'] or 'Seed 8'}. "
    alt_text += f"2) {match_list['1']['home'] or 'Seed 4'} vs {match_list['1']['away'] or 'Seed 5'}. "
    alt_text += f"3) {match_list['2']['home'] or 'Seed 2'} vs {match_list['2']['away'] or 'Seed 7'}. "
    alt_text += f"4) {match_list['3']['home'] or 'Seed 3'} vs {match_list['3']['away'] or 'Seed 6'}. "
    alt_text += f"Semifinals: Match 1 has {match_list['4']['home'] or 'Winner Q1'} vs {match_list['4']['away'] or 'Winner Q2'}. "
    alt_text += f"Match 2 has {match_list['5']['home'] or 'Winner Q3'} vs {match_list['5']['away'] or 'Winner Q4'}. "
    alt_text += f"Finals: {match_list['6']['home'] or 'Winner S1'} vs {match_list['6']['away'] or 'Winner S2'}."

    return alt_text

def get_celebrity_hashtag(name):
    """Converts a celebrity name into a clean, valid hashtag.

    e.g., 'DJ Jazzy Jeff!' -> '#DJJazzyJeff'
          'Geoffrey the Butler' -> '#GeoffreytheButler'
    """
    clean_name = re.sub(r"[^a-zA-Z0-9]", "", name)
    return f"#{clean_name}"

def get_celebrity_image_path(celebrity_name):
    """Looks up the image file path from the loaded dictionary list using the 'name' key."""
    for celebrity in master_jeff_list:
        if isinstance(celebrity, dict) and celebrity.get("name") == celebrity_name:
            # Resolve relative to script directory
            return SCRIPT_DIR / "jeff_images" / celebrity.get("image")
    return None

def get_daily_theme():
    """Selects a theme dynamically based on the current date integer."""
    return THEMES[(date_to_integer(datetime.now())) % len(THEMES)]

def generate_matchup_graphic(match_label, left_name, right_name):
    """Creates a 1200x800 canvas with left and right celebrity photos side-by-side."""
    canvas_w, canvas_h = 1200, 800
    top_margin, side_margin, spacing = 4, 4, 2

    # Calculate dimensions for each side lane
    photo_w = (canvas_w - (side_margin * 2) - spacing) // 2
    photo_h = canvas_h - top_margin - side_margin

    # 1. Canvas Setup
    img = Image.new("RGB", (canvas_w, canvas_h), color="#1e1f29")
    draw = ImageDraw.Draw(img)
    font, fallback_font = load_graphic_fonts()

    # 2. Process Left & Right Lanes
    left_box = (side_margin, top_margin, photo_w, photo_h)
    right_box = (side_margin + photo_w + spacing, top_margin, photo_w, photo_h)

    paste_celebrity_side_lane(img, draw, left_name, left_box, fallback_font)
    paste_celebrity_side_lane(img, draw, right_name, right_box, fallback_font)

   
    # 3. Layered Text Overlay
    lines = [match_label.upper(), "", left_name, "versus", right_name]

    draw_multiline_text_layered(
        draw_obj=draw,
        center_position=(canvas_w // 2, canvas_h // 2),
        lines=lines,
        font=font,
        main_color="#ffeeff",
        stroke_color="#000000",
        stroke_width=15,
        line_spacing=1.1,
    )

    # 4. Save Image Asset
    output_path = SCRIPT_DIR / "jeff_matchup.png"
    try:
        img.save(output_path)
        print(f"🎉 Matchup graphic successfully saved to: {output_path}")
        return f"Side by side celebrity matchup photos for {match_label}: {left_name} vs {right_name}"
    except Exception as save_err:
        print(f"❌ Critical error saving compilation image to disk: {save_err}")
        return ""


def get_random_question():
    """Selects a random Jeff category without repeating the previous one
    stored in bracket_state.json, then updates the saved state.
    """
    previous_criteria = None

    # 1. Try to read the previous criteria from state file
    if STATE_FILE.exists():
        try:
            with open(STATE_FILE, "r") as f:
                state_data = json.load(f)
                previous_criteria = state_data.get("previous_criteria")
        except Exception as e:
            print(
                f"⚠️ Warning: Could not read previous criteria from state file: {e}"
            )
            state_data = {}
    else:
        state_data = {}

    # 2. Filter out the previous criteria to prevent consecutive duplicates
    available_categories = [
        cat for cat in jeff_categories if cat != previous_criteria
    ]

    # Fallback to full list if available_categories is empty (e.g. 1-item list)
    if not available_categories:
        available_categories = jeff_categories

    # 3. Select new criteria
    selected_criteria = random.choice(available_categories)

    # 4. Save the new choice back to bracket_state.json
    state_data["previous_criteria"] = selected_criteria
    try:
        with open(STATE_FILE, "w") as f:
            json.dump(state_data, f, indent=4)
    except Exception as e:
        print(f"❌ Error: Failed to save updated criteria to state file: {e}")

    return f"Which Jeff is the {selected_criteria}?"

def get_poll_winner(poll_id, match_details):
    if DEBUG_MODE:
        simulated_winner = random.choice([match_details["home"], match_details["away"]])
        print(f"🔮 [DEBUG] Simulating winner for poll {poll_id}: {simulated_winner}")
        return simulated_winner

    try:
        status = mastodon.status(poll_id)
        poll = status.get("poll")
        if not poll:
            return None

        # Check if poll is expired OR if current time is past expiration + 1 min buffer
        now = datetime.now(timezone.utc)
        poll_expired = poll.get("expired", False)

        if not poll_expired and poll.get("expires_at"):
            expires_at = datetime.fromisoformat(
                poll["expires_at"].replace("Z", "+00:00")
            )
            if now >= expires_at:
                poll_expired = True  # Force expiration check past scheduled end time

        if not poll_expired:
            print(f"⏳ Poll {poll_id} is still marked active by Mastodon.")
            return None

        options = poll["options"]
        if options[0]["votes_count"] >= options[1]["votes_count"]:
            return options[0]["name"]
        else:
            return options[1]["name"]
    except Exception as e:
        print(f"Error fetching poll winner: {e}")
        return None
    

def initialize_new_bracket():
    """Initializes a new bracket layout on Monday by excluding last week's winner

    and randomly sampling 8 new Jeffs from master_jeff_list.
    """
    last_weeks_winner = None

    # 1. Read last_weeks_winner from bracket_state.json if it exists
    if STATE_FILE.exists():
        try:
            with open(STATE_FILE, "r") as f:
                old_state = json.load(f)
                last_weeks_winner = old_state.get("last_weeks_winner")
        except Exception as e:
            print(
                f"⚠️ Warning: Could not read previous state for last_weeks_winner: {e}"
            )

    # 2. Extract plain string names from master_jeff_list (handling dict or string elements)
    all_jeff_names = [
        jeff["name"] if isinstance(jeff, dict) else jeff
        for jeff in master_jeff_list
    ]

    # 3. Exclude last week's winner from the available pool
    eligible_jeffs = [
        name for name in all_jeff_names if name != last_weeks_winner
    ]

    # Fallback safeguard in case the list gets too small
    if len(eligible_jeffs) < 8:
        eligible_jeffs = all_jeff_names

    # 4. Randomly select 8 unique Jeffs for this week's tournament
    selected_jeffs = random.sample(eligible_jeffs, 8)

    # 5. Build the standard 8-team seed matchings: 1v8, 4v5, 2v7, 3v6
    state = {
        "current_state": BracketState.INTRO.name,
        "previous_status_id": None,
        "last_weeks_winner": last_weeks_winner,  # Carry forward for logging/reference
        "week_start": datetime.now().strftime("%Y-%m-%d"),
        "matches": {
            "0": {
                "home": selected_jeffs[0],
                "away": selected_jeffs[7],
                "poll_id": None,
                "winner": None,
                "label": "Quarterfinal 1",
            },  # Monday
            "1": {
                "home": selected_jeffs[3],
                "away": selected_jeffs[4],
                "poll_id": None,
                "winner": None,
                "label": "Quarterfinal 2",
            },  # Tuesday
            "2": {
                "home": selected_jeffs[1],
                "away": selected_jeffs[6],
                "poll_id": None,
                "winner": None,
                "label": "Quarterfinal 3",
            },  # Wednesday
            "3": {
                "home": selected_jeffs[2],
                "away": selected_jeffs[5],
                "poll_id": None,
                "winner": None,
                "label": "Quarterfinal 4",
            },  # Thursday
            "4": {
                "home": None,
                "away": None,
                "poll_id": None,
                "winner": None,
                "label": "Semifinal 1",
            },  # Friday (Winner Q1 vs Winner Q2)
            "5": {
                "home": None,
                "away": None,
                "poll_id": None,
                "winner": None,
                "label": "Semifinal 2",
            },  # Saturday (Winner Q3 vs Winner Q4)
            "6": {
                "home": None,
                "away": None,
                "poll_id": None,
                "winner": None,
                "label": "Finals",
            },  # Sunday (Winner S1 vs Winner S2)
        },
    }

    return state

def load_graphic_fonts():
    """Loads Arial Bold at primary and fallback sizes, with PIL default fallback."""
    try:
        font = ImageFont.truetype(
            "/System/Library/Fonts/Arial Bold.ttf", size=50
        )
        fallback_font = ImageFont.truetype(
            "/System/Library/Fonts/Arial Bold.ttf", size=30
        )
    except Exception:
        font = ImageFont.load_default()
        fallback_font = ImageFont.load_default()
    return font, fallback_font

def load_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r") as f:
            return json.load(f)
    return None

def paste_celebrity_side_lane(
    canvas_img, draw_obj, name, target_box, fallback_font
):
    """Attempts to load, resize, and center a celebrity photo into its half-lane.

    Falls back to a visual error box if the image is missing or corrupt.
    """
    box_left, box_top, photo_w, photo_h = target_box
    image_path = get_celebrity_image_path(name)

    if image_path and image_path.exists():
        try:
            with Image.open(image_path) as celeb_img:
                celeb_img.thumbnail((photo_w, photo_h))

                # Center within assigned half-lane
                x_pos = box_left + (photo_w - celeb_img.width) // 2
                y_pos = box_top + (photo_h - celeb_img.height) // 2

                canvas_img.paste(celeb_img, (x_pos, y_pos))
                return True
        except Exception as img_err:
            print(
                f"⚠️ Warning: Image for '{name}' exists but failed to open: {img_err}"
            )

    # Render fallback box if missing or unreadable
    fallback_rect = [box_left, box_top, box_left + photo_w, box_top + photo_h]
    draw_missing_image_fallback(
        draw_obj, name, fallback_rect, fallback_font
    )
    return False


def post_monday_wrapup(state):
    print("Processing Monday wrap-up before resetting the tournament slate...")
    final_match = state["matches"].get("6")

    if final_match and final_match.get("poll_id"):
        champion = final_match.get("winner")
        if not champion:
            champion = get_poll_winner(final_match["poll_id"], final_match)

        if champion:
            week_label = state.get("week_start", "Current Week")
            announcement_text = f"🏆🥇 MASTER JEFF CHAMPION 🥇🏆\nfor the week of {week_label} is...\n\n{champion.upper()}\n\nThanks for voting!\n\n#MasterJeff"

            try:
                print(f"Replying to the last post with championship announcement...")
                media_ids = []

                if not DEBUG_MODE:
                    champ_poster_path = get_celebrity_image_path(champion)
                    
                    if champ_poster_path and champ_poster_path.exists():
                        # Retry loop for uploading media asset (up to 3 attempts)
                        for attempt in range(3):
                            try:
                                print(f"📤 Uploading champion poster for {champion} (Attempt {attempt + 1}/3)...")
                                alt_desc = f"Poster for the film {champion}"
                                media_dict = mastodon.media_post(
                                    media_file=champ_poster_path,
                                    mime_type="image/jpeg",
                                    description=alt_desc,
                                )
                                media_ids.append(media_dict["id"])
                                break  # Success! Break out of the retry loop.
                            except (MastodonBadGatewayError, MastodonInternalServerError, MastodonServiceUnavailableError) as server_err:
                                print(f"⚠️ Gateway Error ({server_err.status_code}) on champion poster upload. Retrying in 10s...")
                                time.sleep(10)
                            except Exception as img_upload_err:
                                logging.error(f"Fatal error uploading champion poster asset: {img_upload_err}", exc_info=True)
                                print("❌ Direct upload failure, aborting retries.")
                                break
                        else:
                            print("⚠️ Poster upload failed after 3 attempts, proceeding with text-only announcement.")

                    mastodon.status_post(
                        status=announcement_text,
                        in_reply_to_id=state.get("previous_status_id") or final_match["poll_id"], 
                        media_ids=media_ids if media_ids else None,
                        visibility="public",
                    )
                else:
                    print(f"[DEBUG] Simulated Champion Post Deployment:\n{announcement_text}")
                    
            except Exception as api_err:
                logging.error(f"Failed to post championship announcement reply: {api_err}", exc_info=True)


def process_chart_stage(state, match_key):
    """Generates the bracket update image and replies directly to the immediate previous post."""
    match = state["matches"][match_key]
    match_label = match["label"].upper()
    week_label = state.get("week_start", "Current Week")

    try:
        generated_alt_text = generate_bracket_graphic(state, get_daily_theme())
    except Exception as e:
        logging.error(f"Failed to generate bracket image asset: {e}", exc_info=True)
        generated_alt_text = "Master Jeff tournament bracket update."

    reply_text = f"🕺✨ MASTER JEFF BRACKET ✨🕺\nfor {match_label}\nweek of {week_label}\n\n#MasterJeff"

    if DEBUG_MODE:
        print(f"[DEBUG] Simulated Chronological Chart Post for {match_label}")
        return True

    for attempt in range(3):
        try:
            media_dict = mastodon.media_post(
                media_file=GRAPHIC_FILE,
                mime_type="image/png",
                description=generated_alt_text,
            )
            
            # Linear chaining rule: Always reply to the immediate past piece of content
            target_reply_id = state.get("previous_status_id")

            status_response = mastodon.status_post(
                status=reply_text,
                in_reply_to_id=target_reply_id, 
                media_ids=[media_dict["id"]],
                visibility="public",
            )
            
            # Update the rolling position placeholder
            state["previous_status_id"] = status_response["id"]
            return True
        except (MastodonBadGatewayError, MastodonInternalServerError, MastodonServiceUnavailableError) as server_err:
            print(f"⚠️ Gateway Error ({server_err.status_code}) on graphic. Retrying in 10s...")
            time.sleep(10)
        except Exception as e:
            logging.error(f"Fatal exception during chart attachment step: {e}", exc_info=True)
            break
    return False




def process_match_stage(state, match_key):
    """Generates the side-by-side poster image and posts it to the linear chain."""
    match = state["matches"][match_key]
    match_label = match["label"]
    alt_text = ""

    # Dynamic fallback checks to match standard poll logic safety parameters
    if not match["home"] or not match["away"]:
        fallback_jeffs = random.sample(master_jeff_list, 2)
        if not match["home"]:
            match["home"] = (
                fallback_jeffs[0]["name"]
                if isinstance(fallback_jeffs[0], dict)
                else fallback_jeffs[0]
            )
        if not match["away"]:
            match["away"] = (
                fallback_jeffs[1]["name"]
                if isinstance(fallback_jeffs[1], dict)
                else fallback_jeffs[1]
            )

    try:
        print(f"🎨 Generating poster matchup matrix for {match_label}...")
        alt_text = generate_matchup_graphic(
            match_label, match["home"], match["away"]
        )
    except Exception as e:
        print(f"❌ Failed to generate poster matchup asset: {e}")
        return False

    reply_text = f"🕺⚔️ MASTER JEFF MATCHUP ⚔️🕺\n{match_label.upper()}:\n{match['home']} vs {match['away']}\n\n#MasterJeff"

    if DEBUG_MODE:
        print(
            f"[DEBUG] Simulated Chronological Poster Matchup Post for {match_label}"
        )
        return True

    # 1. Ensure path exists and matches jeff_matchup.png
    matchup_img_path = SCRIPT_DIR / "jeff_matchup.png"
    if not matchup_img_path.exists():
        print(f"❌ Error: Matchup graphic file not found at {matchup_img_path}")
        return False

    # 2. Upload and Post with Explicit Terminal Error Reporting
    for attempt in range(1, 4):
        try:
            print(
                f"📤 Uploading graphic to Mastodon (Attempt {attempt}/3)..."
            )
            media_dict = mastodon.media_post(
                media_file=str(matchup_img_path),  # Must be converted to string
                mime_type="image/png",
                description=alt_text,
            )

            target_reply_id = state.get("previous_status_id")

            print("📝 Posting status update to Mastodon...")
            status_response = mastodon.status_post(
                status=reply_text,
                in_reply_to_id=target_reply_id,
                media_ids=[media_dict["id"]],
                visibility="public",
            )

            state["previous_status_id"] = status_response["id"]
            print("✅ Successfully posted matchup graphic!")
            return True

        except Exception as e:
            print(
                f"❌ Fatal error during poster upload/post step (Attempt {attempt}): {e}"
            )
            traceback.print_exc()  # Prints the full stack trace to terminal
            time.sleep(2)

    return False

def process_poll_stage(state, match_key, expires_in_seconds, emojis):
    """Calculates dependencies, parses titles, and publishes the voting poll card."""
    match = state["matches"][match_key]
    
    # Run dynamic missing candidate resolution fallbacks
    if not match["home"] or not match["away"]:
        fallback_movies = random.sample(master_jeff_list, 2)
        if not match["home"]: 
            match["home"] = fallback_movies[0]["name"] if isinstance(fallback_movies[0], dict) else fallback_movies[0]
        if not match["away"]: 
            match["away"] = fallback_movies[1]["name"] if isinstance(fallback_movies[1], dict) else fallback_movies[1]

    jeffA = addEllipsisIfTooLong(match["home"])
    jeffB = addEllipsisIfTooLong(match["away"])

    e1, e2 = random.sample(emojis, 2)
    match_label = match["label"].upper()

    post_text = (
        f"{e1}{e2} MASTER JEFF POLL {e2}{e1}\n{match_label}\n"
        f"{get_random_question()}\n\n"
        f"#MasterJeff {get_celebrity_hashtag(jeffA)} {get_celebrity_hashtag(jeffB)}"
    )

    if DEBUG_MODE:
        print(f"[DEBUG] Simulated Poll Post Deployment:\n{post_text}")
        match["poll_id"] = random.randint(100000, 999999)
        return True

    for attempt in range(3):
        try:
            poll = mastodon.make_poll(options=[jeffA, jeffB], expires_in=expires_in_seconds, multiple=False)
            
            # Linear chaining rule: Always reply to the immediate past piece of content
            target_reply_id = state.get("previous_status_id")

            status_response = mastodon.status_post(
                status=post_text, 
                poll=poll, 
                in_reply_to_id=target_reply_id, 
                visibility="public"
            )
            
            match["poll_id"] = status_response["id"]
            
            # Update the rolling position placeholder
            state["previous_status_id"] = status_response["id"]
            return True
        except (MastodonBadGatewayError, MastodonInternalServerError, MastodonServiceUnavailableError) as server_err:
            print(f"⚠️ Gateway Error ({server_err.status_code}) on poll. Retrying in 10s...")
            time.sleep(10)
        except Exception as e:
            logging.error(f"Fatal error deploying poll entity: {e}", exc_info=True)
            break
    return False

def save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=4)




def main():
    emojis = [
    "🛠️",  
    "🥩", 
    "🔥", 
    "🏎️", 
    "🪚", 
    "🏈", 
    "🍺", 
    "🏕️", 
    "🎣", 
    "🎸", 
    "🎳",  
    "🎮",  
    "🪓", 
    "🥊",
    "🏋️", 
    "🏍️", 
    "⛳", 
    "🏎️", 
    "🧱", 
    "☕", 
    "🍔", 
    "🍕", 
    "🕹️", 
]

    # 1. Load context state
    try:
        state = load_state()
        if state is None:
            state = initialize_new_bracket()
        
        current_state = BracketState[state.get("current_state", BracketState.INTRO.name)]
    except Exception as e:
        logging.error(f"FSM Context Resolution Lifecycle Error: {e}", exc_info=True)
        return

    # 2. Automatically check and populate tournament results from previous days
    for m_id, match in state["matches"].items():
        if match["poll_id"] and not match["winner"]:
            winner = get_poll_winner(match["poll_id"], match)
            if winner:
                match["winner"] = winner
                print(f"✅ Resolved {match['label']}: Winner is {winner}")
            else:
                print(
                    f"⏳ Checked {match['label']} (Poll {match['poll_id']}), but poll is not finalized yet."
                )

    if state["matches"]["0"]["winner"]: state["matches"]["4"]["home"] = state["matches"]["0"]["winner"]
    if state["matches"]["1"]["winner"]: state["matches"]["4"]["away"] = state["matches"]["1"]["winner"]
    if state["matches"]["2"]["winner"]: state["matches"]["5"]["home"] = state["matches"]["2"]["winner"]
    if state["matches"]["3"]["winner"]: state["matches"]["5"]["away"] = state["matches"]["3"]["winner"]
    if state["matches"]["4"]["winner"]: state["matches"]["6"]["home"] = state["matches"]["4"]["winner"]
    if state["matches"]["5"]["winner"]: state["matches"]["6"]["away"] = state["matches"]["5"]["winner"]

    # 3. Dynamic target time math (Closes at 16:59:50 tomorrow minus now) almost 5pm
    LOCAL_TZ = ZoneInfo("America/New_York")
    now = datetime.now(LOCAL_TZ)
    target_today = now.replace(hour=16, minute=59, second=50, microsecond=0)
    target_time = target_today + timedelta(days=1)
    expires_in_seconds = max(1, int((target_time - now).total_seconds()))

    # 4. Map the days of the week to their allowed execution states
    weekday = datetime.now().weekday()  # Monday = 0, Tuesday = 1, etc.
    
    # Define which states are allowed to run on which days
    day_schedules = {
        0: [BracketState.WRAP_UP, BracketState.INTRO, BracketState.CHARTQ1, BracketState.MATCHQ1, BracketState.POLL_Q1], 
        1: [BracketState.CHARTQ2, BracketState.MATCHQ2, BracketState.POLL_Q2],                                          
        2: [BracketState.CHARTQ3, BracketState.MATCHQ3, BracketState.POLL_Q3],                                          
        3: [BracketState.CHARTQ4, BracketState.MATCHQ4, BracketState.POLL_Q4],                                          
        4: [BracketState.CHARTS1, BracketState.MATCHS1, BracketState.POLL_S1],                                          
        5: [BracketState.CHARTS2, BracketState.MATCHS2, BracketState.POLL_S2],                                          
        6: [BracketState.CHARTFI, BracketState.MATCHFI, BracketState.POLL_FI]                                           
    }
    
    allowed_states = day_schedules.get(weekday, [])

    print(f"--- Running FSM Loop for Weekday {weekday} ---")
    
    # 5. Continuous Loop: Run through states sequentially if they belong to today's schedule
    while current_state in allowed_states:
        print(f"Processing State: {current_state.name} ({current_state.value})")
        success = False

        if current_state == BracketState.INTRO:
            success = True

        # --- QUARTERFINALS MATCH STAGES ---
        elif current_state == BracketState.CHARTQ1: success = process_chart_stage(state, "0")
        elif current_state == BracketState.MATCHQ1: success = process_match_stage(state, "0")
        elif current_state == BracketState.POLL_Q1:  success = process_poll_stage(state, "0", expires_in_seconds, emojis)
        
        elif current_state == BracketState.CHARTQ2: success = process_chart_stage(state, "1")
        elif current_state == BracketState.MATCHQ2: success = process_match_stage(state, "1")
        elif current_state == BracketState.POLL_Q2:  success = process_poll_stage(state, "1", expires_in_seconds, emojis)
        
        elif current_state == BracketState.CHARTQ3: success = process_chart_stage(state, "2")
        elif current_state == BracketState.MATCHQ3: success = process_match_stage(state, "2")
        elif current_state == BracketState.POLL_Q3:  success = process_poll_stage(state, "2", expires_in_seconds, emojis)
        
        elif current_state == BracketState.CHARTQ4: success = process_chart_stage(state, "3")
        elif current_state == BracketState.MATCHQ4: success = process_match_stage(state, "3")
        elif current_state == BracketState.POLL_Q4:  success = process_poll_stage(state, "3", expires_in_seconds, emojis)

        # --- SEMIFINALS STAGES ---
        elif current_state == BracketState.CHARTS1: success = process_chart_stage(state, "4")
        elif current_state == BracketState.MATCHS1: success = process_match_stage(state, "4")
        elif current_state == BracketState.POLL_S1:  success = process_poll_stage(state, "4", expires_in_seconds, emojis)
        
        elif current_state == BracketState.CHARTS2: success = process_chart_stage(state, "5")
        elif current_state == BracketState.MATCHS2: success = process_match_stage(state, "5")
        elif current_state == BracketState.POLL_S2:  success = process_poll_stage(state, "5", expires_in_seconds, emojis)

        # --- CHAMPIONSHIP FINALS STAGES ---
        elif current_state == BracketState.CHARTFI: success = process_chart_stage(state, "6")
        elif current_state == BracketState.MATCHFI: success = process_match_stage(state, "6")
        elif current_state == BracketState.POLL_FI:  success = process_poll_stage(state, "6", expires_in_seconds, emojis)
        
        # --- WRAP UP / RESET ---
        elif current_state == BracketState.WRAP_UP:
            post_monday_wrapup(state)
            print("Resetting bracket records completely for the new week...")
            
            new_state = initialize_new_bracket()
            state.clear()
            state.update(new_state)
            
            current_state = BracketState.INTRO
            state["current_state"] = current_state.name
            save_state(state)
            continue

        # Advance state machine immediately if current task returns True
        if success:
            next_state = advance_state(current_state)
            print(f"State {current_state.name} completed. Advancing to: {next_state.name}")
            
            current_state = next_state
            state["current_state"] = current_state.name
            
            try:
                save_state(state)
            except Exception as e:
                logging.error(f"Failed mid-loop state file write: {e}", exc_info=True)
                break
        else:
            print(f"❌ State execution failed or paused at {current_state.name}. Breaking sequence loop.")
            break

    print(f"Finished schedule loop for today. Current retained machine state: {current_state.name}")

if __name__ == "__main__":
    main()
    # alt_text = generate_matchup_graphic(
    #     match_label="Quarterfinal 2",
    #     left_name="Jeff Goldblum",
    #     right_name="Jeff Bridges"
    # )