#!/bin/bash

# Install FFmpeg (if needed, through your install_ffmpeg.sh)
bash install_ffmpeg.sh

# Set the PATH to include FFmpeg
export PATH="/home/site/ffmpeg:$PATH"

# Install ImageMagick
apt-get update
apt-get install -y imagemagick

# Check if ImageMagick was installed correctly by running a simple command
if ! magick -version &> /dev/null
then
    echo "ImageMagick could not be installeded."
    exit 1
else
    echo "ImageMagick installed successfully."
fi


# Set the PATH to include ImageMagick
#export PATH="/usr/bin:$PATH"

# Set the ImageMagick binary for MoviePy to use
#export IMAGEMAGICK_BINARY="/usr/bin/magick"

# Run the Flask application
python app.py




