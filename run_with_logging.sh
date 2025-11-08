#!/bin/bash
# run_with_logging.sh
#
# Runs the YouTube data processing pipeline and logs all output to a timestamped file.
#
# Usage:
#   bash run_with_logging.sh
#   or
#   ./run_with_logging.sh (after chmod +x run_with_logging.sh)
#
# Output:
#   - Terminal: Real-time output (stdout and stderr)
#   - File: data/run_YYYY-MM-DD_HHMMSS.log (timestamped log file)
#   - File: data/app.log (application logs from logger)

timestamp=$(date +%Y-%m-%d_%H%M%S)
python main.py 2>&1 | tee "data/run_${timestamp}.log"
