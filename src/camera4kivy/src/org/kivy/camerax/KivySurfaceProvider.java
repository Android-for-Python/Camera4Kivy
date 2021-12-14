package org.kivy.camerax;

import java.util.concurrent.Executor;
import androidx.camera.core.Preview;
import androidx.camera.core.SurfaceRequest;
import android.graphics.SurfaceTexture;
import android.view.Surface;

// Ref https://developer.android.com/reference/androidx/camera/core/Preview.SurfaceProvider?hl=zh-cn#onSurfaceRequested(androidx.camera.core.SurfaceRequest)

class KivySurfaceProvider implements Preview.SurfaceProvider {
    // This executor must have also been used with Preview.setSurfaceProvider()
    // to ensure onSurfaceRequested() is called on our GL thread.
    Executor mGlExecutor;
    Surface surface;
    public SurfaceTexture surfaceTexture;

    public KivySurfaceProvider(int id,  Executor self_te,
			       int width, int height) {
	surfaceTexture = new SurfaceTexture(id);
	surfaceTexture.setDefaultBufferSize(width, height);

	surface = new Surface(surfaceTexture);
        mGlExecutor = self_te;
    }

    public void KivySurfaceTextureUpdate() {
	surfaceTexture.updateTexImage();
    }

    @Override
    public void onSurfaceRequested(SurfaceRequest request) {
	request.provideSurface(surface, mGlExecutor, (result) -> {});
    }
}
 
