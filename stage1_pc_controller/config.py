APP_NAME = "quanquan Stage 1 Controller"

DEFAULT_PORT = "COM3"
DEFAULT_BAUD_RATE = 115200
DEFAULT_LINE_ENDING = "\r"
DEFAULT_FEED_RATE = 500

# These limits are intentionally wide because the real safe range must be
# calibrated on the robot. Tighten them after the first hands-on test.
AXIS_LIMITS = {
    "X": (-9999.0, 9999.0),
    "Y": (-9999.0, 9999.0),
    "Z": (-9999.0, 9999.0),
}

FEED_RATE_LIMITS = (1.0, 6000.0)

POSE_FILE = "poses.json"
