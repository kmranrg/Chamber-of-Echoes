#!/bin/bash

# Default commit message if none provided
MESSAGE=${1:-"Quick commit"}

git add .
git commit -m "$MESSAGE"
git push origin main