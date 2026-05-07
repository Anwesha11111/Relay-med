"""
Differential Privacy Engine — Adds calibrated Laplace noise to exported statistics and raw records.
Acts as an Anti-Hacking layer to prevent exact data reconstruction by unauthorized entities or models.
"""

import random
import math
from typing import List, Optional


class DifferentialPrivacyEngine:
    """
    Implements the Laplace Mechanism for (ε, 0)-differential privacy.
    sensitivity is the L1 sensitivity of the query function.
    Provides 'Anti-Hacking' noise layers for sensitive medical data.
    """

    def __init__(self, epsilon: float = 0.8):
        if epsilon <= 0:
            raise ValueError("Epsilon must be positive.")
        self.epsilon = epsilon

    def add_laplace_noise(self, value: float, sensitivity: float = 1.0) -> float:
        """Add Laplace noise calibrated to sensitivity/epsilon."""
        scale = sensitivity / self.epsilon
        noise = self._laplace(scale)
        return value + noise

    def protect_value(self, value: float, vital_type: str) -> float:
        """
        Applies noise tailored to the vital type's typical sensitivity.
        This serves as the 'Anti-Hacking' layer for individual data points.
        """
        # Approximate sensitivity based on clinical significance
        sensitivity_map = {
            "heart_rate": 2.0,
            "spo2": 1.0,
            "blood_pressure_systolic": 5.0,
            "blood_pressure_diastolic": 3.0,
            "glucose_fasting": 10.0,
            "temperature": 0.5,
        }
        sensitivity = sensitivity_map.get(vital_type, 1.0)
        return self.add_laplace_noise(value, sensitivity)

    def privatise_list(self, values: List[float], sensitivity: float = 1.0) -> List[float]:
        return [self.add_laplace_noise(v, sensitivity) for v in values]

    def privatise_mean(self, values: List[float], sensitivity: float = 1.0) -> float:
        if not values:
            return 0.0
        true_mean = sum(values) / len(values)
        return self.add_laplace_noise(true_mean, sensitivity / len(values))

    @staticmethod
    def _laplace(scale: float) -> float:
        u = random.uniform(-0.5, 0.5)
        if u == 0: u = 1e-10
        return -scale * math.copysign(1, u) * math.log(1 - 2 * abs(u))


dp_engine = DifferentialPrivacyEngine(epsilon=0.8)
