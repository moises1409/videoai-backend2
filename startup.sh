#!/bin/bash

# Install FFmpeg (if needed, through your install_ffmpeg.sh)
bash install_ffmpeg.sh

# Set the PATH to include FFmpeg
export PATH="/home/site/ffmpeg:$PATH"

# Run the Flask application
python app.py




