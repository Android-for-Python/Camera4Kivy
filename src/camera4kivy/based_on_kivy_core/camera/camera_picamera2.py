'''
PiCamera2 Camera: Implement CameraBase with PiCamera2
'''

__all__ = ('CameraPiCamera2', )

from kivy.logger import Logger
from kivy.clock import Clock, mainthread
from kivy.graphics.texture import Texture
from kivy.graphics import Color, Rectangle, Rotate, Translate, Fbo, BindTexture

from picamera2 import Picamera2
from picamera2.previews import NullPreview
from picamera2.encoders import H264Encoder, Quality 
from picamera2.outputs import Output
from picamera2.request import _MappedBuffer

import numpy as np
from os import environ
from PIL import Image
from . import CameraBase

import signal
import subprocess
import prctl

# Libcamera defaults to INFO, too verbose
environ['LIBCAMERA_LOG_LEVELS'] = 'ERROR'

#################################
# Picamera2 Sensor Interface
#################################

class SensorInterface(NullPreview):

    def __init__(self):
        super().__init__()
        self.mute = False
        self.y = None
        self.u = None
        self.v = None
        self.stream_size = ()

    # Sync event loops
    ###################
    @mainthread
    def sync_yuv(self,y,u,v):
        self.y = y
        self.u = u
        self.v = v
    
    # Request Handlers
    ###################
    def handle_request(self, picam2):
        if self.picam2.display_stream_name:
            camera_config = self.picam2.camera_config
            self.display_stream_name = self.picam2.display_stream_name
            stream_config = camera_config[self.display_stream_name]
            self.stream_fmt = stream_config["format"]
            self.stream_size = stream_config['size']
        picam2.process_requests(self)

    def render_request(self, request):
        try:
            # The added latency due to array manipulation in some of
            # these, occurs in the Picamera2 thread and is much less
            # than sample period of the Kivy thread. Nyquist is happy.
            with _MappedBuffer(request,self.display_stream_name) as mm:
                if self.stream_fmt == 'YUV420':
                    size = len(mm)
                    end_y = size * 2 // 3
                    end_u = end_y + end_y // 4
                    y = bytes(mm[:end_y])
                    u = bytes(mm[end_y:end_u])
                    v = bytes(mm[end_u:])
                    self.sync_yuv(y,u,v)
                                
                elif self.stream_fmt and not self.mute:
                    self.mute = True
                    Logger.error(
                        "Picamera2 SensorInterface unsupported format " +\
                        self.stream_fmt)

        except Exception as e:
            Logger.error("Picamera2 SensorInterface\n" + str(e))


####################################
# FfmpegOutput with rotate metadata
####################################

class FfmpegOutputPlus(Output):

    def __init__(self, output_filename, audio=False, audio_device="default",
                 audio_sync=-0.3, audio_samplerate=48000, audio_codec="aac",
                 audio_bitrate=128000, pts=None, rotate = None):
        super().__init__(pts=pts)
        self.output_filename = output_filename
        self.audio = audio
        self.audio_device = audio_device
        self.audio_sync = audio_sync
        self.audio_samplerate = audio_samplerate
        self.audio_codec = audio_codec
        self.audio_bitrate = audio_bitrate
        self.rotate = rotate

    def start(self):
        general_options = ['-loglevel', 'warning', '-y']  
        video_input = ['-use_wallclock_as_timestamps', '1',
                       '-thread_queue_size', '32',  
                       '-i', '-']
        if self.rotate:  #-map_metadata 0 -metadata:s:v rotate="90"
            video_input = video_input + ['-map_metadata', '0', '-metadata:s:v',
                                         'rotate='+str(self.rotate)]
        video_codec = ['-c:v', 'copy']
        audio_input = []
        audio_codec = []
        if self.audio:
            audio_input = ['-itsoffset', str(self.audio_sync),
                           '-f', 'pulse',
                           '-sample_rate', str(self.audio_bitrate),
                           '-thread_queue_size', '512',  
                           '-i', self.audio_device]
            audio_codec = ['-b:a', str(self.audio_bitrate),
                           '-c:a', self.audio_codec]

        command = ['ffmpeg'] + general_options + audio_input + video_input + \
            audio_codec + video_codec + self.output_filename.split()

        self.ffmpeg = subprocess.Popen(command, stdin=subprocess.PIPE,
                                       preexec_fn=lambda: prctl.set_pdeathsig(signal.SIGKILL))
        super().start()

    def stop(self):
        super().stop()
        if self.ffmpeg is not None:
            self.ffmpeg.stdin.close()  # FFmpeg needs this to shut down tidily
            self.ffmpeg.terminate()
            self.ffmpeg = None

    def outputframe(self, frame, keyframe=True, timestamp=None):
        if self.recording:
            self.ffmpeg.stdin.write(frame)
            self.ffmpeg.stdin.flush()  # forces every frame to get timestamped individually
            self.outputtimestamp(timestamp)

            
            

#################################
# Picamera2 Camera Lifecycle
#################################

class CameraPi2():

    def __init__(self):
        super().__init__()
        self.sensor = None
        self.picam2 = None
        self.base_scaler_crop = None
        self.scaler_crop = None
        self.zoom_level = None
        self._rotate = 0
        self.video_recording = False
        self.audio = False

    # Start
    # Choose sensor, configure pc2
    ###############################

    def start(self, index):
        self.zoom_level = 1
        self.previous_fmt = ''
        self.previous_size = (0,0)
        self.previous_tsize = (0,0)
        self.fbo = None
        
        # Get info about this camera
        num_cameras = len(Picamera2.global_camera_info())
        if num_cameras == 0:
            Logger.error('C4k Picamera2: No camera found.')
            return
        if index <0 or index >= num_cameras:
            Logger.warning('C4k Picamera2: Requested camera '+ str(index) +\
                           ' not found, using ' + str(num_cameras -1) + ' .')
            index = num_cameras -1
        Id = Picamera2.global_camera_info()[index]['Id']
        if 'i2c' not in Id.lower():
            Logger.error('C4k Picamera2: USB cameras not supported.')
            return

        # initialize 
        self.picam2 = Picamera2(index)
        self.configure_sensor(index)
        self.picam2.configure(self.preview_config)
        self.sensor= SensorInterface()
        self.sensor.start(self.picam2)
        self.picam2.attach_preview(self.sensor)
        self.base_scaler_crop = self.crop_limits
        self.scaler_crop = self.crop_limits
        self.picam2.start()

    def configure_sensor(self, index):
        # Sensor configuration
        size_s = (0,0)
        wide = self._context.aspect_ratio == '16:9'
        for m in self.picam2.sensor_modes:
            # Raspberry camera resolution is also field of view.
            # get highest sensor resoluton for this framerate
            # so framerate will set field of view depending on camera
            #
            # Because video players don't support crop metadata well,
            # we can't crop from 4:3 to 16:9
            # So use native 16:9 and shift in fbo
            if 'fps' in m and 'size' in m and 'bit_depth' in m:
                fps = m['fps']
                size = m['size']
                bits = m['bit_depth']
                if fps >= self._framerate and bits == 8:   
                    if not wide and size[0]/size[1] < 1.5:
                        if size[0] > size_s[0]:
                            size_s = size
                            self.crop_limits = m['crop_limits']
                    elif wide and size[0]/size[1] >= 1.5:
                        if size[0] > size_s[0]:
                            size_s = size
                            self.crop_limits = m['crop_limits']

        if not size_s[0]:
            Logger.error('No sensor found in supporting ' +\
                         self.aspect_ratio + ' and ' +\
                         str(self._framerate) + ' fps.')
            return

        # Stream sizes for each configuration
        def align(edge, val):
            return val * round(edge / val)

        dw = align(self._resolution[0] , 64)
        if wide:
            dh = align(self._resolution[0] * 9 / 16, 64)
            vh = 720
        else:
            dh = align(self._resolution[1], 64)
            vh = 960
        main = {"size": (align(size_s[0], 16), align(size_s[1], 16)) }
        preview_lores = {"size": (dw, dh)}
        video_lores = {"size": (1280, vh)}
        
        # Configurations
        self.preview_config = self.picam2.create_preview_configuration(
            main = main,
            lores = preview_lores,
            display = 'lores')
        self.photo_config = self.picam2.create_still_configuration(
            main = main)
        self.video_config = self.picam2.create_video_configuration(
            main = main,
            lores = video_lores,
            encode = 'lores',
            display = 'lores')


    # Stop
    ###############################
    
    def stop(self):
        if self.sensor:
            self.sensor.stop()
        if self.picam2:
            self.picam2.close()
        self.sensor = None
        self.picam2 = None
        self.photo_config = None
        self.video_config = None

    # Display Update
    ###############################

    def update(self):
        ss = self.sensor
        if ss and ss.y:
            return self._yuv_to_rgba('YUV420', ss.y, ss.u, ss.v,
                                     ss.stream_size, self._resolution)
        return None            

    # Zoom and Drag events
    ###############################

    def zoom(self, scale):
        if self.picam2 and self.base_scaler_crop:
            self.zoom_level /= scale   # wheel on pi is backwards
            self.set_zoom()

    def set_zoom(self):
        max_zoom = 7.0
        if self.zoom_level < 1:
            self.zoom_level = 1.0
        if self.zoom_level > max_zoom:
            self.zoom_level = max_zoom
        factor = 1.0 / self.zoom_level
        full_img = self.base_scaler_crop
        center = (self.scaler_crop[0] + self.scaler_crop[2] // 2,
                  self.scaler_crop[1] + self.scaler_crop[3] // 2)
        w = int(factor * full_img[2])
        h = int(factor * full_img[3])
        x = full_img[0] + center[0] - w // 2
        y = full_img[1] + center[1] - h // 2
        self.limit_and_save([x, y, w, h])

    def drag(self, dx, dy):
        if self.picam2 and self.base_scaler_crop:
            full_img = self.base_scaler_crop
            w = self.scaler_crop[2]
            h = self.scaler_crop[3]
            x = self.scaler_crop[0] + int(full_img[2] * dx)
            y = self.scaler_crop[1] + int(full_img[3] * dy)
            self.limit_and_save([x, y, w, h])

    def limit_and_save(self,new_scaler_crop):
        full_img = self.base_scaler_crop
        new_scaler_crop[1] = min(max(new_scaler_crop[1], full_img[1]),
                                 full_img[1] + full_img[3] - new_scaler_crop[3])
        new_scaler_crop[0] = min(max(new_scaler_crop[0], full_img[0]),
                                 full_img[0] + full_img[2] - new_scaler_crop[2])
        self.scaler_crop = tuple(new_scaler_crop)
        self.picam2.controls.ScalerCrop = self.scaler_crop


    # Photo start/stop capture
    ###############################

    def capture_file(self, file_output, callback):
        request = self.picam2.capture_request()
        size = request.config['main']['size']
        with _MappedBuffer(request,'main') as pixels:
            img = Image.frombytes('RGB', size, bytes(pixels))
        request.release()
        if self._rotate in [90,270]:
            size = size[::-1]
        crop = self._context.crop_for_aspect_orientation(size[0],
                                                         size[1])
        if self._rotate in [90,270]:
            t = crop[2]
            crop[2] = crop[3]
            crop[3] = t
        bottom = crop[3] - crop[1]
        right = crop[2] + crop[0]
        img = img.crop((crop[0], crop[1], right, bottom))
        img = img.rotate(self._rotate, expand = True)
        with open(file_output, 'wb') as fp:
            img.save(fp)
        if callback:
            callback(file_output)
            
    # picam2.switch_mode loses ScalarCrop
    def switch_config(self, new_config):
        self.picam2.stop()
        self.picam2.configure(new_config)
        self.picam2.controls.ScalerCrop = self.scaler_crop
        self.picam2.start()
        self.picam2.controls.ScalerCrop = self.scaler_crop  
        
    def photo(self, path, callback):
        if self.picam2 and self.sensor and not self.video_recording:
            self.switch_config(self.photo_config)
            self.capture_file(path, callback)
            self.switch_config(self.preview_config)

    # Video start/stop
    ###############################

    def video_start(self, filepath, callback): 
        self.video_filepath = filepath
        self.video_callback = callback
        if self.picam2 and self.sensor:
            self.video_recording = True
            self.picam2.switch_mode(self.video_config)
            encoder = H264Encoder()
            output = FfmpegOutputPlus(filepath, rotate = self._rotate,
                                      audio= self.audio, audio_sync = 0)
            self.picam2.start_encoder(encoder, output)

    def video_stop(self):
        self.picam2.stop_encoder()
        self.picam2.switch_mode(self.preview_config)
        self.video_recording = False
        if self.video_callback:
            self.video_callback(self.video_filepath)

    # YUV reformatting
    ###############################

    YUV_RGB_FS = '''
    $HEADER$
    uniform sampler2D tex_y;
    uniform sampler2D tex_u;
    uniform sampler2D tex_v;
    mat3 YUV2RGB_JPEG = mat3(1.0,   1.0,   1.0  ,
                             0.0, -0.344, 1.772,
                             1.402, -0.714, 0.0);
    mat3 YUV2RGB_SMPTE170M = mat3(1.164, 1.164, 1.164,
                                  0.0, -0.392, 2.017,
                                  1.596, -0.813, 0.0);
    mat3 YUV2RGB_REC709 = mat3(1.164, 1.164, 1.164,
                               0.0, -0.213, 2.112,
                               1.793, -0.533, 0.0);
    void main(void) {
        vec3 yuv;
        yuv.r = texture2D(tex_y, tex_coord0).r;
        yuv.g = texture2D(tex_u, tex_coord0).r -0.5;
        yuv.b = texture2D(tex_v, tex_coord0).r -0.5;
        gl_FragColor = vec4(YUV2RGB_JPEG * yuv, 1.0);
    }
    '''

    def _yuv_to_rgba(self, fmt, y, u, v, size, tsize):
        if self._context.aspect_ratio == '16:9':
            isize = [tsize[0], round(tsize[0] * 9 / 16)]
            translate = (tsize[1] - isize[1]) // 2
        else:
            isize = tsize
            translate = 0
        origin = (tsize[0]//2, tsize[1]//2)
        if fmt == 'YUV420':
            uv_size = (size[0]//2, size[1]//2 )
        else:
            uv_size = (size[0]//2, size[1]) 
            
        if self.previous_size[0] != size[0] or self.previous_size[1] != size[1]:
            self.tex_y = Texture.create(size= size, colorfmt='luminance')
            self.tex_u = Texture.create(size= uv_size, colorfmt='luminance')
            self.tex_v = Texture.create(size= uv_size, colorfmt='luminance')

        if self.previous_tsize[0] != tsize[0] or\
           self.previous_tsize[1] != tsize[1] or\
               self.fbo == None:
            self.previous_tsize = tsize
            self.fbo = Fbo(size=tsize)   # size for bilt to self._texture
            self.fbo.texture.flip_vertical()
            with self.fbo:
                self.b_u = BindTexture(texture=self.tex_u, index=1)
                self.b_v = BindTexture(texture=self.tex_v, index=2)
                Rotate(origin = origin, angle = 360-self._rotate,
                       axis = (0, 0, 1))
                Translate(0, translate)
                self.r_y = Rectangle(size=isize, texture=self.tex_y)
            self.fbo.shader.fs = self.YUV_RGB_FS
            self.fbo['tex_y'] = 0
            self.fbo['tex_u'] = 1
            self.fbo['tex_v'] = 2
            
        if self.previous_size[0] != size[0] or self.previous_size[1] != size[1]:
            self.previous_size = size
            self.r_y.size = isize
            self.r_y.texture = self.tex_y
            self.b_u.texture = self.tex_u
            self.b_v.texture = self.tex_v
            # Repeat previous pixels to prevent flicker on change
            return bytes(self.fbo.texture.pixels)
        
        self.tex_y.blit_buffer(y, colorfmt='luminance')
        self.tex_u.blit_buffer(u, colorfmt='luminance')
        self.tex_v.blit_buffer(v, colorfmt='luminance')
        self.fbo.ask_update()
        self.fbo.draw()
        return self.fbo.texture.pixels


#################################
# Kivy Camera Provider
#################################

class CameraPiCamera2(CameraBase):
    '''Implementation of CameraBase using PiCamera2  
    '''

    def __init__(self, **kwargs):
        self._update_ev = None
        self._camera = None
        self._framerate = kwargs.get('framerate', 30)
        self.started = False
        self.fbo = None
        self._rotate = kwargs.get('rotation', 0) 
        self.audio = kwargs.get('audio', False) 
        super().__init__(**kwargs)

    # Lifecycle
    ################################

    def init_camera(self):
        self._format = 'rgba'   
        if self._camera is not None:
            self._camera.close()
        self._texture = None
        self.stopped = True
        self.fps = 1. / self._framerate

    def update(self, dt):
        if self.stopped:
            return
        if self._texture is None:
            self._texture = Texture.create(self._resolution)
            self._texture.flip_vertical()
            self._context.on_load()
        try:
            self._buffer = self._camera.update()
            if self._buffer:
                self._copy_to_gpu()
        except Exception as e:
            Logger.error('CameraPiCamera2\n' + str(e))

    def start(self): 
        if not self.started:
            self.started = True
            super().start()
            self._camera = CameraPi2()
            self._camera._resolution = self._resolution
            self._camera._framerate = self._framerate
            self._camera._context = self._context
            self._camera._rotate = self._rotate
            self._camera.audio = self.audio
            self._texture = None
            if self._update_ev is not None:
                self._update_ev.cancel()
            self._camera.start(self._index)
            self._update_ev = Clock.schedule_interval(self.update, self.fps)

    def stop(self):
        super().stop()
        self.started = False
        #self._camera = None

        if self._update_ev is not None:
            self._update_ev.cancel()
            self._update_ev = None
        if self._camera:
            self._camera.stop()
        self._texture = None
        self.fbo = None

    def photo(self,filepath, callback):
        if self._camera:
            self._camera.photo(filepath, callback)

    def video_start(self,filepath, callback):
        if self._camera:
            self._camera.video_start(filepath, callback)

    def video_stop(self):
        if self._camera:
            self._camera.video_stop()

    def zoom(self, scale):
        if self._camera:
            self._camera.zoom(scale)

    def drag(self, dx, dy):
        if self._camera:
            self._camera.drag(dx, dy)

