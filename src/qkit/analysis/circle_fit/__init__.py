import qkit
import logging

circle_fit_version = qkit.cfg.get("circle_fit_version", 1)

if circle_fit_version == 1:
    from .circle_fit_classic import calibration, circlefit, circuit, utilities
elif circle_fit_version == 2:
    from .circle_fit_2019 import circuit
else:
    logging.warning("Circle fit version not properly set in configuration!")