# Vercel entry point
from server import app

# Vercel expects a handler function
def handler(request):
    return app(request.environ, lambda *args: None)

# For Vercel, we need to expose the app
application = app

if __name__ == "__main__":
    app.run()