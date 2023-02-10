Camera4Kivy
===========

*Yet Another Camera for Kivy*

2023/02/09 : Android users: camerax_provider has been updated to version 0.0.3 

- [Overview](#overview)
- [Install](#install)
  * [Install Camera4Kivy on Desktop](#install-camera4kivy-on-desktop)
  * [Install Camera4Kivy on Android](#install-camera4kivy-on-android)
    + [buildozer.spec:](#buildozerspec-)
    + [Run Time Permissions](#run-time-permissions)
  * [Install Camera4Kivy on iOS](#install-camera4kivy-on-ios)
    + [Run Time Permissions](#run-time-permissions-1)
- [Examples](#examples)
  * [Tested Examples](#tested-examples)
    + [C4K Photo Example](#c4k-photo-example)
    + [C4K QR Example](#c4k-qr-example)
    + [C4K OpenCV Example](#c4k-opencv-example)
    + [C4K MLKit Example](#c4k-mlkit-example)
    + [C4K TFLite Example](#c4k-tflite-example)
  * [Tested Platforms](#tested-platforms)
- [Preview Widget](#preview-widget)
  * [Preview Widget Properties](#preview-widget-properties)
    + [aspect_ratio](#aspect-ratio)
    + [letterbox_color](#letterbox-color)
    + [orientation](#orientation)
  * [Preview Widget API](#preview-widget-api)
    + [Connect Camera](#connect-camera)
      - [camera_id](#camera-id)
      - [mirrored](#mirrored)
      - [filepath_callback](#filepath-callback)
      - [sensor_resolution](#sensor-resolution)
      - [analyze_pixels_resolution](#analyze-pixels-resolution)
      - [enable_analyze_pixels](#enable-analyze-pixels)
      - [enable_analyze_imageproxy](#enable-analyze-imageproxy)
      - [enable_zoom_gesture](#enable-zoom-gesture)
      - [enable_focus_gesture](#enable-focus-gesture)
      - [imageproxy_data_format:](#imageproxy-data-format-)
    + [Disconnect Camera](#disconnect-camera)
    + [Capture](#capture)
      - [location](#location)
      - [subdir](#subdir)
      - [name](#name)
    + [Select Camera](#select-camera)
    + [Zoom](#zoom)
    + [Flash](#flash)
    + [Torch](#torch)
    + [Focus](#focus)
    + [camera_connected](#camera-connected)
- [Image analysis](#image-analysis)
  * [Overview and Examples](#overview-and-examples)
  * [User Interaction](#user-interaction)
  * [Coordinates and image encoding](#coordinates-and-image-encoding)
  * [Analysis Configuration](#analysis-configuration)
  * [Debugging](#debugging)
  * [Performance](#performance)
- [Camera Behavior](#camera-behavior)
  * [A Physical Camera](#a-physical-camera)
  * [Resolution](#resolution)
    + [Sensor Resolution](#sensor-resolution)
    + [Cropped Sensor Resolution](#cropped-sensor-resolution)
    + [Preview Resolution](#preview-resolution)
    + [Capture Resolution](#capture-resolution)
    + [Analysis Resolution](#analysis-resolution)
    + [Display Resolution.](#display-resolution)
- [Camera Provider](#camera-provider)
  * [Android Camera Provider](#android-camera-provider)
  * [OpenCV](#opencv)
  * [GStreamer](#gstreamer)
  * [Picamera](#picamera)
  * [Picamera2](#picamera2)
  * [AVFoundation](#avfoundation)
- [Known Behavior](#known-behavior)
  * [Behavior: Android .mp4 Orientation](#behavior--android-mp4-orientation)
  * [Behavior: Android .jpg Orientation.](#behavior--android-jpg-orientation)
  * [Behavior: Android armeabi-v7a build installed on an arm64-v8a device](#behavior--android-armeabi-v7a-build-installed-on-an-arm64-v8a-device)
  * [Behavior: Android "No supported surface combination"](#behavior--android--no-supported-surface-combination-)

## Overview

Available on all the usual platforms.

```python
from camera4kivy import Preview
```

Camera4Kivy consists of a `Preview` widget with an api to connect to the physical camera unit. The Preview widget layout is [configured with Kivy properties](https://github.com/Android-for-Python/Camera4Kivy#preview-widget-properties) , the camera unit and image analysis behavior are [configured with an api](https://github.com/Android-for-Python/Camera4Kivy#preview-widget-api). For example:

In .kv
```
    Preview:
        id: preview
	aspect_ratio: '16:9'
```

In Python
```python
    self.preview = Preview(aspect_ratio = '16:9')
```

To connect the camera unit to the Preview call the preview's `connect_camera()` method, **after on_start()**. For example to connect the camera with the image analysis api enabled :

```python
    self.preview.connect_camera(enable_analyze_pixels = True)
```

Well behaved apps disconnect the camera when it is no longer in use. It is important to be well behaved.

```python
    self.preview.disconnect_camera()
```

To take a photo:

```python
    self.preview.capture_photo()
```

The captured file location may be specified and is also reported in a callback. A data analysis api allows per frame analysis and preview annotation or preview image replacement.

On Android a pinch/spread gesture controls zoom, and a tap overrides any automatic focus and metering (if available). Some `connect_camera()` options are platform specific.

Be aware Preview operation depends on the performance of the graphics hardware. In general Preview uses the highest available resolution for 30fps performance. On devices with low performance graphics hardware sush as low end laptops or Raspberry, you will probably have to explicitly set a lower image resolution inorder to increase the frame rate.

## Install

A [camera provider](https://github.com/Android-for-Python/camera4kivy#camera-provider) may be required. On a destop the camera provider is installed once. On Android the camera provider is [added to each project](https://github.com/Android-for-Python/camera4kivy#android-camera-provider).

### Install Camera4Kivy on Desktop

`pip3 install camera4kivy`

### Install Camera4Kivy on Android

Camera4Kivy depends on Buildozer 1.3.0 or later

#### buildozer.spec:

`android.api = 33` (Constrained by Android packages imported by camerax_provider)

`requirements = python3, kivy, camera4kivy, gestures4kivy`

Set `p4a.hook` to enable the app's use of the [camera provider](https://github.com/Android-for-Python/camera4kivy#android-camera-provider). This sets the required p4a options.

`p4a.hook = camerax_provider/gradle_options.py`

The implementation of the camerax gradle dependencies is architecture specific, an app built for armeabi-v7a will crash on an arm64-v8a device.

#### Run Time Permissions

The following run time permissions must be in be requested in the app. As usual request these in build() or after on_start(). See the examples.

Always required: `CAMERA`

Required to record video with audio: `RECORD_AUDIO`

Required when capturing photo, screenshot, or video and saving to shared storage, and only on devices running api_version < 29: `WRITE_EXTERNAL_STORAGE`

### Install Camera4Kivy on iOS

Install the 'master' (2022/04/22 or later) version of kivy-ios.
```
pip3 install git+https://kivy/kivy-ios.git
toolchain build python3 kivy
```

`toolchain pip3 install camera4kivy`

#### Run Time Permissions

Permission to use the camera and save images is **required** by iOS. To enable permissions edit `<project>-ios/<project-Info.plist`. Add some or all of these:

To enable use of the Camera add:
```
        <key>NSCameraUsageDescription</key>
	<string> </string>
```
To enable saving image captures to the Photos App (the default behavior) add:
```
	<key>NSPhotoLibraryAddUsageDescription</key>
	<string> </string>
```
To enable viewing images saved to app local storage with the File Manager:
```
        <key>UIFileSharingEnabled</key>
	<true/>
        <key>LSSupportsOpeningDocumentsInPlace</key>
	<true/>
```


## Examples

A prerequisite is that a working camera is installed. Test this with the platform's camera app before proceeding. All examples use the platform specific camera provider, and assume the typical default camera_id of '0'. If you find the example does not connect to a camera review the available camera ids and your camera provider choice.

### Tested Examples

The Photo example illustrates basic camera usage, try this first. The remaining examples illustrate image analysis using various packages. 

On Android and iOS the app can rotate when the device rotates, on the desktop you can change the window size to simulate orientation, and thus rotating a mobile device. 

#### C4K Photo Example 
[C4K-Photo-Example](https://github.com/Android-for-Python/c4k_photo_example). Illustrates basic layout using screens. Basic camera functionality including photo capture, screenshot capture, and on Android capture of video with audio.
On Raspberry PI a mouse must be used, a touch pad does not work correctly.

#### C4K QR Example
[C4K-QR-Example](https://github.com/Android-for-Python/c4k_qr_example). Everything you need to read a restaurant menu. Long press or double click on a highlighted QR code to open a web browser. Illustrates basic analysis, screen annotation, and user interaction. 

#### C4K OpenCV Example
[C4K OpenCV Example](https://github.com/Android-for-Python/c4k_opencv_example)
Edge detect the video stream. Illustrates using OpenCV analysis and replacing the original preview with the transformed image.

#### C4K MLKit Example
[C4K MLKit Example](https://github.com/Android-for-Python/c4k_mlkit_example)
Face detect, MLKit is Android only. Illustrates using the ImageProxy api.

#### C4K TFLite Example
[C4K TFLite Example](https://github.com/Android-for-Python/c4k_tflite_example)
Object classification. Illustrates using a large Tensorflow Lite model, and writing text to the Preview image.

### Tested Platforms 

| Example | Windows | Macos | Linux | Android | iOS | Coral |
|---------|---------|-------|-------|---------|-----|-------|
| Photo   | :heavy_check_mark: | :heavy_check_mark: | :heavy_check_mark: | :heavy_check_mark: | :heavy_check_mark: | |
| QR   | :heavy_check_mark: | :heavy_check_mark: | :heavy_check_mark: | :heavy_check_mark: | | |
| OpenCV | :heavy_check_mark: | :heavy_check_mark: | :heavy_check_mark: | :heavy_check_mark: | | |
| MLKit | | | | :heavy_check_mark: | | |
| TFLite   | :heavy_check_mark: | :heavy_check_mark: | :heavy_check_mark: | :heavy_check_mark: | | :heavy_check_mark: |

- Windows : Windows 11, i7-10 @ 1.1GHz, Python 3.8.2  Kivy==2.1.0.dev0
- Windows : Windows 10, i3-7 @ 2.4GHz, Python 3.9.7 Kivy==2.0.0
- Macos   : Big Sur,  i5-10 @ @ 1.1GHz, Python 3.9.9 Kivy==2.0.0
- Linux   : Raspberry Buster, Cortex-A72 @ 1.5GHz Python3.7.3 Kivy==2.0.0
- Android : build : arm64-v8a  device: Android 12, Pixel 5
- Android : build : armeabi-v7a device: Android 6, Nexus 5  Start is somewhat slow.
- iOS     : iPhone SE (second generation)
- Coral   : [Accelerator](https://coral.ai/products/accelerator) tested with Windows 11 , gave very approximately an order of magnitude speed up.

## Preview Widget

An app can have multiple `Preview` widgets, but only one can be connected to the physical camera unit at a time. A natural way to implement this is to add a preview widget to a screen's contents, then connect to the camera unit `on_enter` and disconnect `on_pre_leave`. Or if using a ModalView, Popup, or MDDialog use `on_open` and `on_pre_dismiss`. The C4K-Photo-Example illustrates this, the other examples simply connect the camera after `on_start()` and disconnect `on_stop()`.

### Preview Widget Properties

The widget has these Kivy properties that configure its layout:

#### aspect_ratio
A string property. Either '4:3' (default) or '16:9'. 

#### letterbox_color
A color property. Geometry tells us that layout of a fixed aspect ratio widget almost always results in letterboxing. Art tells us we can hide letterboxes by filling them with a color that matches the surrounding widgets. 

#### orientation
A string property. One of 'portrait' , 'landscape', 'same', 'opposite'.  The default is the 'same' as the device or window. This choice modifies effective resolution, [see](https://github.com/Android-for-Python/camera4kivy#cropped-sensor-resolution). The best resolution is always obtained with 'same'.

### Preview Widget API

The widget has these methods:

#### Connect Camera 

This may only be called after `on_start()`.

```python
    def connect_camera(self,kwargs):
```

Optional arguments:
    
##### camera_id
Specify which camera to connect to. For example `camera_id = 'front'`. A string containing an integer (default '0'), or on Android or iOS 'back' (default), or 'front'.

##### mirrored
Mirrors the Preview image, default is `True`. This option is ignored on Android and iOS where by convention 'front' is always mirrored and 'back' is never mirrored. This option should usually be `True` for any camera facing the user, and `False` for any camera not facing the user. 

Captures are never mirrored, except a screenshot capture if the Preview is mirrored.

The pixels argument to `image_analysis_callback()` is never mirrored, if a Preview is mirrored a `texture` result of any image analysis will be automatically mirrored in the `canvas_instructions_callback()` by the tex_size and tex_pos arguments. If image analysis genetates image annotation locations, these locations must be adjusted by the app for a mirrored preview. See the [Image Analysis Section](https://github.com/Android-for-Python/camera4kivy#image-analysis) for code fragments and links to examples.  

##### filepath_callback
On a capture of a photo, video, or screenshot, this argument specifies a method to receive the path and name of the saved file. For example `filepath_callback = my_method`, where `def my_method(self, path):` is an app supplied method with a string argument.

Photo and Video captures may be implemented in a different thread. The only way to know that a capture is complete is a filepath_callback. There may be [latency](https://github.com/Android-for-Python/Camera4Kivy#latency) concequences of disconnecting the camera after initiating a capture and before a filepath_callback.

The filepath_callback can also be used to reset any 'video recording' indicator in the UI. While video recording is normally terminated by the user, it can also be terminated by app pause, device rotation, or camera selection. In these last cases the any recording indicator can be reset by the callback, which occurs on any capture termination regardless of cause. 

##### sensor_resolution
Overrides the default sensor resolution, which is the highest resolution available, except Raspberry Pi where it is (1024, 768). Tuple of two integers, for example `sensor_resolution = (640, 480)`. The resulting capture resolution obtained depends on the behavior of the camera provider (for example it is ignored by GStreamer). The capture resolution also depends on the relative orientation and aspect ratio of the Preview. Treat the value specified as a request that may not be exactly honored.

##### analyze_pixels_resolution
Sets the pixels resolution passed by `analyze_pixels_callback()`. A scalar, representing the number of pixels on the long edge, the short edge is determined using the aspect ratio. For example `analyze_pixels_resolution = 720`. The default is the minimum of cropped sensor resolution and 1024.

As an alternative, sometimes the analysis package will need to set the resolution. This is done with `self.auto_analyze_resolution` as described in [Analyze Configuration](https://github.com/Android-for-Python/camera4kivy#analyze-configuration). 

##### enable_analyze_pixels
Use `enable_analyze_pixels = True` to enable the `analyze_pixels_callback()`

##### enable_analyze_imageproxy
Use `enable_analyze_imageproxy = True` to enable the `analyze_imageproxy_callback()`
Android only.

##### enable_zoom_gesture
Default True.  Android and iOS only.

##### enable_focus_gesture
Default True. Android only.
       
##### imageproxy_data_format:
Applies only to the Android ImageProxy api. 'yuv420' (default) or 'rgba'.


#### Disconnect Camera

Always do this, it is important to disconnect the camera when not in use.

```python
    def disconnect_camera(self):
```

A disconnect while a capture is in progress generally results in termination of the capture and saving the result as usual.

However on Android a disconnect immediately after a capture has be initiated may prevent the start of the file save and nothing is saved. A warning message is reported by filepath_callback, this may be filtered as shown in [this example](https://github.com/Android-for-Python/c4k_photo_example/blob/main/applayout/toast.py#L15)

#### Capture
```python
    def capture_photo(self, kwargs):
    def capture_screenshot(self, kwargs):
    def capture_video(self, kwargs):      # Android only
    def stop_capture_video(self):         # Android only
```

Video capture is only available on Android or with the OpenCV camera provider. Capturing audio with video is only available on Android.

Captures are never mirrored, except a screenshot capture if the Preview is mirrored. Capture resolution is discussed [here](https://github.com/Android-for-Python/Camera4Kivy#capture-resolution).

Captures are saved to `<location>/<subdir>/<name>.jpg` or `.mp4`. 

The default values are as follows. On a desktop `<location>` is the current directory `.`, on Android `<location>` is `DCIM/<appname>`, and on iOS <location> is the Photos App. The value of `<subdir>` is the current date, the format is 'YYYY_MM_DD'. The value of `<name>` is the current time, the format is 'hh_mm_ss_xx' (xx is 1/100 sec).

The [filepath_callback](https://github.com/Android-for-Python/Camera4Kivy#filepath_callback) occurs on capture completion, with an argument that is the actual path for a particular capture. 

Be aware that on Android >= 10 shared storage files are saved in a database, called MediaStore, and not in a file system. The architecture of Android storage is outside the scope of this document. 

The values of `<location>`, `<subdir>`, and `<name>` can be modified with optional keyword arguments to the three `capture_` methods:

##### location

The value replaces the default value of `<location>`.

On a desktop the value is a directory that must exist. 

On Android and iOS the value can only be `'shared'` or `'private'`, other values default to `'shared'`.

On Android the value `'shared'` specifies Android shared storage `DCIM/<appname>`. The value `'private'` specifies [app local storage](https://github.com/kivy/python-for-android/blob/develop/doc/source/apis.rst#storage-paths) `app_storage_path()/DCIM`. If you want a different location use `'private'` and move the resulting file based on the path provided by filepath_callback.

On iOS the value `'shared'` specifies the iOS Photos App. The value `'private'` specifies app local storage. For `'shared'` the filepath_callback returns an empty string, for `'private'` it returns the paths to the file in app local storage.


##### subdir

The value replaces the default value of `<subdir>`. The subdirectory will be created or added to the Android MediaStore path. For iOS when `location='shared'` this is ignored.

##### name

The value replaces the default value of `<name>`, the `.jpg` or `.mp4` extensions will be added automatically.

Note that it is a characteristic of Android MediaStore that a second capture with the same subdir and name values as the first will not overwrite the first. It will create a second file named `<subdir>/<name> (1).jpg`, this name is created by Android MediaStore. The MediaStore may crash if it creates too many (31 ?) such names.

For iOS when `location='shared'` this is ignored.

#### Select Camera

Change the currently connected camera, camera_id must specify a physically connected camera.

```python
    def select_camera(self, camera_id):
```

#### Zoom
On Android only, zoom_delta() is called by pinch/spread gesture unless disabled.
On iOS only, zoom_abs() is called by pinch/spread gesture unless disabled.
```python 
    def zoom_delta(self, delta_scale):  
    def zoom_abs(self, scale):  
```

#### Flash
Android only, and for capture photo only, the value is ignored for video and data. The `state` argument must be in `['on', 'auto', 'off']`, alternatively if `state=None` sequential calls sequence through that list. Note that 'on' always turns on the flash around the time a photo is captured, 'auto' only does this if the light level is low enough.

```python 
    def flash(self, state = None)
```

#### Torch
Android only, immediately turns the flash on in any use case. The `state` argument must be in `['on', 'off']`

```python 
    def flash(self, state)
```

#### Focus
Android only, if available on device. Called by a tap gesture unless disabled
```python
    def focus(x, y): 
```

#### camera_connected

This is a boolean variable describing the camera state. It is `True` immediatedal *after* the camera is connected, and `False` immediately *before* the camera is disconnected.

## Image analysis

### Overview and Examples

The programming pattern for video data analysis is to create a subclass of `Preview` and implement two predefined methods. One to analyze the frame, the second to modify the Preview image with the analysis result. In general like this:

```python
class CustomAnalyzer(Preview):
      def analyze_pixels_callback(self, pixels, size, image_pos,
                                  image_scale, mirror):
	### Add your pixels analysis code here
	### Add your coordinate transforms here
				
      def canvas_instructions_callback(self, texture, tex_size, tex_pos):
	### Add your Preview annotation or image replacement code here
```

The `analyze_pixels_callback()` is called each time new pixels are available, and the `canvas_instructions_callback()` is called on each iteration of the Kivy event loop. The availability of new pixels depends on the camera data rate, and the latency of any analysis code included with the previous call of `analyze_pixels_callback()`. Thus `analyze_pixels_callback()` is typically called at a rate less than `canvas_instructions_callback()`, so the annotation update rate is typically less than the image frame rate.

On Android this is an alternative to analyze_pixels_callback(), it is used for Android only analysis packages.
```python
      def analyze_imageproxy_callback(self, image_proxy, image_pos,
                                      image_scale, mirror, degrees):
	### Add your imageproxy specific analysis code here
```

Keep to this pattern. Perform analysis and coordinate transforms in the 'analyze_pixel_callback' (or imageproxy) method. And in 'canvas_instructions_callback' only display the results of previous calculations. Data passed from the analysis method to the display method must be passed in a thread safe way.

The `analyze_pixels_callback` method is used to analyze its RGBA `pixels` and `size` arguments. The `pos`, `scale`, and `mirror` arguments enable mapping the analyzed pixels coordinates to Preview coordinates. The `mirror` parameter is required because `pixels` image is never mirrored, but the Preview may be. An example:

```python
   def analyze_pixels_callback(self, pixels, image_size, image_pos,
                               scale, mirror):
	# Convert the image encoding		       
        pil_image = Image.frombytes(mode='RGBA', size=image_size,
	                            data= pixels)
        # Analyze the image				    
        barcodes = pyzbar.decode(pil_image, symbols=[ZBarSymbol.QRCODE])
	# Collect the results and transform the coordinates
        found = []
        for barcode in barcodes:
            text = barcode.data.decode('utf-8')
            if 'https://' in text or 'http://' in text:
                x, y, w, h = barcode.rect
                # Map Zbar coordinates to Kivy coordinates
                y = image_size[1] -y -h
                # Map Analysis coordinates to Preview coordinates
                if mirror:
                    x = image_size[0] -x -w
                x = round(x * scale + image_pos[0])
                y = round(y * scale + image_pos[1])
                w = round(w * scale)
                h = round(h * scale)
                found.append({'x':x, 'y':y, 'w':w, 'h':h, 't':text})
	# Save the results in a thread safe way
        self.make_thread_safe(list(found)) ## A COPY of the list
```

Analysis and canvas annotation callbacks occur on different threads. The result of the analysis must be saved in a thread safe way, so that it is available for the canvas callback. We pass a **copy** of the result to:

```python
    @mainthread
    def make_thread_safe(self, found):
        if self.camera_connected:
            self.annotations = found
        else:
            self.annotations = []
```
Note that we null the application state when the camera is not connected. This prevents saved annotations from being shown when a camera is re-connected, due to the multi-threaded implementation. 

Then add the thread safe annotations to the canvas. 

```python
    def canvas_instructions_callback(self, texture, tex_size, tex_pos):
        # Add the annotations determinined during analyze callback.
        Color(1,0,0,1)
        for r in self.annotations:
            Line(rectangle=(r['x'], r['y'], r['w'], r['h']), width = dp(2))	
```
We can also replace the existing Preview image with some other texture, positioned with the 'tex_size' and 'tex_pos' arguments. Use a thread safe texture created as a result of some image analysis like this:

```python
    def canvas_instructions_callback(self, texture, tex_size, tex_pos):
        # Add a different preview image, which is a transformed camera image
	# this image has 'analyze_pixels_resolution'
        if self.analyzed_texture:
	    # 'self.analyzed_texture' contents created
	    # by analyze_pixels_callback()
            Color(1,1,1,1)
            Rectangle(texture= self.analyzed_texture,
	              size = tex_size, pos = tex_pos)
```	   
The new texture will be automatically mirrored by 'text_size' and 'tex_pos' if required. These 'text_size' and 'tex_pos' arguments are for adding a texture, and not valid for coordinate calculations as they are potentially mirrored.

See the OpenCV example for details on creating a thread safe texture. 

The above code fragments are fully implemented in two examples: [QR Reader](https://github.com/Android-for-Python/c4k_qr_example/blob/main/qrreader.py), and [OpenCV](https://github.com/Android-for-Python/c4k_opencv_example/blob/main/edgedetect.py). Similar examples exhibiting this pattern are [tflite](https://github.com/Android-for-Python/c4k_tflite_example/blob/main/classifyobject.py) and [mlkit](https://github.com/Android-for-Python/c4k_mlkit_example/blob/main/facedetect.py).

### User Interaction

But wait, there is more, a user can interact with the analysis results in the Preview. The Preview subclass may have multiple inheritance, for example to allow the user to interact with annotations on the screen. The QR Reader example illustrates this, by inheriting from a gestures package:

```python
    class QRReader(Preview, CommonGestures):
```

That package's gesture callbacks, and an annotation location test are used to initiate some action. In this case open a web browser based on a URL in a QR code, and a long press or mouse double click inside the box drawn around the QR code.

```python
    def cg_long_press(self, touch, x, y):
        self.open_browser(x, y)

    def cg_double_tap(self, touch, x, y):
        self.open_browser(x, y)

    def open_browser(self, x, y):
        for r in self.annotations:
            if x >= r['x'] and x <= r['x'] + r['w'] and\
               y >= r['y'] and y <= r['y'] + r['h']:
                webbrowser.open_new_tab(r['t'])
```

### Coordinates and image encoding

**Important**, be aware of different coordinate systems and image encoding. A test with a print statement of third party analysis code coordinates can be valuable. 

- Kivy image coordinates have their origin at the bottom left. Most other systems use top left (with positive y increaing downwards) as their origin.

- Kivy image properties are a (width, height) tuple. Some packages, notably numpy images, reverse the order to (height, width).

- Kivy pixels are encoded RGBA. Third party analysis code may expect some other encoding, both Pillow and OpenCV provide encoding converions. Some image recodings are computationally expensive.

- The 'canvas_instructions_callback()' arguments 'tex_size' and 'tex_pos' are potentially mirrored and their values are not valid for coordinate mapping. Perform mapping in 'analyze_pixels_callback()' using the 'image_size' and 'image_pos' arguments.


### Analysis Configuration

Image analysis is enabled with a parameter to `connect_camera()`:

`connect_camera(enable_analyze_pixels = True)`

To change the default analysis resolution specify the number of pixels in the long edge (the default is the smaller of 1024 or the cropped resolution):

`connect_camera(enable_analyze_pixels = True, analyze_pixels_resolution = 720)`

The `analyze_pixels_resolution` option provides analysis images with the same orientation and aspect ratio as the Preview. 

As an alternative the analysis software may set `self.auto_analyze_resolution` a two element list of [width, height]. In this case the aspect ratio is not necessarily maintained for analysis, the `analyze_pixels_callback()` `image_scale` parameter is a two element list [width, height] allowing scaling of any results. As used in [c4k_tflite_example classifyobject.py](https://github.com/Android-for-Python/c4k_tflite_example/blob/main/classifyobject.py).

On Android only, the imageproxy api is an alternative to the pixels api. 

`connect_camera(enable_analyze_imageproxy = True)`

The imageproxy api provides images in landscape, regardless of the preview orientation. A degrees parameter enables adjusting the analysis accordingly. Android implements automatic changes to frame rate and resolution in the case of slow analysis.

### Debugging

Check that the app analysis code is doing what you expect. If the result of this is coordinates (most cases) then check these with a print statement. Move whatever you expect to be detected to the four corners of the camera view. Look the printed values, do they reflect the analysed image pixels size and orientation? Repeat for the coordinates after they are mapped to a Kivy widget.

Measure the time the analysis algorithm takes to execute on one frame. Do this in the cases of detection and nothing to detect. This along with some overhead will define the maximum analysis frame rate. The [tflite example](https://github.com/Android-for-Python/c4k_tflite_example/blob/main/classifyobject.py) monitors analysis frame rate as part of its normal operation.

### Performance

The camera provides a stream of images for analysis via `analyze_pixels_callback()`. Images arrive at typically 30 fps, so given some overhead the app has probably less than 30mS to do the analysis.

The api has a builtin mechanism so that images are analyzed only when the previous analysis is complete. This mechanism does not alter the canvas instructions frame rate. If the analysis results are 'jerky' it is because the analysis algorithm is slow for the hardware.

Conversely, you can explicitly decrease the analysis frame rate without changing anything else using a flag set using Kivy Clock. Clock rates close to the actual analyze rate will exhibit jitter. For example for a one second analyze interval:

```python
        self.enable_analyze_frame = True
        Clock.schedule_interval(self.analyze_filter,1)
                                                      
    def analyze_filter(self, dt):
        self.enable_analyze_frame = True

    def analyze_pixels_callback(self, pixels, image_size, image_pos,
                                scale, mirror):
	if self.enable_analyze_frame:
	    self.enable_analyze_frame = False
	    # place usual analyse code inside this if block
```
One could modify this in various ways, for example a single sample after some delay.

One way to improve performance is to reduce the `analyze_pixels_resolution` as shown above. This option may alter the qualitative behavior, perhaps because of resolution bias in some third party analyzers. Experiment, some analysis code will work well at much less than VGA resolution. 

The analysis code must be lean. So for example Keras is a complete development environment, a whole bunch of stuff you don't need to run an inference. Port the application to Tensorflow Lite, then use the tflite-runtime not the full Tensorflow Lite.

## Camera Behavior

### A Physical Camera

A camera is a single physical device with a software api, it is not a software object though it can look like one. It is a physical object with physical constraints. 

### Resolution

In the context of a camera, resolution has several uses. It is always a tuple, in this context (width, height).

#### Sensor Resolution

This is a phyical property of the sensor module. The default behavior of `connect_camera()` is to use the maximum resolution provided by the camera provider. Is can be overridden with the `sensor_resolution` option, but in general camera providers take this a a hint which may be ignored or re-interpreted. `GStreamer` ignores this option, `picamera` may require it.

#### Cropped Sensor Resolution

The [sensor resolution](https://github.com/Android-for-Python/Camera4Kivy#sensor-resolution) cropped according to the orientation of the sensor, the orientation of the Preview, and the aspect ratio of the Preview. The will impact the capture resolution, for example a 16:9 aspect image maybe cropped from a 4:3 sensor image. Thus the product of width and height will less for 16:9 that for 4:3 in this case.

Rotating a mobile device also rotates the sensor, the highest resolution images are obtained when the Priview widget orientation is the same as the device orientation. Conversly for example a landscape preview with the device in portrait orientation will result in an image width resolution that is the sensor height resolution.

This behaviour is a characteric of the camera sensor having physical constraints. Notably that image sensors are usually not square, they are rectangular and give the highest quality results when the sensor has the same orientation as the captured image. This is mostly transparent to the app user unless the sensor resolution is low, or a photo capture has lower than expected resolution.

#### Preview Resolution

Is a physical property of the screen ([display resolution](https://github.com/Android-for-Python/Camera4Kivy#display-resolution)) and the Preview widget size on the screen. The preview resolution can be less than or greater than the cropped sensor resolution.

#### Capture Resolution

The resolution of a capture. A photo capture resolution is [cropped sensor resolution](https://github.com/Android-for-Python/Camera4Kivy#cropped-sensor-resolution). Video resolution is one to the standard resolutions, depending on the cropped sensor resolution. A screenshot capture size in pixels is the [Preview resolution](https://github.com/Android-for-Python/Camera4Kivy#preview-resolution). 

#### Analysis Resolution

Analysis resolution is less than or equal to [cropped sensor resolution](https://github.com/Android-for-Python/Camera4Kivy#cropped-sensor-resolution). It may be useful to reduce this in order to decrease analysis time, at the cost of analysis resolution.  

The `analyze_pixels_callback()` resolution may be changed with the `analyze_pixels_resolution` camera connect option. The scale parameter allows re-scaling of the analysis results to the Preview resolution.

The `analyze_imageproxy_callback()` implements a graceful degradation mechanism. This automatically reduces frame rate and/or image resolution. A very slow frame analysis will case the feed to stop.  

#### Display Resolution.

Nothing to do with a camera, it is a physical property of a screen. A scalar measured in dpi.

## Camera Provider

Camera4Kivy depends on a 'camera provider' to access the OS camera api. On most platforms this uses the same provider as Kivy, with modified defaults.

| Platform    | Provider      | Requires       |
|-------------|---------------|----------------|
| Windows     | [OpenCV](https://github.com/Android-for-Python/camera4kivy#opencv)                      |
|             | [Gstreamer](https://github.com/Android-for-Python/camera4kivy#gstreamer)                      |
| Macos       | [AVFoundation](https://github.com/Android-for-Python/camera4kivy#avfoundation)| OSX >= 10.7    |   
| Linux       | [Gstreamer](https://github.com/Android-for-Python/camera4kivy#gstreamer)                      |
|             | [OpenCV](https://github.com/Android-for-Python/camera4kivy#opencv)                      |
| Rasberry    | [Picamera](https://github.com/Android-for-Python/camera4kivy#picamera)    | <= Buster      |
|             | [Gstreamer](https://github.com/Android-for-Python/camera4kivy#gstreamer)  |  <= Buster |
|             |[OpenCV](https://github.com/Android-for-Python/camera4kivy#opencv) |  <= Buster  |
|             | [Picamera2](https://github.com/Android-for-Python/camera4kivy#picamera2)    | >= Bullseye      |
| Android     | [CameraX](https://github.com/Android-for-Python/camera4kivy#android-camera-provider)                      |  Android >= 5.0 |
| iOS         | [AVFoundation](https://github.com/Android-for-Python/camera4kivy#avfoundation)                      |

Like Kivy, the first available provider is selected. Some camera provider specific behavior should be expected. For example a switch to a camera that does not exist will be ignored on MacOS and Rasberry Pi, but generate a screen message with OpenCV or GStreamer. Camera resolution defaults to the maximum available camera provider resolution, except on Raspberry Pi where the default is (1024, 768).

You can remove a camera provider ('picamera' in the example below) from the above lists by inserting this code **before** `from kivy.app import App`.

```python
from kivy import kivy_options
providers= list(kivy_options['camera'])
providers.remove('picamera')
kivy_options['camera'] = tuple(providers)
```

You can read back the chosen camera provider with:

```python
from camera4kivy import CameraProviderInfo

    provider_string = CameraProviderInfo().get_name()
```

### Android Camera Provider

`cd <project directory>`

`git clone https://github.com/Android-for-Python/camerax_provider.git`

`rm -rf camerax_provider/.git`

Set `p4a.hook` to enable the app's use of the camera provider.

`p4a.hook = camerax_provider/gradle_options.py`

### OpenCV

`pip3 install opencv-python`

### GStreamer

Depends on the Linux flavor, but commonly:

`sudo apt-get install gstreamer-1.0`

`sudo apt-get install gstreamer1.0-dev`

### Picamera
Pre-installed

### Picamera2
Raspberry PI Bullseye support currently not available.

### AVFoundation
Pre-installed


## Known Behavior

### Behavior: Android .mp4 Orientation

Video file orientation is incorrect if the preview orientation is not the same as the device orientation. Do not use this layout configuration when recording video. [Google issue tracker](https://issuetracker.google.com/issues/201085351).

### Behavior: Android .jpg Orientation.

Some image viewers (including Kivy Image widget) will incorrectly display a .jpg as rotated by 90 degrees. This occurs if the capture preview orientation is not the same as the device orientation, and the third party viewer does not use the Exif metadata.   

### Behavior: Android armeabi-v7a build installed on an arm64-v8a device

The implementation of Google's camerax gradle dependencies appears to be architecture specific, an app built for armeabi-v7a will crash on an arm64-v8a device. To run on an arm64-v8a device you **must** build for arm64-v8a.

### Behavior: Android "No supported surface combination"

`No supported surface combination is found for camera device - Id : 0.  May be attempting to bind too many use cases.`

On very low end Android devices the camera may have limited hardware resources. So far only one device has exhibited this issue. By default c4k configures connect_camera() for either 'photo and video` or 'photo and image analysis' - this keeps the api as simple as possible. But in this case it is too expensive for the hardware. We can override these configurations.

If the connection is only used for photo use `connect_camera(enable_video = False, ...other options..)`. If the connection is only used for video or data analysis use `connect_camera(enable_photo = False, ...other options..)`. 

