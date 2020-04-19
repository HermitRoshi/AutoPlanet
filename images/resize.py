import sys
import glob
from PIL import Image

def autocrop_image(image, border = 0):
    # Get the bounding box
    bbox = image.getbbox()

    # Crop the image to the contents of the bounding box
    image = image.crop(bbox)

    # Determine the width and height of the cropped image
    (width, height) = image.size

    # Add border
    width += border * 2
    height += border * 2

    size = max(width, height)
    # Create a new image object for the output image
    cropped_image = Image.new("RGBA", (size, size), (0,0,0,0))

    # Paste the cropped image onto the new image
    cropped_image.paste(image, (border, border))

    # Done!
    return cropped_image
    

filePaths = glob.glob("old" + "/*.png") #search for all png images in the folder

for filePath in filePaths:
    image=Image.open(filePath)

    # Do the cropping
    image = autocrop_image(image, 0)

    # Save the output image
    image.save("new//"+filePath)
