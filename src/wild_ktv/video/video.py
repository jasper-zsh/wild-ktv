from kivy.uix.image import Image

class Video(Image):
    def __init__(self, controller, **kwargs):
        super().__init__(**kwargs)
        self.controller = controller
        self.controller.bind(on_frame=self._on_frame)
    
    def _on_frame(self, instance, value):
        self.texture = value
        self.canvas.ask_update()