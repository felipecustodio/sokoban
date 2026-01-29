"""FastAPI backend wrapping sokoban_engine for the web renderer."""

from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from sokoban_engine import Direction, Game, MoveResult, load_collection_with_info

app = FastAPI(title="Sokoban Game Server")

LEVELS_DIR = Path(__file__).resolve().parent.parent / "levels"
GAME_DIR = Path(__file__).resolve().parent

# --- State ---

_current_game: Game | None = None
_current_collection: str = ""
_current_index: int = 0


# --- Request models ---


class LoadRequest(BaseModel):
    filename: str
    index: int = 0


class MoveRequest(BaseModel):
    direction: int  # 0=UP, 1=DOWN, 2=LEFT, 3=RIGHT


class MovePathRequest(BaseModel):
    directions: list[int]


# --- Helpers ---


def _game_state_json(game: Game) -> dict:
    """Convert current game state to JSON-serializable dict."""
    walls: list[list[int]] = []
    floors: list[list[int]] = []

    for row in range(game.height):
        for col in range(game.width):
            if game.is_wall(row, col):
                walls.append([row, col])
            elif game.is_floor(row, col):
                floors.append([row, col])

    player = list(game.player_position)
    boxes = [list(pos) for pos in game.box_positions]
    goals = [list(pos) for pos in game.goal_positions]

    return {
        "width": game.width,
        "height": game.height,
        "walls": walls,
        "floors": floors,
        "player": player,
        "boxes": boxes,
        "goals": goals,
        "is_solved": game.is_solved,
        "move_count": game.move_count,
        "push_count": game.push_count,
        "boxes_on_goals": game.boxes_on_goals,
        "can_undo": game.can_undo,
        "can_redo": game.can_redo,
        "title": game.title,
    }


def _require_game() -> Game:
    if _current_game is None:
        raise HTTPException(status_code=400, detail="No level loaded")
    return _current_game


# --- API Endpoints ---


@app.get("/api/collections")
def list_collections():
    """List available level collection files."""
    files = sorted(
        f.name for f in LEVELS_DIR.iterdir() if f.suffix == ".txt" and f.is_file()
    )
    return {"collections": files}


@app.get("/api/collections/{filename}/levels")
def list_levels(filename: str):
    """List levels in a collection file."""
    path = LEVELS_DIR / filename
    if not path.is_file():
        raise HTTPException(status_code=404, detail=f"Collection not found: {filename}")
    try:
        infos = load_collection_with_info(path)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {
        "filename": filename,
        "levels": [{"index": info.index, "title": info.title} for info in infos],
    }


@app.post("/api/load")
def load_level(req: LoadRequest):
    """Load a level from a collection."""
    global _current_game, _current_collection, _current_index

    path = LEVELS_DIR / req.filename
    if not path.is_file():
        raise HTTPException(
            status_code=404, detail=f"Collection not found: {req.filename}"
        )

    try:
        infos = load_collection_with_info(path)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

    if req.index < 0 or req.index >= len(infos):
        raise HTTPException(
            status_code=400,
            detail=f"Index {req.index} out of range (0-{len(infos) - 1})",
        )

    info = infos[req.index]
    _current_game = info.game
    _current_collection = req.filename
    _current_index = req.index
    return _game_state_json(_current_game)


@app.post("/api/move")
def move(req: MoveRequest):
    """Make a move."""
    game = _require_game()
    if req.direction not in (0, 1, 2, 3):
        raise HTTPException(status_code=400, detail="Invalid direction (must be 0-3)")
    game.move(Direction(req.direction))
    return _game_state_json(game)


@app.post("/api/move-path")
def move_path(req: MovePathRequest):
    """Execute a sequence of moves (walk path). Rolls back on failure."""
    game = _require_game()
    executed = 0
    try:
        for d in req.directions:
            if d not in (0, 1, 2, 3):
                raise ValueError(f"Invalid direction {d}")
            result = game.move(Direction(d))
            executed += 1
            if result in (MoveResult.BLOCKED_WALL, MoveResult.BLOCKED_BOX):
                raise ValueError(f"Blocked at step {executed}")
    except ValueError as e:
        for _ in range(executed):
            game.undo()
        raise HTTPException(status_code=400, detail=str(e))
    return _game_state_json(game)


@app.post("/api/undo")
def undo():
    """Undo last move."""
    game = _require_game()
    game.undo()
    return _game_state_json(game)


@app.post("/api/redo")
def redo():
    """Redo last undone move."""
    game = _require_game()
    game.redo()
    return _game_state_json(game)


@app.post("/api/reset")
def reset():
    """Reset current level."""
    game = _require_game()
    game.reset()
    return _game_state_json(game)


# --- Static file serving ---

# Serve game static files (js, css)
app.mount("/game/js", StaticFiles(directory=GAME_DIR / "js"), name="game-js")
app.mount("/game/css", StaticFiles(directory=GAME_DIR / "css"), name="game-css")


@app.get("/game/")
@app.get("/game")
def serve_game_page():
    """Serve the main game HTML page."""
    return FileResponse(GAME_DIR / "index.html", media_type="text/html")
