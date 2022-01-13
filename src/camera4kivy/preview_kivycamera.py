from threading import Thread
from kivy.clock import mainthread
from kivy.utils import platform
from kivy.core import core_select_lib
from kivy.graphics import Rectangle, Color
from kivy.graphics.texture import Texture
from kivy.core.text import Label as CoreLabel
from kivy.metrics import sp
from camera4kivy.based_on_kivy_core.camera import Camera
from camera4kivy.preview_common import PreviewCommon

class PreviewKivyCamera(PreviewCommon):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.error_message = ''
        self.mirror = True
        self.switching_camera = False
        self.starting_camera = False
        self.abort_camera_start = False
        
    def __del__(self):
        self.disconnect_camera()

    def on_size(self, instance, size):
        self.configure_viewport()
        self.configure_texture_crop(None)
        self.canvas.clear()
        if self.error_message:
            self.canvas_text(self.error_message)
        elif self._camera:
            self.on_tex(None)
        else:
            with self.canvas:
                Color(1,1,1,1)
                Rectangle(size = self.view_size, pos = self.view_pos)

    #############################################
    # User Events
    #############################################

    def connect_camera(self,
                       camera_id = '0',
                       mirrored = True,
                       sensor_resolution = [],
                       filepath_callback = None,
                       analyze_callback = None,
                       canvas_callback = None,
                       **kwargs):
        self.set_index(camera_id)
        self.set_resolution(sensor_resolution)
        self.set_filepath_callback(filepath_callback)
        self.data_callback = analyze_callback
        self.canvas_callback = canvas_callback
        self.mirror = mirrored
        self.stop_camera()
        Thread(target=self.start_camera, daemon=True).start()

    def disconnect_camera(self):
        if self.starting_camera:
            self.abort_camera_start = True
        else:
            self.stop_camera()
        
    def select_camera(self, index):
        if self.switching_camera or self.starting_camera:
            return self.index
        self.switching_camera = True
        self.stop_camera()
        self.set_index(index)
        self.start_camera()
        self.switching_camera = False
        return index

    def capture_screenshot(self, location = '.', subdir = '', name = ''):
        view_crop = self.screenshot_crop()
        tex = self.export_as_image().texture.get_region(*view_crop)
        path = self.capture_path(location, subdir, name)
        tex.save(path, flipped = True)   
        if self.callback:
            self.callback(path)

    def capture_photo(self, location = '.', subdir = '', name = ''):
        if self._camera and self._camera.texture:
            path = self.capture_path(location, subdir, name)
            tex = self._camera.texture.get_region(*self.tex_crop)
            tex.save(path, flipped = False)    
            if self.callback:
                self.callback(path)
        
    #############################################
    # Ignored User Events
    #############################################

    def capture_video(self, location = '', subdir = '', name = ''):
        pass
    
    def stop_capture_video(self):
        pass

    def flash(self):
        return 'off'

    def focus(self, x, y):
        pass

    def zoom_delta(self, delta_scale):
        pass

    def zoom_abs(self, scale):
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
                else:
                    # default 4:3 , value ignored by gi
                    self._sensor_resolution = [6400, 4800]
                try:
                    import picamera
                    self._sensor_resolution = [1024 , 768]
                except:
                    pass
            self._camera = Camera(index= self.index,
                                  resolution = self._sensor_resolution,
                                  callback = self.camera_error)
            self.error_message = ""
        except AttributeError:
            self.camera_error_message()
        except:
            if self._camera:
                self.error_message = 'ERROR: Camera internal error.'
            else:
                self.error_message = 'ERROR: No camera provider found.'
            self._camera = None

        if self.error_message:
            self.canvas_text(self.error_message)
                
        if self._camera:
            self._camera.start()
            self._camera.bind(on_load=self.configure_texture_crop)
            self._camera.bind(on_texture=self.on_tex)
        if self.abort_camera_start:
            self.stop_camera()
        self.abort_camera = False
        self.starting_camera = False

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
            if self._camera.__class__.__name__ == 'CameraGi':
                self._camera.unload()
            del self._camera
            self._camera = None
            
    #############################################
    # Texture 
    #############################################

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
        orientation = self.decode_orientation()
        if self.aspect_ratio == "4:3":
            aspect = 4 / 3
        else:
            aspect = 16 / 9        
        width_tex, height_tex = self._camera.texture.size
        crop_pos_x = 0
        crop_pos_y = 0
        crop_siz_x = width_tex
        crop_siz_y = height_tex   
        if orientation == 'portrait':
            crop_siz_x = height_tex / aspect
            crop_pos_x = (width_tex - height_tex / aspect) / 2
        elif width_tex / height_tex > 1.5:
            # texture is 16:9
            if self.aspect_ratio == '4:3':
                crop_siz_x = height_tex * aspect
                crop_pos_x = (width_tex - height_tex * aspect) / 2
        else:
            # texture is 4:3
            if self.aspect_ratio == '16:9':
                crop_siz_y = width_tex / aspect
                crop_pos_y = (height_tex - width_tex / aspect) / 2

        self.tex_crop = [ crop_pos_x, crop_pos_y, crop_siz_x, crop_siz_y]
        self.tscale = self.view_size[1] / crop_siz_y 


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
            
