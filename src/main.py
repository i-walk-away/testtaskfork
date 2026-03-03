from src.app.bootstrap import app
import uvicorn


__all__ = ["app"]


if __name__ == "__main__":
    uvicorn.run(app="src.main:app", host="0.0.0.0", port=8000)
