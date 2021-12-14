package org.kivy.camerax;

//# General
import java.io.File;
import java.util.concurrent.Executor;
import java.util.concurrent.Executors;
import java.util.concurrent.ExecutionException;

import com.google.common.util.concurrent.ListenableFuture;

import org.kivy.android.PythonActivity;

import android.app.Activity;
import android.util.Size;
import android.util.Rational;
import android.graphics.Rect;
import android.graphics.SurfaceTexture;
import android.content.Context;
import android.content.ContentResolver;
import android.content.ContentValues;
import android.net.Uri;
import android.provider.MediaStore;

//MediaActionSound = import android.media.MediaActionSound;

import androidx.core.content.ContextCompat;
import androidx.camera.core.Camera;
import androidx.camera.core.CameraState;
import androidx.camera.core.Preview;
import androidx.camera.core.AspectRatio;
import androidx.camera.core.ImageCapture; 
import androidx.camera.core.VideoCapture;
import androidx.camera.core.FocusMeteringAction;
import androidx.camera.core.MeteringPoint;
import androidx.camera.core.SurfaceOrientedMeteringPointFactory;
import androidx.camera.core.ImageAnalysis;
import androidx.camera.lifecycle.ProcessCameraProvider;
import androidx.camera.core.UseCaseGroup; 
import androidx.camera.core.CameraSelector;
import androidx.camera.core.ZoomState;
import androidx.camera.core.ViewPort;
import androidx.lifecycle.ProcessLifecycleOwner;
import androidx.lifecycle.LifecycleOwner;

// Local Java
import org.kivy.camerax.ImageSavedCallback;
import org.kivy.camerax.VideoSavedCallback;
import org.kivy.camerax.ImageAnalysisAnalyzer;
import org.kivy.camerax.KivySurfaceProvider;
import org.kivy.camerax.CallbackWrapper;

class CameraX {

    // Initial State
    private boolean photo;
    private boolean video;
    private boolean analysis;
    private int lensFacing;
    private int [] cameraResolution;  
    private int aspectRatio;
    private CallbackWrapper callbackClass;
    private int flashMode;
    private int imageOptimize;
    private float zoomScaleFront;
    private float zoomScaleBack;
    private int dataFormat;

    // Connect State
    private int viewPortWidth;
    private int viewPortHeight;
    private Rect cropRect;
    private Size resolution;
    private int rotation;

    // Run time State                 
    private Executor executor = Executors.newSingleThreadExecutor();
    private UseCaseGroup useCaseGroup = null;
    private Preview preview = null;
    private ProcessCameraProvider cameraProvider = null;
    private ImageCapture imageCapture = null;
    private VideoCapture videoCapture = null;
    private Camera camera = null;
    private KivySurfaceProvider kivySurfaceProvider = null;
    private boolean videoIsRecording = false;
    private boolean selectingCamera = false;
    private boolean imageIsReady = false;
    
    public CameraX(boolean photo,
		   boolean video,
		   boolean analysis,
		   String facing,
		   int[] resolution,
		   String aspect_ratio,
		   CallbackWrapper callback_class,
		   String flash,
		   String optimize,
		   float zoom_scale,
		   String data_format) {

	this.photo = photo;
	this.video = video;
	this.analysis = analysis;
	if (this.analysis == true) {
	    this.video = false;
	}
	if (facing.equals("front")) {
            this.lensFacing = CameraSelector.LENS_FACING_FRONT;
	} else {
	    this.lensFacing = CameraSelector.LENS_FACING_BACK;
	}
        cameraResolution = resolution;

	if (aspect_ratio.equals("16:9")) {
	    this.aspectRatio = AspectRatio.RATIO_16_9;
	} else {
	    this.aspectRatio = AspectRatio.RATIO_4_3;
	}
        this.callbackClass = callback_class;

	if (flash.equals("on")) {
	    this.flashMode = ImageCapture.FLASH_MODE_ON;
        } else if (flash.equals("auto")) {
            this.flashMode = ImageCapture.FLASH_MODE_AUTO;
	} else {
            this.flashMode = ImageCapture.FLASH_MODE_OFF;	    
	}

        if (optimize.equals("quality")) {
            this.imageOptimize = ImageCapture.CAPTURE_MODE_MAXIMIZE_QUALITY;
	} else {
            this.imageOptimize = ImageCapture.CAPTURE_MODE_MINIMIZE_LATENCY;
	}
	    
        this.zoomScaleFront = zoom_scale;
        this.zoomScaleBack = zoom_scale;

	if (data_format.equals("rgba")) {
            this.dataFormat = ImageAnalysis.OUTPUT_IMAGE_FORMAT_RGBA_8888;
        } else {
            this.dataFormat = ImageAnalysis.OUTPUT_IMAGE_FORMAT_YUV_420_888;
	}
    }

    //##############################
    //# Android CameraX
    //##############################

    public void setViewPort(int []view_port_size) {
	this.viewPortWidth = view_port_size[0];
        this.viewPortHeight = view_port_size[1];
    }

    public void startCamera() {
	Context context =  PythonActivity.mActivity.getApplicationContext();
	
	final ListenableFuture<ProcessCameraProvider> cameraProviderFuture =
	    ProcessCameraProvider.getInstance(context);

	cameraProviderFuture.addListener(new Runnable() {
		@Override
		public void run() {
		    try {
			ProcessCameraProvider cameraProvider =
			    cameraProviderFuture.get();
			CameraX.this.cameraProvider = cameraProvider;
			configureCamera();
		    } catch (ExecutionException | InterruptedException e) {
			// No errors need to be handled for this Future.
			// This should never be reached.
		    }
		}
	    }, ContextCompat.getMainExecutor(context));
    }

    public void configureCameraMainThread() {
	Context context =  PythonActivity.mActivity.getApplicationContext();
	Executor executor = ContextCompat.getMainExecutor(context);
	executor.execute(new Runnable() {
		@Override
		public void run() { configureCamera(); }
	    });
    }
    
    private void configureCamera() {
	Activity mActivity = PythonActivity.mActivity;
	int rotation =
	    mActivity.getWindowManager().getDefaultDisplay().getRotation();

        // ImageAnalysis
	ImageAnalysis imageAnalysis = null;
	if (this.analysis) {
            int strategy = ImageAnalysis.STRATEGY_KEEP_ONLY_LATEST;
            ImageAnalysis.Builder ib = new ImageAnalysis.Builder();
            if (cameraResolution.length != 0) {
                ib.setTargetResolution(new Size(cameraResolution[0],
						cameraResolution[1]));
            } else {
                ib.setTargetAspectRatio(this.aspectRatio);
	    }
            ib.setOutputImageFormat(this.dataFormat); 
            ib.setBackpressureStrategy(strategy);
            ib.setTargetRotation(rotation);  
            imageAnalysis = ib.build();
            ImageAnalysisAnalyzer iaa =
		new ImageAnalysisAnalyzer(this.callbackClass);
            imageAnalysis.setAnalyzer(executor, iaa); 
	}

	// ImageCapture
	if (this.video) {
	    VideoCapture.Builder cb = new VideoCapture.Builder();
	    if (cameraResolution.length != 0) {
		cb.setTargetResolution(new Size(cameraResolution[0],
						cameraResolution[1]));
	    } else {                
		cb.setTargetAspectRatio(this.aspectRatio);
	    }
	    cb.setTargetRotation(rotation);
	    this.videoCapture = cb.build();
	}
	    
	if (this.photo) {
	    ImageCapture.Builder cb = new ImageCapture.Builder();
	    cb.setFlashMode(this.flashMode);
	    cb.setCaptureMode(this.imageOptimize);
	    if (cameraResolution.length != 0) {
		cb.setTargetResolution(new Size(cameraResolution[0],
						cameraResolution[1]));
	    } else {                
		cb.setTargetAspectRatio(this.aspectRatio);
	    }
	    cb.setTargetRotation(rotation);
	    this.imageCapture = cb.build();
	}

        // Preview
	int aspect = this.aspectRatio;
        if (cameraResolution.length != 0) {
            if ((Math.max(cameraResolution[0],cameraResolution[1]) /
		 Math.min(cameraResolution[0],cameraResolution[1]) > 1.5)) {
		aspect = AspectRatio.RATIO_16_9;
            } else {
		aspect = AspectRatio.RATIO_4_3;
	    }
	}
        this.preview = new Preview.Builder()
	    .setTargetAspectRatio(aspect)
	    .build();

        // ViewPort
	Rational vpAspect = new Rational(this.viewPortWidth,
					 this.viewPortHeight);
        ViewPort viewPort = new ViewPort.Builder(vpAspect, rotation).build(); 

        // UseCaseGroup
        UseCaseGroup.Builder ucgb = new UseCaseGroup.Builder();
        ucgb.setViewPort(viewPort);
        ucgb.addUseCase(this.preview);
	if (this.video) {
	    ucgb.addUseCase(this.videoCapture);
	}
	if (this.photo) {
	    ucgb.addUseCase(this.imageCapture);
	}
        if (this.analysis) {
            ucgb.addUseCase(imageAnalysis);
	}
        this.useCaseGroup = ucgb.build();

	bindPreview();
    }

    private void bindPreview() {
        // CameraSelector
	CameraSelector cameraSelector;
	if (this.lensFacing == CameraSelector.LENS_FACING_BACK) {
	    cameraSelector = CameraSelector.DEFAULT_BACK_CAMERA;
	} else {
	    cameraSelector = CameraSelector.DEFAULT_FRONT_CAMERA;
	}
        
        // Bind
        this.cameraProvider.unbindAll();
	LifecycleOwner plo = ProcessLifecycleOwner.get();
        this.camera = this.cameraProvider.bindToLifecycle(plo,
							  cameraSelector,
							  this.useCaseGroup);

	// Set touch state
	float zoom = zoomScaleFront;
        if (this.lensFacing == CameraSelector.LENS_FACING_BACK) {
            zoom = zoomScaleBack;
        } 
        this.camera.getCameraControl().setLinearZoom(zoom);
        focus((float)0.5,(float)0.5);

	this.cropRect = this.preview.getResolutionInfo().getCropRect();
	this.resolution = this.preview.getResolutionInfo().getResolution();
	this.rotation = this.preview.getResolutionInfo().getRotationDegrees();
	
	this.callbackClass.callback_config(this.cropRect,
					   this.resolution,
					   this.rotation);

    }

    public boolean imageReady() {
	if (this.imageIsReady) {
	    if (this.kivySurfaceProvider != null) {
		kivySurfaceProvider.KivySurfaceTextureUpdate();
	    }
	    return true;
	}
	return false;
    }
    
    public void setTexture(int texture_id, int[] size) {
	Context context =  PythonActivity.mActivity.getApplicationContext();
	Executor mainExecutor = ContextCompat.getMainExecutor(context);

        this.kivySurfaceProvider = new KivySurfaceProvider(texture_id,
							   mainExecutor, 
							   size[0],
							   size[1]);
	this.imageIsReady = false;
        this.kivySurfaceProvider.surfaceTexture.setOnFrameAvailableListener(
		  new SurfaceTexture.OnFrameAvailableListener() {
            @Override
            public void onFrameAvailable(final SurfaceTexture surfaceTexture) {
		CameraX.this.imageIsReady = true;
            }
        });  
    }
    
    public void setSurfaceProvider(boolean enable) {
	if (enable) {
	    this.preview.setSurfaceProvider(this.kivySurfaceProvider);
	} else {
	    this.preview.setSurfaceProvider(null);
	}
    }

    public void unbind_camera() {
        if (this.cameraProvider != null) {
	    this.cameraProvider.unbindAll();
	    this.cameraProvider = null;
	    this.useCaseGroup = null;
	    this.preview = null;
	    this.camera = null;
	    this.imageCapture = null;
	    this.videoCapture = null;
	    this.kivySurfaceProvider = null;
	    this.videoIsRecording = false;
	    this.selectingCamera = false;
	}
    }
        
    //##############################
    //# User Events
    //##############################
    
    public void select_camera(String facing) { 
        if (!this.selectingCamera) {
	    this.selectingCamera = true;
	    this.lensFacing = CameraSelector.LENS_FACING_BACK;
            if (facing.equals("front")) {
                this.lensFacing = CameraSelector.LENS_FACING_FRONT;
	    }
	    bindPreview();
	    this.selectingCamera = false;
	}
    }
        

    public void focus(float x, float y) {
	SurfaceOrientedMeteringPointFactory factory =
	    new SurfaceOrientedMeteringPointFactory((float)1.0,(float)1.0);
        MeteringPoint point = factory.createPoint(x / this.viewPortWidth,
						  y / this.viewPortHeight);
	FocusMeteringAction action =
	    new FocusMeteringAction.Builder(point).build();
	if (this.camera != null) { 
	    this.camera.getCameraControl().startFocusAndMetering(action);
	}
    }

    public void zoom(float scale, boolean absolute) {
        if (this.camera != null) {
            ZoomState zs =
		this.camera.getCameraInfo().getZoomState().getValue();
	    float newScale = scale;
	    if (absolute == false) {
		newScale = zs.getZoomRatio() * scale;
	    }
            newScale = Math.min(newScale,zs.getMaxZoomRatio());
            newScale = Math.max(newScale,zs.getMinZoomRatio());
            this.camera.getCameraControl().setZoomRatio(newScale);
            zs = this.camera.getCameraInfo().getZoomState().getValue();
            if (this.lensFacing == CameraSelector.LENS_FACING_BACK) {
                this.zoomScaleBack = zs.getLinearZoom();
            } else {
                this.zoomScaleFront = zs.getLinearZoom();
	    }
	}
    }
    
    public String flash(String mode) {
	if (this.photo) {
	    this.flashMode = ImageCapture.FLASH_MODE_OFF;
	    if (mode.equals("on")) {
		this.flashMode = ImageCapture.FLASH_MODE_ON;
	    } else if (mode == "auto") {
		this.flashMode = ImageCapture.FLASH_MODE_AUTO;
	    }
	    this.imageCapture.setFlashMode(this.flashMode);
	}
        return mode;
    }

    public void stop_capture_video() {
        if (this.video && this.videoIsRecording) {
            this.videoCapture.stopRecording();
            this.videoIsRecording = false;
	}
    }
        
    public void capture_video(String location, String filename,
			      boolean fileStorage) {
        if (this.video && !this.videoIsRecording) {
	    this.videoIsRecording = true;
	    VideoCapture.OutputFileOptions vcf;
            if (fileStorage) {
                String filePath = location + "/" + filename;
                File videoFile = new File(filePath);
                vcf = new VideoCapture.OutputFileOptions.Builder(videoFile)
		    .build();
            } else {
                ContentResolver cr =
		    PythonActivity.mActivity.getContentResolver();
                Uri collection = MediaStore.Video.Media.EXTERNAL_CONTENT_URI;
                ContentValues cv = new ContentValues();
                cv.put(MediaStore.MediaColumns.DISPLAY_NAME, filename);
                cv.put(MediaStore.MediaColumns.MIME_TYPE, "video/mp4");
                cv.put(MediaStore.MediaColumns.RELATIVE_PATH, location);
                vcf = new VideoCapture.OutputFileOptions.Builder(cr,
								 collection,
								 cv).build();
		VideoSavedCallback vsc =
		    new VideoSavedCallback(this.callbackClass);
		this.videoCapture.startRecording(vcf,executor,vsc);
	    }
	}
    }

    public void capture_photo(String location, String filename,
			      boolean fileStorage) {
	if (this.photo) {
	    ImageCapture.OutputFileOptions icf;
	    if (fileStorage) {
		String filePath = location + "/" + filename;
		File photoFile = new File(filePath);
		icf = new ImageCapture.OutputFileOptions.Builder(photoFile)
		    .build();
	    } else {
		ContentResolver cr = PythonActivity.mActivity.getContentResolver();
		Uri collection = MediaStore.Images.Media.EXTERNAL_CONTENT_URI;
		ContentValues cv = new ContentValues();
		cv.put(MediaStore.MediaColumns.DISPLAY_NAME, filename);
		cv.put(MediaStore.MediaColumns.MIME_TYPE, "image/jpeg");
		cv.put(MediaStore.MediaColumns.RELATIVE_PATH, location);
		icf = new ImageCapture.OutputFileOptions.Builder(cr,
								 collection,
								 cv).build();
	    }
	    ImageSavedCallback isc = new ImageSavedCallback(this.callbackClass);
	    this.imageCapture.takePicture(icf,executor,isc);
	}
    }
}


