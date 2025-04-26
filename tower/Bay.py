import salabim as sim

from GraphicsSettings import *


class Bay(sim.Component):
    def __init__(self, bay_name, tray, niveau, vlm_location_x, is_first):
        super().__init__()
        self.bay_name = bay_name
        self.tray = tray

        if is_first:
            self.gui_x_left = (vlm_location_x - VLMTHICKNESS / 2) * MULTIPLIER - BAYTHICKNESS
            self.gui_x_right = (vlm_location_x - VLMTHICKNESS / 2) * MULTIPLIER
        else:
            self.gui_x_left = (vlm_location_x + VLMTHICKNESS / 2) * MULTIPLIER
            self.gui_x_right = (vlm_location_x + VLMTHICKNESS /2) * MULTIPLIER + BAYTHICKNESS

        self.gui_y_bottom = LAYERHEIGHT * niveau + BASE_Y
        self.gui_y_top = LAYERHEIGHT * (niveau + 1) + BASE_Y

        self.rect = sim.AnimateRectangle(spec=(self.gui_x_left, self.gui_y_bottom, self.gui_x_right, self.gui_y_top), fillcolor="red", text=self.bay_name, layer=0)
       # self.rect_tray = sim.AnimateRectangle(spec=(self.gui_x_left + 3, self.gui_y_bottom + 3, self.gui_x_right - 3, self.gui_y_top - 3), fillcolor="green", layer=-1)
       # self.rect_tray.remove()
    def process(self):
        self.passivate()
    def set_tray(self, tray):
        if self.tray is not None:
            raise ValueError("Tray already set")
        self.tray = tray
#        self.rect_tray.__setattr__('text', self.tray.tray_name)
        self.rect_tray = sim.AnimateRectangle(spec=(self.gui_x_left + 3, self.gui_y_bottom + 3, self.gui_x_right - 3, self.gui_y_top - 3), fillcolor="green", layer=-1, text=self.tray.tray_name)

    def remove_tray(self):
        if self.tray is None:
            raise ValueError("No tray to remove")
        self.tray = None
        if self.rect_tray is not None:
            self.rect_tray.remove()
        self.rect_tray = None
    def is_empty(self):
        return self.tray is None
