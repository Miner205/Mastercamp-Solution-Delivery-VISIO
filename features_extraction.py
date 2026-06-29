import math
import os
# TODO: ExifTags?
from PIL import Image, ExifTags
from rembg import remove

default_image_path = ("Data/train/with_label/dirty/838.full.jpeg")


def get_file_size(image_path):
    return os.path.getsize(image_path)


def get_image(image_path):
    return Image.open(image_path)


def get_image_size(image):
    return image.size


def get_image_color_stats(image):
    max_r = 0
    min_r = 255
    avg_r = 0

    max_g = 0
    min_g = 255
    avg_g = 0

    max_b = 0
    min_b = 255
    avg_b = 0

    image_size = image.size

    for x in range(image_size[0]):
        for y in range(image_size[1]):
            pixel = image.getpixel((x, y))

            if pixel[0] > max_r:
                max_r = pixel[0]
            if pixel[0] < min_r:
                min_r = pixel[0]
            avg_r += pixel[0]

            if pixel[1] > max_g:
                max_g = pixel[1]
            if pixel[1] < min_r:
                min_g = pixel[1]
            avg_g += pixel[1]

            if pixel[2] > max_b:
                max_b = pixel[2]
            if pixel[2] < min_b:
                min_b = pixel[2]
            avg_b += pixel[2]

    return avg_r/(image_size[0] * image_size[1]), avg_g/(image_size[0] * image_size[1]), avg_b/(image_size[0] * image_size[1]), (min_r, max_r), (min_g, max_g), (min_b, max_b)


def get_image_l(image):
    return image.convert("L")


def get_image_l_stats(image):
    max_l = 0
    min_l = 255
    avg_l = 0

    image_size = image.size

    for x in range(image_size[0]):
        for y in range(image_size[1]):
            pixel = image.getpixel((x, y))

            if pixel > max_l:
                max_l = pixel
            if pixel < min_l:
                min_l = pixel
            avg_l += pixel

    return avg_l/(image_size[0] * image_size[1]), (min_l, max_l)


def get_image_histogram(image):
    return image.histogram()


def get_image_l_contrast(max_l, min_l, avg_l):
    return (max_l - min_l)/avg_l


def get_hue_pixel(image, x, y):
    r, g, b = image.getpixel((x, y))[0:3]
    return math.atan2(math.sqrt(3)*(g - b), 2*r - g - b)*(180/math.pi)


def create_bin_mask(image):
    width, height = image.size
    bin_mask = Image.new("L", (width, height))
    for x in range(width):
        for y in range(height):
            pixel_hue = get_hue_pixel(image, x, y)
            if 60 <= pixel_hue <= 180:
                bin_mask.putpixel((x, y), 255)
    return bin_mask


def compute_nb_area():
    pass


def create_bin_image(image, bin_mask, nb_x_area, nb_y_area):
    width, height = image.size
    bin_image = Image.new("RGBA", (width, height))
    area_width = width//nb_x_area
    area_height = height//nb_y_area
    above_area_value = 0
    area_value = 0
    for area_x in range(nb_x_area):
        for area_y in range(nb_y_area):

            for x in range(area_width):
                for y in range(area_height):
                    area_value += (bin_mask.getpixel((area_width*area_x + x, area_height*area_y + y))/255)

            if area_value >= (area_width*area_height)/8 or above_area_value >= (area_width*area_height)/4:
                for x in range(area_width):
                    for y in range(area_height):
                        if y == area_height - 1 or x == area_width - 1:
                            bin_image.putpixel((area_width*area_x + x, area_height * area_y + y), (255, 0, 255, 255))
                        else:
                            bin_image.putpixel((area_width*area_x + x, area_height*area_y + y), image.getpixel((area_width*area_x + x, area_height*area_y + y)))

            above_area_value = area_value
            area_value = 0

    return bin_image


if __name__ == '__main__':
    file_size = get_file_size(default_image_path)
    print(file_size)
    img = get_image(default_image_path)
    img.show()
    img.save("base.png")
    #exif = {ExifTags.TAGS[k]: v for k, v in img.getexif().items() if k in ExifTags.TAGS}
    #print(exif)
    img_size = get_image_size(img)
    print(img_size)

    avg_r, avg_g, avg_b, (min_r, max_r), (min_g, max_g), (min_b, max_b) = get_image_color_stats(img)
    print((avg_r, avg_g, avg_b))
    print(min_r, max_r)
    print(min_g, max_g)
    print(min_b, max_b)

    img_l = get_image_l(img)
    #img_l.show()

    avg_l, (min_l, max_l) = get_image_l_stats(img_l)
    print(avg_l)
    print(min_l, max_l)

    img_histogram = get_image_histogram(img)
    print(img_histogram)

    contrast = get_image_l_contrast(max_l, min_l, avg_l)
    print(contrast)

    img_no_bg = remove(img)
    img_no_bg.show()
    img_no_bg.save("no_bg.png")

    msk_bin = create_bin_mask(img_no_bg)
    msk_bin.show()
    msk_bin.save("mask.png")

    img_bin = create_bin_image(img, msk_bin, 8, 8)
    img_bin.show()
    img_bin.save("poubelle.png")


