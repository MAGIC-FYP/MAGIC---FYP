from dataclasses import dataclass,field
import numpy as np

class MUXConfig:
    MUX_SELECT_CHANNELS = [13, 14, 15, 16]
    MUX_ENABLE_CHANNELS = [17, 18, 19, 20, 21, 22]
    # Separated MUX channel configurations
    MUX_DISCRETE_CHANNELS = [17, 18, 19, 20]
    MUX_CONTINUOUS_CHANNELS = [21, 22]
    MUX_GRAVE_CHANNELS = [21]

@dataclass
class ADCConfig:
    pass

@dataclass
class HEConfig:
    SQUARE_SIZE: float = 35.0
    NUM_SENSORS: int = 96
    MAIN_SENSOR_POSITIONS: np.ndarray = field(init=False)
    WHITE_PLAYER_GY_PLACEMENT_LOC: tuple[float, float] = (10.5*35, 35/2)
    BLACK_PLAYER_GY_PLACEMENT_LOC: tuple[float, float] = (1.5*35, 8*35 - 35/2)
    #TODO:CONTINUOUS_SENSOR_POSITIONS: np.ndarray = np.array([])

    def __post_init__(self):
        self.MAIN_SENSOR_POSITIONS = np.array([
            [
                [2.5*self.SQUARE_SIZE + file * self.SQUARE_SIZE, self.SQUARE_SIZE/2 + rank * self.SQUARE_SIZE]
                for file in range(8)
            ]
            for rank in range(8)
        ], dtype=np.float32)

