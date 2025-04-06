import salabim as sim

from GraphicsSettings import *


class Bay(sim.Component):
    def __init__(self, bay_name, tray, niveau, vlm_location_x, is_first):
        super().__init__()
        self.bay_name = bay_name
        self.tray = tray

        if is_first:
            self.gui_x_left = vlm_location_x - VLMTHICKNESS - BAYTHICKNESS
            self.gui_x_right = vlm_location_x - VLMTHICKNESS
        else:
            self.gui_x_left = vlm_location_x - VLMTHICKNESS
            self.gui_x_right = vlm_location_x - VLMTHICKNESS + BAYTHICKNESS

        self.gui_y_bottom = LAYERHEIGHT * niveau
        self.gui_y_top = LAYERHEIGHT * (niveau + 1)

        self.rect = sim.AnimateRectangle(spec=(self.gui_x_left, self.gui_y_bottom, self.gui_x_right, self.gui_y_top), fillcolor="red", text=self.bay_name, layer=-1)
    def process(self):
        self.passivate()
    def set_tray(self, tray):
        if self.tray is not None:
            raise ValueError("Tray already set")
        self.tray = tray

    def remove_tray(self):
        if self.tray is None:
            raise ValueError("No tray to remove")
        self.tray = None

    def is_empty(self):
        return self.tray is None
