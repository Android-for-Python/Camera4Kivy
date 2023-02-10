# An implementation of Android CameraX called from a Kivy Preview widget.
#
# About CameraX:
#    https://developer.android.com/training/camerax
# Tested devices:
#    https://developer.android.com/training/camerax/devices
#
# Source
# https://github.com/Android-for-Python/Camera4Kivy/preview_camerax.py
#

from kivy.clock import Clock, mainthread
from kivy.graphics import Fbo, Callback, Rectangle, Rotate, Scale, Translate,\
    Color
from kivy.graphics.texture import Texture
from kivy.logger import Logger

from datetime import datetime
from os.path import exists, join
from os import mkdir, remove
from pathlib import Path
from threading import Thread

from gestures4kivy import CommonGestures
from camera4kivy.preview_common import PreviewCommon

from android.storage import app_storage_path, primary_external_storage_path
from android.runnable import run_on_ui_thread
from android import mActivity, api_version
from jnius import autoclass, PythonJavaClass, java_method

GL_TEXTURE_EXTERNAL_OES = autoclass(
    'android.opengl.GLES11Ext').GL_TEXTURE_EXTERNAL_OES
Environment = autoclass('android.os.Environment')
CameraX = autoclass('org.kivy.camerax.CameraX')
if api_version >= 29:
    ContentValues = autoclass('android.content.ContentValues')
    MediaStoreMediaColumns =\
        autoclass('android.provider.MediaStore$MediaColumns')
    MediaStoreImagesMedia =\
        autoclass('android.provider.MediaStore$Images$Media')
    FileInputStream = autoclass('java.io.FileInputStream')
    FileUtils        = autoclass('android.os.FileUtils')
            
class PreviewCameraX(PreviewCommon, CommonGestures):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._camera = None
        self.enable_zoom_gesture = False
        self.enable_focus_gesture  = False
        self.block_pipeline = True
    
    ##############################
    # Lifecycle events
    ##############################

    def connect_camera(self,
                       enable_photo = True,
                       enable_video = True,
                       enable_analyze_imageproxy  = False,
                       camera_id = 'back',
                       optimize = 'quality',
                       sensor_resolution = None,
                       default_flash = 'off',
                       default_zoom = 0.5,
                       enable_zoom_gesture = True,
                       enable_focus_gesture = True,   
                       data_format = 'yuv420',
                       filepath_callback = None,
                       analyze_proxy_callback = None,
                       analyze_callback = None,
                       canvas_callback = None,
                       **kwargs):

        self._camera = None
        self._update_ev = None
        self._name_pipe = []
        self.texture_size = []
        self.rotation = 0
        self.capture_in_progress = False

        # uniform case
        self.flash_state = default_flash.lower()
        data_format = data_format.lower()
        optimize = optimize.lower()

        self.canvas_callback = canvas_callback
        self.set_filepath_callback(filepath_callback)
        self.set_facing(camera_id)
        self.set_resolution(sensor_resolution)
        self.enable_data = enable_analyze_imageproxy
        
        # flash
        if self.flash_state not in ['on','off','auto']:
            self.flash_state = 'off'

        # optimize
        if optimize not in ['latency','quality']:
            optimize = 'quality'

        # zoom and focus
        default_zoom = min(max(default_zoom,0),1)
        self.enable_zoom_gesture = enable_zoom_gesture
        self.enable_focus_gesture = enable_focus_gesture

        # Analyse Image format
        if data_format not in ['rgba', 'yuv420']:
            data_format = 'yuv420'

        self._analyze_callback = analyze_callback
        self._analyze_proxy_callback = analyze_proxy_callback

        
        # These Java callbacks will execute in Java Main Thread
        self.cb_wrapper = CallbackWrapper(self._filename_callback,
                                          self._analyze_image_proxy,
                                          self._configure_pipeline)

       # Create an Android camera with the required behavior
        self._camera = CameraX(
            enable_photo,
            enable_video,
            self.enable_data,
            self.facing,
            self._sensor_resolution,
            self.aspect_ratio,
            self.cb_wrapper,
            self.flash_state,
            optimize,
            default_zoom,
            data_format)

        # check camerax_provider version
        # Set in org/kivy/camerax/CameraX.java
        latest = '0.0.3'  
        try:
            if self._camera.providerVersion() < latest:
                Logger.warning('Update camerax_provider to the latest version, this is ' + latest)
        except:
            Logger.warning('Update camerax_provider to the latest version, this is ' + latest)

        # Configure the camera for the Kivy view port
        self._configure_camera(True)

    def disconnect_camera(self):
        self.destroy_camera()
        self.block_and_clear_pipeline() 
        
    @run_on_ui_thread
    def destroy_camera(self):
        self.stop_capture_video()
        self._deschedule_pipeline()
        if self._camera:
            self._camera.unbind_camera()
            self._camera = None
                
    # configure camera
    def _configure_camera(self, start):
        self.configure_viewport()
        if self._camera:
            self._camera.setViewPort(self.view_size)
            self._camera.startCamera()
        else:
            self.canvas.clear()
            with self.canvas:
                Color(1,1,1,1)
                Rectangle(size = self.view_size, pos = self.view_pos)

    # Device Rotate
    def on_size(self, instance, size):
        if self._camera:
            self.stop_capture_video()
            self._configure_camera(False)
            
    ##################################
    # Parse options
    ##################################

    def set_facing(self, facing):
        facing = facing.lower()
        if facing == '0':
            facing = 'back'
        elif facing == '1':
            facing = 'front'
        elif facing not in ['back','front']:
            facing = 'back'
        self.facing = facing

    ##############################
    # Preview Widget Touch Events
    ##############################

    # CommonGestures Touch Events
    # tap for focus
    def cgb_primary(self, touch, x, y):
        if self._camera and self.enable_focus_gesture:
            self.focus(x, y)

    # pinch/spread for zoom
    def cgb_zoom(self, touch0, touch1, x, y, scale):
        if self._camera and self.enable_zoom_gesture:
            self.zoom_delta(scale)

    ##############################
    # User events
    ##############################

    def capture_photo(self, location = '',  subdir = '', name = ''):
        if self._camera:
            self.capture_in_progress = True
            self._set_location(location)
            subdir = self._default_subdir_android(subdir)
            name = self._default_file_name(name, '.jpg')
            if self.file_storage:
                self._name_pipe.append(join(subdir, name))
            self._camera.capture_photo(subdir, name, self.file_storage)

    def capture_video(self, location = '', subdir = '', name = ''):
        if self._camera:
            self.capture_in_progress = True
            self._set_location(location)
            subdir = self._default_subdir_android(subdir)
            name = self._default_file_name(name,'.mp4')
            if self.file_storage:
                self._name_pipe.append(join(subdir, name))
            self._camera.capture_video(subdir, name, self.file_storage)

    def stop_capture_video(self):
        if self._camera:
            self._camera.stop_capture_video()

    def capture_screenshot(self, location = '.', subdir = '', name = ''):
        view_crop = self.screenshot_crop()
        self._set_location(location)
        subdir = self._default_subdir_android(subdir)
        name = self._default_file_name(name, '.jpg')
        tex = self.export_as_image().texture.get_region(*view_crop)
        path = join(subdir, name)
        if self.file_storage:
            # local or, shared and api<=29
            tex.save(path, flipped = True)
            if self.callback:
                self.callback(path)
        else:
            # MediaStore
            cache = self.cache_path()
            if cache:
                # write to cache
                cachefile = join(cache, name)
                tex.save(cachefile, flipped = True)
                # create MediaStore entry
                cv = ContentValues()
                cv.put(MediaStoreMediaColumns.DISPLAY_NAME, name)
                cv.put(MediaStoreMediaColumns.MIME_TYPE, 'image/jpeg')  
                cv.put(MediaStoreMediaColumns.RELATIVE_PATH, subdir)
                root_uri = MediaStoreImagesMedia.getContentUri('external')
                context = mActivity.getApplicationContext()    
                uri = context.getContentResolver().insert(root_uri, cv)
                # copy cache file to MediaStore
                rs = FileInputStream(cachefile)
                ws = context.getContentResolver().openOutputStream(uri)
                FileUtils.copy(rs,ws)    
                ws.flush()
                ws.close()
                rs.close()                
                remove(cachefile)
                if self.callback:
                    self.callback(path)
    

    # Select back, front camera
    def select_camera(self, facing):
        if self._camera:
            facing = facing.lower()
            if facing == 'toggle':
                if self.facing == 'back':
                    self.facing = 'front'
                else:
                    self.facing = 'back'
            elif facing == 'front' or facing == '1':
                self.facing = 'front'
            else:
                self.facing = 'back'

            # may have to wait for a capture to complete
            if not self.capture_in_progress:
                self.block_and_clear_pipeline()
                self.do_select_camera()
            else:
                self.stop_capture_video()
                self._facing_ev = Clock.schedule_interval(
                    self.can_select_camera, 1 / 30)
            facing = self.facing
        return facing

    def can_select_camera(self,dt):
        if not self.capture_in_progress:
            self.block_and_clear_pipeline()
            self.do_select_camera()
            Clock.unschedule(self._facing_ev)

    @run_on_ui_thread
    def do_select_camera(self):
        self._camera.select_camera(self.facing)
            
    # Sequence flash : off, on, auto, ...
    def flash(self, state = None):
        # None, auto sequence, 0 ->2 set state
        if self._camera:
            if state == None:
                if self.flash_state == 'off':
                    self.flash_state = 'on'
                elif self.flash_state == 'on':
                    self.flash_state = 'auto'
                else:
                    self.flash_state = 'off'
            elif state in ['off', 'on', 'auto']:
                self.flash_state = state
            self.flash_state = self._camera.flash(self.flash_state)
            return self.flash_state
        return "off"

    def torch(self, state = None):
        if self._camera:
            if state in ['off', 'on']:
                try:
                    return self._camera.torch(state)
                except:
                    Logger.warning('Update camerax_provider to >= 0.0.3')
                    return 'off'
        else:
            return 'off'
                
    # if enable_focus_gesture == True, then this is called by a tap gesture
    def focus(self, x, y):
        if self._camera:
            self._camera.focus(x, y)

    # if enable_zoom_gesture == True, then this called by pinch/spread gesture
    def zoom_delta(self, delta_scale):
        if self._camera:
            self._camera.zoom(delta_scale, False)

    def zoom_abs(self, scale):
        if self._camera:
            self._camera.zoom(scale, True)

    ##############################
    # Create Preview Pipeline
    ##############################
        
    def _create_texture(self, size):
        self._camera_texture = Texture(width = size[0],
                                       height= size[1],
                                       target=GL_TEXTURE_EXTERNAL_OES,
                                       colorfmt='rgba')
        return int(self._camera_texture.id)

    def _create_fbo(self, texture_size, rotation):
        long_edge = max(texture_size)
        short_edge = min(texture_size)
        origin    = (texture_size[0]/2, texture_size[1]/2)
        translate = 0
        scalex = 1
        scaley = 1

        if rotation == 90:
            translate = -(long_edge - short_edge) /2
        elif rotation == 270:
            translate = (long_edge - short_edge) /2

        if texture_size[0] < texture_size[1]:
            translate = -translate
            scalex = -scalex
            scaley = -scaley

        if rotation in [90 , 270]:            
            fbo_size = (texture_size[1],texture_size[0])
        else:
            fbo_size = texture_size

        self._fbo = Fbo(size=fbo_size)
        self._fbo.shader.fs = '''
            #extension GL_OES_EGL_image_external : require
            $HEADER$
            uniform samplerExternalOES texture1;
            void main()
            {
                gl_FragColor = texture2D(texture1, tex_coord0);
            }
        '''
        
        with self._fbo.before:
            Rotate(origin = origin, angle = 360 - rotation, axis = (0, 0, 1))
            Translate(translate, translate)
            Scale(scalex, scaley, 1, origin = origin )
            Rectangle(size = texture_size)

        with self._fbo:
            self._camera_texture_cb = Callback(lambda instr:
                                               self._camera_texture.bind)

    # Run on Kivy main thread because required by FBO.
    @mainthread
    def _create_pipeline(self, texture_size, rotation):
        id = self._create_texture(texture_size)
        self._create_fbo(texture_size, rotation)
        self._camera.setTexture(id,texture_size)
        self._schedule_pipeline()

    ##############################
    # Fill Preview Pipeline
    ##############################
            
    def block_and_clear_pipeline(self):
        self.block_pipeline = True
        if self._camera and self._fbo.texture:
            tex_size = self._fbo.texture.size
            buf = bytes([255] * tex_size[0] * tex_size[1] * 4)
            self._fbo.texture.blit_buffer(buf, colorfmt='rgba',
                                          bufferfmt='ubyte')
            self._analyze_texture()
            self._update_canvas() 

    def _schedule_pipeline(self):
        self._deschedule_pipeline()
        if self._camera and self._camera_texture and self._fbo.texture:
            self._set_surface_provider(True)
            self.block_pipeline = False
            self._update_ev = Clock.schedule_interval(self._update_pipeline,
                                                      1 / 30)

    def _deschedule_pipeline(self):
        if self._update_ev is not None:
            self._set_surface_provider(False)
            self._update_ev.cancel()
            self._update_ev = None

    def _update_pipeline(self, dt):
        if self._camera.imageReady() and not self.block_pipeline:
            self._camera_texture_cb.ask_update() 
            self._fbo.draw()  
            self._analyze_texture()
            self._update_canvas() 

    # Run on UI thread because required by CameraX
    @run_on_ui_thread
    def _set_surface_provider(self, enable):
        self._camera.setSurfaceProvider(enable)

    # Run on mainthread because required by Kivy canvas
    @mainthread
    def _update_canvas(self):
        tex = self._fbo.texture.get_region(*self.crop)

        # moved from create_fbo
        if self.facing == 'front':
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

    #######################################
    # Storage Location
    #######################################

    def _set_location(self, location):
        storage = location.lower()
        if storage not in ['private', 'shared']:
            storage = 'shared'
        self.private_storage = storage == 'private'
        self.file_storage = self.private_storage or api_version < 29

    def _default_location(self):
        if self.private_storage:
            root = join(app_storage_path(),Environment.DIRECTORY_DCIM)
            if not exists(root):
                mkdir(root)
        else:
            if api_version < 29:
                root = join(primary_external_storage_path(),
                            Environment.DIRECTORY_DCIM,
                            self._app_name())
                if not exists(root):
                    mkdir(root)
            else:
                root = join(Environment.DIRECTORY_DCIM, self._app_name())
        return root
                
    def _default_subdir_android(self, subdir=''):
        root = self._default_location()
        if not subdir:
            # Today's date
            subdir = datetime.now().strftime("%Y_%m_%d")
        path = join(root,subdir)
        if self.private_storage or api_version < 29:
            if not exists(path):
                mkdir(path)
        return path

    def _app_name(self):
        context = mActivity.getApplicationContext()
        appinfo = context.getApplicationInfo()
        if appinfo.labelRes:
            name = context.getString(appinfo.labelRes)
        else:
            name = appinfo.nonLocalizedLabel.toString()
        return name

    def cache_path(self):
        context = mActivity.getApplicationContext()
        cache =  context.getExternalCacheDir()
        return str(cache.toString())

    #######################################
    # Callbacks
    #######################################

    # Runs in Java Main Thread
    def _configure_pipeline(self, croprect, resolution, rotation):
        if rotation in [ 90, 270]:  
            self.crop = [croprect.top,   croprect.left,
                         croprect.bottom - croprect.top,
                         croprect.right - croprect.left]
        else:  
            self.crop = [croprect.left,   croprect.top,
                         croprect.right - croprect.left,
                         croprect.bottom - croprect.top]
        texture_size = [resolution.getWidth(), resolution.getHeight()]
        self.texture_size = texture_size
        self.tscale = self.view_size[1] / self.crop[3]
        self.rotation = rotation
        self._create_pipeline(texture_size, rotation)

    # Runs in some Java thread
    def _filename_callback(self, file_id):
        if not file_id:
            # The callback returns "" for non-MediaStore saves
            if self._name_pipe:
                file_id = self._name_pipe[0]
                self._name_pipe = self._name_pipe[1:]
        self.capture_in_progress = False
        if self.callback:
            self.callback(str(file_id))

    def _analyze_texture(self):
        if not self.enable_data and self._analyze_callback:
            tex = self._fbo.texture.get_region(*self.crop)
            self._analyze_callback(tex, self.view_pos,
                                   self.tscale, self.facing=='front')

    def _analyze_image_proxy(self, image_proxy):
        if self.enable_data and self._analyze_proxy_callback:
            if self.rotation in [0, 180]:
                tscale = self.view_size[1] / image_proxy.getHeight()
            else:
                tscale = self.view_size[1] / image_proxy.getWidth()
            self._analyze_proxy_callback(image_proxy, self.view_pos,
                                         tscale, self.facing == 'front',
                                         self.rotation)

       
class CallbackWrapper(PythonJavaClass):
    __javacontext__ = 'app'
    __javainterfaces__ = ['org/kivy/camerax/CallbackWrapper']

    def __init__(self, callback0, callback1, callback2):
        super().__init__()
        self.callback0 = callback0
        self.callback1 = callback1
        self.callback2 = callback2

    @java_method('(Ljava/lang/String;)V')        
    def callback_string(self, filepath):
        if self.callback0:
            self.callback0(filepath)

    @java_method('(Landroidx/camera/core/ImageProxy;)V')        
    def callback_image(self, image):
        if self.callback1:
            self.callback1(image)

    @java_method('(Landroid/graphics/Rect;Landroid/util/Size;I)V')  
    def callback_config(self, croprect, resolution, rotation):
        if self.callback2:
            self.callback2(croprect, resolution, rotation)
            
