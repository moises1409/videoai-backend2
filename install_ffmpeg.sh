#!/bin/bash
# Download FFmpeg release (statically linked)
mkdir -p /home/site/ffmpeg

# Download FFmpeg static build for Linux
curl -L https://johnvansickle.com/ffmpeg/releases/ffmpeg-release-i686-static.tar.xz | tar -xJ --strip-components=1 -C /home/site/ffmpeg

# Set the PATH to use the downloaded FFmpeg binary
export PATH="/home/site/ffmpeg:$PATH"

# Verify FFmpeg installation
ffmpeg -version

