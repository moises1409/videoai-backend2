#!/bin/bash
# Update the package list
sudo apt-get update

# Install FFmpeg
sudo apt-get install -y ffmpeg

# Verify FFmpeg installation
ffmpeg -version
