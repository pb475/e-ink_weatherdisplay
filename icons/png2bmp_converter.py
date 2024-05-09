from PIL import Image
import numpy as np
import os

threshold = 110

locations = [
    'pack1/16/png/', 'pack1/24/png/', 'pack1/32/png/', 'pack1/64/png/', 'pack1/96/png/', 'pack1/128/png/', 'pack1/256/png/', 'pack1/512/png/',
    'pack2/16/png/', 'pack2/24/png/', 'pack2/32/png/', 'pack2/64/png/', 'pack2/96/png/', 'pack2/128/png/', 'pack2/256/png/', 'pack2/512/png/']


print('Processing...')
for location in locations:
    if not os.path.exists(location):
        continue
    newlocation = location.replace('png/','bmp/')
    # Create the new location if it does not exist
    if not os.path.exists(newlocation):
        os.makedirs(newlocation)

    # Get the file names
    file_names = os.listdir(location)
    for file in file_names:
        print(file)

        # Open the image, and start doing the conversion
        img = Image.open(location+file).convert('RGBA')
        data = [img.getpixel((x, y)) for x in range(img.width) for y in range(img.height)]

        last_values = [pixel[-1] for pixel in data]
        width_height=int(np.sqrt(len(last_values)))
        #
        data = np.array(last_values).reshape((width_height, width_height))
        data[data > threshold] = 255; data[data <= threshold] = 0
        #
        data = np.rot90(np.rot90(np.rot90(data)))
        inverted_data = 255 - data
        im_inverted = Image.fromarray(inverted_data.astype(np.uint8), mode='L')
        #
        flipped_data = np.fliplr(inverted_data)
        im_flipped = Image.fromarray(flipped_data.astype(np.uint8), mode='L')
        #
        im_flipped.save(newlocation+file.replace('.png', '.bmp'))
        im_inverted.save(newlocation+file.replace('.png', '_flipped.bmp'))
print('Done!')