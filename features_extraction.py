import os
from PIL import Image, ExifTags
from rembg import remove

default_image_path = "Data/train/with_label/dirty/4d7b8b72cd8cfd0b7cad769e3929e0cc37ba3581.temp.jpeg"


def get_file_size(image_path):
    return os.path.getsize(image_path)


def get_image(image_path):
    return Image.open(default_image_path)


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

    img_size = get_image_size(image)

    for x in range(img_size[0]):
        for y in range(img_size[1]):
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

    return avg_r/(img_size[0] * img_size[1]), avg_g/(img_size[0] * img_size[1]), avg_b/(img_size[0] * img_size[1]), (min_r, max_r), (min_g, max_g), (min_b, max_b)


def get_image_l(image):
    return image.convert("L")


def get_image_l_stats(image):
    max_l = 0
    min_l = 255
    avg_l = 0

    for x in range(img_size[0]):
        for y in range(img_size[1]):
            pixel = img_l.getpixel((x, y))

            if pixel > max_l:
                max_l = pixel
            if pixel < min_l:
                min_l = pixel
            avg_l += pixel

    return avg_l/(img_size[0] * img_size[1]), (min_l, max_l)


def get_image_histogram(image):
    return image.histogram()


def get_image_l_contrast(max_l, min_l, avg_l):
    return (max_l - min_l)/avg_l


if __name__ == '__main__':
    file_size = get_file_size(default_image_path)
    print(file_size)
    img = get_image(default_image_path)
    img.show()
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

    result = remove(img)
    result.show()
