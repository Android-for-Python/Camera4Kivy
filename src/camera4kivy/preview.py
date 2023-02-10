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
    from .preview_kivycamera import KivyCameraProviderInfo
    
class CameraProviderInfo():
    def get_name(self):
        if platform == 'android':
            provider = 'android'
        else:
            provider = KivyCameraProviderInfo().get_name()
        return provider

class Preview(AnchorLayout):

    ##########################################
    # Layout Properties
    ##########################################

    aspect_ratio      = StringProperty()
    orientation       = StringProperty()
    letterbox_color   = ColorProperty('black')
    filepath_callback = ObjectProperty()
    inhibit_property = False
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
        self.inhibit_property = False
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
        self.camera_connected = False
        self._image_available = Event()
        self.analyze_resolution = 1024
        self.auto_analyze_resolution = []
    
    def on_orientation(self,instance,orientation):
        if self.preview and not self.inhibit_property:
            self.preview.set_orientation(orientation)

    def on_aspect_ratio(self,instance, aspect_ratio):
        if  self.preview and not self.inhibit_property:
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
        self.inhibit_property = True
        self.camera_connected = True
        self._fbo = None
        if enable_analyze_pixels:
            Thread(target=self.image_scheduler, daemon=True).start()
        self.preview.connect_camera(analyze_callback =
                                        self.analyze_image_callback_schedule,
                                    analyze_proxy_callback =
                                        self.analyze_imageproxy_callback,
                                    canvas_callback =
                                        self.possible_canvas_callback,
                                    **kwargs)

    def disconnect_camera(self):
        self._image_available.set()
        self.camera_connected = False
        self.preview.disconnect_camera()
        self.inhibit_property = False

    def capture_screenshot(self, **kwargs):
        self.preview.capture_screenshot(**kwargs)

    def select_camera(self, camera_id):
        return self.preview.select_camera(camera_id)

    ##########################################
    # User Events - some platforms
    ##########################################

    def capture_photo(self, **kwargs):
        self.preview.capture_photo(**kwargs)

    def capture_video(self, **kwargs):
        self.preview.capture_video(**kwargs)

    def stop_capture_video(self):
        self.preview.stop_capture_video()

    ##########################################
    # User Events - Android Only
    ##########################################

    def flash(self, state = None):
        return self.preview.flash(state)

    def torch(self, state):
        return self.preview.torch(state)

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
        # tscale : scale from oriented Texture resolution to Preview resolution
        # mirror : true if preview is mirrored
        if not self._busy:
            self._busy = True
            # Create a texture with lower resolution
            if self.auto_analyze_resolution:
                # resolution set by the analyzer [w,h] regardless of
                # Preview orientation or aspect ratio.
                # If the aspect ratio is not the same the Fbo is distorted.
                # self.scale is a two element array
                fbo_size = self.auto_analyze_resolution
                scale = [tscale * texture.width / fbo_size[0],
                         tscale * texture.height / fbo_size[1]]
            else:
                # resolution is 'self.analyze_resolution' along the long edge
                # default value is 1024
                # Optionally set as a connect option.
                # Value is never greater that the sensor resolution.
                # The aspect ratio is always the same as the Preview
                # self.scale is a scalar
                fbo_scale = max(max(texture.size) / self.analyze_resolution, 1)
                fbo_size  = (round(texture.size[0]/fbo_scale),
                             round(texture.size[1]/fbo_scale))
                scale = tscale * fbo_scale
            origin    = (round(fbo_size[0]/2), round(fbo_size[1]/2))
            # new or resized texture
            if not self._fbo or self._fbo.size[0] != fbo_size[0] or\
               self._fbo.size[1] != fbo_size[1]:
                self._fbo = Fbo(size = fbo_size)
            self._fbo.clear()
            with self._fbo:
                Color(1,1,1,1)
                Scale(1,-1,1, origin = origin)
                Rectangle(texture= texture, size = fbo_size)
            self._fbo.draw()

            # save these for self.analyze_pixels_callback()
            self.pixels = self._fbo.texture.pixels
            self.im_size = self._fbo.texture.size
            self.scale = scale  # 2 ele list , or scalar
            self.tpos = tpos
            self.mirror = mirror
            # ready
            self._image_available.set()

    def image_scheduler(self):
        while True:
            self._image_available.wait()
            self._image_available.clear()
            if not self.camera_connected:
                break
            # Must pass pixels not Texture, becuase we are in a different
            # Thread
            self.analyze_pixels_callback(self.pixels, self.im_size, self.tpos,
                                         self.scale, self.mirror)
            self._busy = False

    def possible_canvas_callback(self, texture, tex_size, tex_pos):
        if self.camera_connected:
            self.canvas_instructions_callback(texture, tex_size, tex_pos)

    ##########################################
    # Data Analysis Callbacks 
    ##########################################
    
    # analyze_pixels_callback()
    #
    # pixels        : Kivy Texture pixels, always RGBA
    # image_size    : size of pixels
    # image_pos     : Bottom left corner of analysis Texture inside the
    #    Preview. AKA the letterbox size plus modified aspect ratio adjustment.
    # image_scale   : Ratio between the analyzed Texture resolution and
    #    screen image resolution.
    # mirror        : True if Preview is mirrored
    
    def analyze_pixels_callback(self, pixels, image_size, image_pos,
                                image_scale, mirror):
        pass

    # canvas_instructions_callback()
    #
    # texture  : the default texture to be displayed in the Priview
    # tex_size : texture size with mirror information
    # tex_pos  : texture pos with mirror information
    def canvas_instructions_callback(self, texture, tex_size, tex_pos):
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


