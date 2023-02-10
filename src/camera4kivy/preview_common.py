from kivy.core.window import Window
from kivy.uix.widget import Widget
from kivy.utils import platform

from os import mkdir
from os.path import exists, join
from pathlib import Path
from datetime import datetime
from inspect import ismethod, signature

class PreviewCommon(Widget):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._camera = None
        self._camera_texture = None
        self.view_size = (10, 10)
        self.view_pos = (0, 0)
        self.tex_crop = (0, 0, 10, 10)
        self.tscale = 1
        self.orientation = 'same'
        self.aspect_ratio = '4:3'
        self.callback = None
        self._sensor_resolution = []
        
    #############################################
    # Parse Arguments
    #############################################

    def set_aspect_ratio(self, aspect_ratio):
        if aspect_ratio in ['4:3', '16:9']:
            self.aspect_ratio = aspect_ratio

    def set_orientation(self, orientation):
        orientation = orientation.lower()
        if orientation in ['landscape', 'portrait','same','opposite']:
            self.orientation = orientation

    def set_resolution(self, resolution):
        if resolution and\
           (type(resolution) is tuple or type(resolution) is list) and\
           len(resolution) == 2:
            self._sensor_resolution = (max(resolution), min(resolution))

    def set_filepath_callback(self,callback):
        if callback:
            if not ismethod(callback) or\
               len(signature(callback).parameters) !=1:
                callback = None
            self.callback = callback

    #############################################
    # Viewport
    #############################################

    def configure_viewport(self):
        orientation = self.decode_orientation()
        width_self, height_self = self.size

        if self.aspect_ratio == "4:3":
            aspect = 4/3
        else:
            aspect = 16/9
            
        if orientation == 'portrait':
            width_view  = height_self / aspect
            height_view = height_self
            if self.width < width_view:
                width_view = self.width
                height_view = self.width * aspect
            pos_x = round((self.width - width_view)/2)
            pos_y = round((self.height - height_view)/2)
            width_view = round(width_view)
            height_view = round(height_view)
        else:
            width_view = width_self
            height_view = width_self / aspect
            if self.height < height_view:
                width_view = self.height * aspect
                height_view = self.height
            pos_x = round((self.width - width_view)/2)
            pos_y = round((self.height - height_view)/2)
            width_view = round(width_view)
            height_view = round(height_view)

        self.view_size = (width_view, height_view)
        self.view_pos  = [self.pos[0] + pos_x, self.pos[1] + pos_y]

    def decode_orientation(self):
        orientation = self.orientation
        if orientation == 'same':
            if Window.width > Window.height:
                orientation = 'landscape'
            else:
                orientation = 'portrait'
        elif orientation == 'opposite':
            if Window.width > Window.height:
                orientation = 'portrait'
            else:
                orientation = 'landscape'
        return orientation

    def screenshot_crop(self):
        pos_x = 0
        pos_y = 0
        if self.view_size[0] == round(self.width) and\
           self.view_size[1] != round(self.height):
            pos_y = (self.height - self.view_size[1])/2
        elif self.view_size[1] == round(self.height) and\
             self.view_size[0] != round(self.width):
            pos_x = (self.width - self.view_size[0])/2
        return (pos_x,pos_y, self.view_size[0],self.view_size[1])

    #############################################
    # File Utilities
    #############################################

    def capture_path(self,location, subdir ,name, ext):
        if platform == 'ios':
            storage = location.lower()
            if storage not in ['private', 'shared']:
                storage = 'shared'
            if storage == 'shared':
                return ''
            location = self._camera.get_app_documents_directory()  
        return join(self._default_subdir(location, subdir),
                    self._default_file_name(name, ext))
    
    def _default_subdir(self, location = '.', subdir=''):
        if not exists(location):
            location = '.'
        if not subdir:
            # Today's date
            subdir = datetime.now().strftime("%Y_%m_%d")
        path = join(location,subdir)
        if not exists(path):
            mkdir(path)
        return path
            
    def _default_file_name(self, name='', ext = '.jpg'):     
        if name:
            name = Path(name).stem
        else:
            name = datetime.now().strftime("%H_%M_%S_%f")[:-4]
        return name + ext            

