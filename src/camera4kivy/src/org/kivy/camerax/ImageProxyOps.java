package org.kivy.camerax;

import androidx.camera.core.ImageProxy;
import android.graphics.ImageFormat;
import android.graphics.PixelFormat;
import java.lang.IllegalArgumentException;
import java.nio.ByteBuffer;

public class ImageProxyOps {

    private byte[] bytes;

    public ImageProxyOps() {
	this.bytes = new byte[0];
    }

    public byte[] copyYUVtoBytes(ImageProxy image) {
	if (image.getFormat() != ImageFormat.YUV_420_888) {
	    throw new IllegalArgumentException("Invalid image format");
	}

	ByteBuffer yBuffer = image.getPlanes()[0].getBuffer();
	ByteBuffer uBuffer = image.getPlanes()[1].getBuffer();
	ByteBuffer vBuffer = image.getPlanes()[2].getBuffer();

	int ySize = yBuffer.remaining();
	int uSize = uBuffer.remaining();
	int vSize = vBuffer.remaining();

	if (this.bytes.length != ySize + uSize + vSize) {
	    this.bytes = new byte[ySize + uSize + vSize];
	}

	// U and V are swapped
	yBuffer.get(this.bytes, 0, ySize);
	vBuffer.get(this.bytes, ySize, vSize);
	uBuffer.get(this.bytes, ySize + vSize, uSize);

	return this.bytes;
    }    

    public byte[] copyRGBAtoBytes(ImageProxy image) {
	if (image.getFormat() != PixelFormat.RGBA_8888) {
	    throw new IllegalArgumentException("Invalid image format");
	}

	// RGBA bytes are in plane zero
	ByteBuffer buffer = image.getPlanes()[0].getBuffer();

	int size = buffer.remaining();

	if (this.bytes.length != size ) {
	    this.bytes = new byte[size];
	}

	buffer.get(this.bytes, 0, size);

	return this.bytes;
    }    
}
