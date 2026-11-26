#!/bin/bash
# Frames (720x1280) -> upscale 1080x1920 -> captions -> voice + music -> MP4
set -e
cd "$(dirname "$0")"
ffmpeg -y -v error -framerate 30 -i frames/f_%04d.png -i voice.wav -i music.wav \
 -filter_complex "[0:v]scale=1080:1920:flags=lanczos,eq=saturation=1.12:contrast=1.04,vignette=PI/6,ass=captions.ass,format=yuv420p[v];\
[1:a]aresample=48000,adelay=0|0,volume=1.6,highpass=f=70[vo];[2:a]volume=0.22[m];[vo][m]amix=inputs=2:duration=longest:normalize=0,alimiter=limit=0.95[a]" \
 -map "[v]" -map "[a]" -c:v libx264 -preset slow -crf 19 -profile:v high -c:a aac -b:a 192k -movflags +faststart -shortest phantom_traffic_jam_short.mp4
echo done
