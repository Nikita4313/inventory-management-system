"""Development entry point for the Flask Inventory Management System."""

from inventory import create_app
from inventory.config import Config

app = create_app()

if __name__ == "__main__":
    app.run(
        host="127.0.0.1",
        port=Config.PORT,
        debug=app.config["DEBUG"],
    )
