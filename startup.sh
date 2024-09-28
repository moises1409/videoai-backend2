#!/bin/bash
# Install FFmpeg
bash install_ffmpeg.sh

# Set the PATH to include FFmpeg
export PATH="/home/site/ffmpeg:$PATH"

python app.py



