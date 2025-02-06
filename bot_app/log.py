import logging
from logging.handlers import RotatingFileHandler

# Set up logging configuration
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)  # Set root logger to the lowest level

# Create a rotating file handler for INFO level logging
rotating_handler = RotatingFileHandler(
    "parser.log",  # Log file name
    maxBytes=5 * 1024 * 1024,  # Maximum log file size in bytes (5MB in this example)
    backupCount=5  # Number of backup files to keep
)
rotating_handler.setLevel(logging.INFO)  # Set file handler level to INFO

# Create a console handler for DEBUG level logging
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)  # Set console handler level to DEBUG

# Define the log format
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')

# Attach the formatter to both handlers
rotating_handler.setFormatter(formatter)
console_handler.setFormatter(formatter)

# Add both handlers to the logger
logger.addHandler(rotating_handler)
logger.addHandler(console_handler)
