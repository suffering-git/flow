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
exit_code=$?
echo "==================================================================="
echo "Process exited with code: $exit_code"
echo "Exit code meanings:"
echo "  0   = Normal exit"
echo "  1   = General error"
echo "  130 = Terminated by Ctrl+C (SIGINT)"
echo "  137 = Killed by SIGKILL"
echo "  143 = Terminated by SIGTERM"
echo "==================================================================="
exit $exit_code
