from kivy.app import App
from kivy.core.window import Window
from threading import Thread
from kivy.clock import mainthread
from kivy.utils import platform
from kivy.core import core_select_lib
from kivy.graphics import Rectangle, Color
from kivy.graphics.texture import Texture
from kivy.core.text import Label as CoreLabel
from kivy.metrics import sp
from gestures4kivy import CommonGestures
from camera4kivy.preview_common import PreviewCommon
if platform in ['macosx', 'ios']:
    from kivy.core.camera import Camera
else:
    from camera4kivy.based_on_kivy_core.camera import Camera

from kivy.logger import Logger

class KivyCameraProviderInfo():
    def get_name(self):
        if Camera:
            provider = str(Camera).split('.')[-2].split('_')[-1] 
        else:
            provider = ""
        return provider


class PreviewKivyCamera(PreviewCommon, CommonGestures):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.error_message = ''
        self.mirror = True
        self.switching_camera = False
        self.starting_camera = False
        self.abort_camera_start = False
        self.enable_zoom_gesture = False
        self.enable_focus_gesture  = False
        self.cg_zoom_level = [1 , 1]
        self.window_width = Window.width
        if platform == 'ios':
            self._enable_on_resume()
        self.provider = KivyCameraProviderInfo().get_name()
            
    def __del__(self):
        self.disconnect_camera()

    @mainthread
    def _enable_on_resume(self):
        app = App.get_running_app()
        app.bind(on_resume = self.on_resume)
            
    def on_resume(self, arg):
        Window.update_viewport()

    def on_size(self, instance, size):
        self.configure_viewport()
        self.configure_texture_crop(None)
        if platform == 'ios' and self.window_width != Window.width:
            if self._camera:
                orientation = self._camera.get_device_orientation()
                if orientation in [1,2,3,4]:
                    self._camera.set_video_orientation(orientation)
        self.canvas.clear()
        if self.error_message:
            self.canvas_text(self.error_message)
        elif self._camera:
            self.on_tex(None)
        else:
            with self.canvas:
                Color(1,1,1,1)
                Rectangle(size = self.view_size, pos = self.view_pos)
        self.window_width = Window.width

    #############################################
    # User Events
    #############################################

    def connect_camera(self,
                       camera_id = '0',
                       mirrored = True,
                       sensor_resolution = [],
                       default_zoom = 1.0,
                       enable_zoom_gesture = True,
                       enable_focus_gesture = True,                         
                       filepath_callback = None,
                       analyze_callback = None,
                       canvas_callback = None,
                       **kwargs):
        self.set_index(camera_id)
        self.set_resolution(sensor_resolution)
        self.set_filepath_callback(filepath_callback)
        self.data_callback = analyze_callback
        self.canvas_callback = canvas_callback
        self.default_zoom = min(max(default_zoom,0),1)
        self.enable_zoom_gesture = enable_zoom_gesture
        self.enable_focus_gesture = enable_focus_gesture        
        self.cg_zoom_level = [self.default_zoom, self.default_zoom]
        if platform == 'ios':
            self.mirror = self.index != 0
        else:
            self.mirror = mirrored
        self.stop_camera()
        #Thread(target=self.start_camera, daemon=True).start()
        self.start_camera()

    def disconnect_camera(self):
        if self.starting_camera:
            # This was related to the Thread above, now redundant?
            self.abort_camera_start = True
        else:
            self.stop_camera()
        
    def select_camera(self, index):
        if self.switching_camera or self.starting_camera:
            return self.index
        self.switching_camera = True
        if platform == 'ios':
            if self._camera:
                self.set_index(index)
                self.mirror = self.index != 0
                self._camera.change_camera_input(self.index)
                self.zoom_abs(self.cg_zoom_level[self.index])                
        else:
            self.stop_camera()
            self.set_index(index)
            self.start_camera()
        self.switching_camera = False
        return index

    # Screenshot
    ######################
    def capture_screenshot(self, location = '.', subdir = '', name = ''):
        view_crop = self.screenshot_crop()
        path = self.capture_path(location, subdir, name, '.jpg')
        tex = self.export_as_image().texture.get_region(*view_crop)
        tex.flip_vertical()
        if platform == 'ios':
            self._camera.save_texture(tex, path)
        else:
            tex.save(path, flipped = False)   
        if self.callback:
            self.callback(path)

    # Photo
    ######################
    def capture_photo(self, location = '.', subdir = '', name = ''):
        if self._camera and self._camera.texture:
            path = self.capture_path(location, subdir, name, '.jpg')
            tex = self._camera.texture.get_region(*self.tex_crop)
            if platform == 'ios':
                self._camera.save_texture(tex, path)
            elif self.provider in ['picamera2', 'opencv']:
                self._camera.photo(path, self.callback)
                return
            else:
                tex.save(path, flipped = False)    
            if self.callback:
                self.callback(path)

    # Video
    ######################

    def capture_video(self, location = '', subdir = '', name = ''):
        if self._camera and self._camera.texture:
            if self.provider in ['picamera2', 'opencv']:
                path = self.capture_path(location, subdir, name, '.mp4')
                self._camera.video_start(path, self.callback)
            
    def stop_capture_video(self):
        if self._camera and self._camera.texture:
            if self.provider in ['picamera2', 'opencv']:
                self._camera.video_stop()
    
    ##############################
    # Preview Widget Touch Events
    ##############################

    # pinch/spread for zoom
    def cgb_zoom(self, touch0, touch1, x, y, scale):
        if self._camera and self.enable_zoom_gesture:
            if platform == 'ios':
                level = max(self.cg_zoom_level[self.index] * scale, 1)
                self.cg_zoom_level[self.index] = level 
                self.zoom_abs(level)
            elif self.provider in ['picamera2']:
                self._camera.zoom(scale)    ###### TODO zoom_level

    # drag
    def cgb_drag(self, touch, x, y, dx, dy):
        if self._camera and self.enable_zoom_gesture:
            if self.provider in ['picamera2']:
                # normalize to preview image
                crop = self.screenshot_crop()
                dx = dx / crop[2]
                dy = dy / crop[3]
                self._camera.drag(dx, dy)
        
    #############################################
    # iOS only User Events
    #############################################

    def zoom_abs(self, level):
        if platform == 'ios' and self._camera:
            self._camera.zoom_level(level)


    #############################################
    # Ignored User Events
    #############################################

    def flash(self, state):
        return 'off'

    def torch(self, state):
        return 'off'

    def focus(self, x, y):
        pass

    def zoom_delta(self, delta_scale):
        pass

    #############################################
    # Parse Arguments
    #############################################

    def set_index(self, index):
        index = index.lower()
        try:
            int(index)
            isint = True
        except:
            isint = False
        if isint:
            self.index = int(index)
        elif index == 'front':
            self.index = 1
        elif index == 'back':
            self.index = 0
        elif index == 'toggle' and self.index == 0:
            self.index = 1
        elif index == 'toggle' and self.index == 1:
            self.index = 0
        else:
            self.index = 0;     

    #############################################
    # Camera Events
    #############################################

    def start_camera(self):
        self.starting_camera = True
        try:
            if not self._sensor_resolution:
                # a max resolution will fall back to the highest available
                # except picamera
                if platform in ['macosx', 'ios']:
                    # default 16:9
                    self._sensor_resolution = [3840, 2160]
                elif self.provider in ['picamera','opencv']:
                    self._sensor_resolution = [1280 , 960]
                elif self.provider in ['picamera2']:
                    self._sensor_resolution = [800 , 600]
                else:
                    #default 4:3 , value ignored by gi
                    self._sensor_resolution = [6400, 4800]

            if self.provider in ['picamera2', 'opencv']:
                context = self
            else:
                context = None
            self._camera = Camera(index= self.index,
                                  resolution = self._sensor_resolution,
                                  callback = self.camera_error,
                                  context = context)
            self.error_message = ""
        except AttributeError as e:
            #Logger.warning(str(e))
            self.camera_error_message()
        except Exception as e:
            #Logger.warning(str(e))
            if self._camera:
                self.error_message = 'ERROR: Camera internal error.'
            else:
                self.error_message = 'ERROR: No camera provider found.'
            self._camera = None

        if self.error_message:
            self.canvas_text(self.error_message)
            
        if self._camera:
            self._camera.bind(on_load=self.configure_texture_crop)
            self._camera.bind(on_texture=self.on_tex)
            self._camera.start()
        if self.abort_camera_start:
            self.stop_camera()
            self._camera = None
        self.abort_camera_start = False
        self.starting_camera = False

    def on_load(self):
        self.configure_texture_crop(None)

    def on_texture(self):
        self.on_tex(None)

    def camera_error(self):
        self.camera_error_message()
        self.canvas_text(self.error_message)            

    def camera_error_message(self):
        self.error_message = "WARNING: Unable to connect to camera_id '" +\
           str(self.index)+"'.\n" +\
           'Check that the camera is connected.'
        self._camera = None

    def stop_camera(self):
        if self._camera:
            self._camera.stop()
            self._camera.unbind(on_texture=self.on_tex)
            self.clear_texture()
            if self._camera.__class__.__name__ == 'CameraGi':
                self._camera.unload()
            del self._camera
            self._camera = None
            
    #############################################
    # Texture 
    #############################################

    def clear_texture(self):
        if self._camera and self._camera.texture:
            tex_size = self._camera.texture.size
            buf = bytes([255] * tex_size[0] * tex_size[1] * 3)
            fmt = self._camera._format   ## all the providers are 3 byte
            self._camera.texture.blit_buffer(buf, colorfmt= fmt,
                                             bufferfmt='ubyte')
            self.on_tex(None)
            

    def on_tex(self, camera):
        if self._camera:
            tex = self._camera.texture.get_region(*self.tex_crop)

            if self.data_callback:
                self.data_callback(tex, self.view_pos,
                                   self.tscale, self.mirror)
            if self.mirror:
                view_size = (-self.view_size[0], self.view_size[1])
                view_pos = (self.view_pos[0] + self.view_size[0],
                            self.view_pos[1])
            else:
                view_size = self.view_size
                view_pos  = self.view_pos
            self.canvas.clear()
            with self.canvas:
                Color(1,1,1,1)
                Rectangle(texture= tex, size = view_size, pos = view_pos)
                if self.canvas_callback:
                    self.canvas_callback(tex, view_size, view_pos)

    def configure_texture_crop(self, dontcare):
        if not self._camera or not self._camera.texture:
            return
        width_tex, height_tex = self._camera.texture.size
        self.tex_crop = self.crop_for_aspect_orientation(width_tex, height_tex)
        self.tscale = self.view_size[1] / self.tex_crop[3]

    def crop_for_aspect_orientation(self, width_tex, height_tex):
        orientation = self.decode_orientation()
        if self.aspect_ratio == "4:3":
            aspect = 4 / 3
        else:
            aspect = 16 / 9        
        crop_pos_x = 0
        crop_pos_y = 0
        crop_siz_x = width_tex
        crop_siz_y = height_tex   
        if orientation == 'portrait':
            if width_tex < height_tex:
                # Portrait texture
                if height_tex / width_tex > 1.5:
                    # texture is 16:9
                    if self.aspect_ratio == '4:3':
                        crop_siz_y = width_tex * aspect   #1
                        crop_pos_y = (height_tex - crop_siz_y) // 2
                else:
                    # texture is 4:3
                    if self.aspect_ratio == '16:9':
                        crop_siz_x = height_tex // aspect
                        crop_pos_x = (width_tex - crop_siz_x) // 2
            else:
                # Landscape texture
                crop_siz_x = height_tex // aspect
                crop_pos_x = (width_tex - crop_siz_x) // 2
        else: # Landscape
            if width_tex < height_tex:
                # Portrait texture
                crop_siz_y = width_tex // aspect
                crop_pos_y = (width_tex - crop_siz_y) // 2
            else:
                # Landscape texture
                if width_tex / height_tex > 1.5:
                    # texture is 16:9
                    if self.aspect_ratio == '4:3':
                        crop_siz_x = height_tex * aspect
                        crop_pos_x = (width_tex - crop_siz_x) // 2
                else:
                    # texture is 4:3
                    if self.aspect_ratio == '16:9':
                        crop_siz_y = width_tex // aspect
                        crop_pos_y = (height_tex - crop_siz_y) // 2
        return [ int(crop_pos_x), int(crop_pos_y),
                 int(crop_siz_x), int(crop_siz_y)]

    @mainthread
    def canvas_text(self,text):
        label = CoreLabel(font_size = sp(16))
        label.text = text
        label.refresh()        
        if label.texture:
            pos = [self.view_pos[0] +\
                   (self.view_size[0] - label.texture.size[0]) / 2,
                   self.view_pos[1] + self.view_size[1] / 2]            
            with self.canvas:
                Color(0.6,0.6,0.6,1)
                Rectangle(size = self.view_size, pos = self.view_pos)
                Color(1,0,0,1)
                Rectangle(size=label.texture.size,
                          pos=pos,
                          texture=label.texture)
            
