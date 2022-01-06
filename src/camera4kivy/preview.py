from kivy.uix.anchorlayout import AnchorLayout
from kivy.uix.label import Label
from kivy.graphics import Fbo, Color, Rectangle, Scale
from kivy.properties import ColorProperty, StringProperty, ObjectProperty
from kivy.utils import platform
from threading import Thread, Event


if platform == 'android':
    from .preview_camerax import PreviewCameraX as CameraPreview
else:
    from .preview_kivycamera import PreviewKivyCamera as CameraPreview

class Preview(AnchorLayout):

    ##########################################
    # Layout Properties
    ##########################################

    aspect_ratio      = StringProperty()
    orientation       = StringProperty()
    letterbox_color   = ColorProperty('black')
    filepath_callback = ObjectProperty()
    camera_connected = False
    preview = None

    ##########################################
    # Camera Events
    ##########################################

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.anchor_x = 'center'
        self.anchor_y = 'center'
        self.label = Label()
        self.preview = CameraPreview()
        self.add_widget(self.label)
        self.add_widget(self.preview)
        self.camera_connected = False
        for key in ['letterbox_color', 'aspect_ratio',
                    'orientation']:
            if key in kwargs:
                setattr(self, key, kwargs[key])
                if key == 'aspect_ratio':
                    self.preview.set_aspect_ratio(kwargs[key])
                if key == 'orientation':
                    self.preview.set_orientation(kwargs[key])
        self._fbo = None
        self._busy = False
        self._finished = False
        self._image_available = Event()
        self.analyze_resolution = 1024
        self.analyzer_resolution = []
    
    def on_orientation(self,instance,orientation):
        if self.preview and not self.camera_connected:
            self.preview.set_orientation(orientation)

    def on_aspect_ratio(self,instance, aspect_ratio):
        if  self.preview and not self.camera_connected:
            self.preview.set_aspect_ratio(aspect_ratio)

    def on_size(self, layout, size):
        self.label.canvas.clear()
        with self.label.canvas:
            Color (*self.letterbox_color) 
            Rectangle(pos = self.pos, size = self.size)

    ##########################################
    # User Events - All Platforms
    ##########################################

    def connect_camera(self, analyze_pixels_resolution = 1024,
                       enable_analyze_pixels = False, **kwargs):
        self.analyze_resolution = analyze_pixels_resolution
        self.camera_connected = True
        self._finished = False
        if enable_analyze_pixels:
            Thread(target=self.image_scheduler, daemon=True).start()
        self.preview.connect_camera(analyze_callback =
                                        self.analyze_image_callback_schedule,
                                    analyze_proxy_callback =
                                        self.analyze_imageproxy_callback,
                                    canvas_callback =
                                        self.canvas_instructions_callback,
                                    **kwargs)

    def disconnect_camera(self):
        self._image_available.set()
        self._finished = True
        self.preview.disconnect_camera()
        self.camera_connected = False

    def capture_screenshot(self, **kwargs):
        self.preview.capture_screenshot(**kwargs)

    def select_camera(self, camera_id):
        return self.preview.select_camera(camera_id)

    def capture_photo(self, **kwargs):
        self.preview.capture_photo(**kwargs)

    ##########################################
    # User Events - Android Only
    ##########################################

    def capture_video(self, **kwargs):
        self.preview.capture_video(**kwargs)

    def stop_capture_video(self):
        self.preview.stop_capture_video()

    def flash(self):
        return self.preview.flash()

    def focus(self, x, y):
        self.preview.focus(x, y)

    def zoom(self, delta_scale):
        self.preview.zoom(delta_scale)

    ##########################################
    # Data Analysis, Image Size and Schedule
    ##########################################

    def analyze_image_callback_schedule(self, texture, tpos, tscale, mirror):
        # texture : Kivy Texture with same orientation as the Preview
        # tpos   : location of texture in Preview
        # scale : scale from oriented Texture resolution to Preview resolution
        # mirror : true if preview is mirrored
        if not self._busy:
            self._busy = True
            # Create a texture with lower resolution
            if self.analyzer_resolution:
                # DO NOT USE THIS PROTO-FEATURE
                # resolution set by the analyzer [w,h] regardless of
                # Preview orientation or aspect ratio.
                # If the aspect ratio is not the same, there will be invisible
                # letterboxes in the Preview image where analysis does not
                # occur
                fbo_size = self.analyzer_resolution
                fbo_scale = max(texture.width / fbo_size[0],
                                texture.height / fbo_size[1])
                fbo_pos = ((texture.width - fbo_size[0] * fbo_scale) / 2,
                           (texture.height - fbo_size[1] * fbo_scale) / 2)
            else:
                # resolution is 'self.analyze_resolution' along the long edge
                # default value is 1024
                # Optionally set as a connect option.
                # Value is never greater that the sensor resolution.
                # The aspect ratio is always the same as the Preview, thus
                # the full Preview is analyzed.
                fbo_scale = max(max(texture.size) / self.analyze_resolution, 1)
                fbo_size  = (round(texture.size[0]/fbo_scale),
                             round(texture.size[1]/fbo_scale))
                fbo_pos = (0, 0)
            origin    = (round(fbo_size[0]/2), round(fbo_size[1]/2))
            # new or resized texture
            if not self._fbo or self._fbo.size[0] != fbo_size[0]:
                self._fbo = Fbo(size = fbo_size)
            self._fbo.clear()
            with self._fbo:
                Color(1,1,1,1)
                Scale(1,-1,1, origin = origin)
                Rectangle(texture= texture, size = fbo_size)
            self._fbo.draw()

            self.pixels = self._fbo.texture.pixels
            self.im_size = self._fbo.texture.size
            self.tpos = (tpos[0] + fbo_pos[0], tpos[1] + fbo_pos[1])
            self.scale = tscale * fbo_scale
            self.mirror = mirror
            self._image_available.set()

    def image_scheduler(self):
        while True:
            self._image_available.wait()
            self._image_available.clear()
            if self._finished:
                break
            # Must pass pixels not Texture, becuase we are in a different
            # Thread
            self.analyze_pixels_callback(self.pixels, self.im_size, self.tpos,
                                         self.scale, self.mirror)
            self._busy = False

    ##########################################
    # Data Analysis Callbacks 
    ##########################################
    
    # analyze_pixels_callback()
    #
    # pixels        : Kivy Texture pixels, always RGBA
    # size          : size of pixels
    # image_pos     : Bottom left corner of analysis Texture inside the
    #    Preview. AKA the letterbox size plus modified aspect ratio adjustment.
    # image_scale   : Ratio between the analyzed Texture resolution and
    #    screen image resolution.
    # mirror        : True if Preview is mirrored
    
    def analyze_pixels_callback(self, pixels, size, image_pos, image_scale,
                                mirror):
        pass

    # canvas_instructions_callback()
    #
    # texture  : the default texture to bedisplayed in the Priview
    # size     : 
    def canvas_instructions_callback(self, texture, size, pos):
        pass

    # analyze_imageproxy_callback()
    # Android only
    #
    # image_proxy :
    #   https://developer.android.com/reference/androidx/camera/core/ImageProxy
    # image_pos   : Bottom left corner of screen image insie the Preview, the
    #    letterbox size.
    # image_scale : Scale image_proxy size to screen image size.
    # mirror      : True if Preview is mirrored
    # degrees     : clockwise rotation required to make image_proxy the same
    #    orientation as the screen.
    def analyze_imageproxy_callback(self, image_proxy, image_pos, image_scale,
                                    mirror, degrees):
        pass


