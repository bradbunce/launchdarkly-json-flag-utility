"""Run the web application."""

import uvicorn


def main():
    """Start the web server."""
    uvicorn.run("web.app:app", host="0.0.0.0", port=8080, reload=True)


if __name__ == "__main__":
    main()
