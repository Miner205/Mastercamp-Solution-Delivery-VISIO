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

    width, height = image.size

    for x in range(width):
        for y in range(height):
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

    nb_pixels = width*height
    return avg_r/nb_pixels, avg_g/nb_pixels, avg_b/nb_pixels, (min_r, max_r), (min_g, max_g), (min_b, max_b)


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


def create_bin_image_old(image, bin_mask, nb_x_area, nb_y_area, area_border=False):
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
                    area_value += bin_mask.getpixel((area_width*area_x + x, area_height*area_y + y))//255

            if area_value >= (area_width*area_height)/8 or above_area_value >= (area_width*area_height)/4:
                for x in range(area_width):
                    for y in range(area_height):
                        if area_border is True and (y == area_height - 1 or x == area_width - 1):
                            bin_image.putpixel((area_width*area_x + x, area_height * area_y + y), (255, 0, 255, 255))
                        else:
                            bin_image.putpixel((area_width*area_x + x, area_height*area_y + y), image.getpixel((area_width*area_x + x, area_height*area_y + y)))

            above_area_value = area_value
            area_value = 0

    return bin_image


def contour_matrix_test(image, bin_mask, nb_x_area, nb_y_area):
    width, height = image.size
    contour_matrix = [[0 for _ in range(nb_y_area)] for _ in range(nb_x_area)]
    area_width = width//nb_x_area
    area_height = height//nb_y_area

    for area_x in range(nb_x_area):
        for area_y in range(nb_y_area):

            for x in range(area_width):
                for y in range(area_height):
                    contour_matrix[area_x][area_y] += bin_mask.getpixel((area_width*area_x + x, area_height*area_y + y))//255
            contour_matrix[area_x][area_y] = (contour_matrix[area_x][area_y]*8)//(area_width*area_height)

    for distance in range(7):
        for area_x in range(nb_x_area):
            for area_y in range(nb_y_area):
                if area_y > 0 and contour_matrix[area_x][area_y] < contour_matrix[area_x][area_y - 1] - 2:
                    contour_matrix[area_x][area_y] = contour_matrix[area_x][area_y - 1] - 1
                if area_x > 0 and contour_matrix[area_x][area_y] < contour_matrix[area_x - 1][area_y] - 4:
                    contour_matrix[area_x][area_y] = contour_matrix[area_x - 1][area_y] - 2
                if area_x < nb_x_area - 1 and contour_matrix[area_x][area_y] < contour_matrix[area_x + 1][area_y] - 4:
                    contour_matrix[area_x][area_y] = contour_matrix[area_x + 1][area_y] - 2
                if area_y < nb_y_area - 1 and contour_matrix[area_x][area_y] < contour_matrix[area_x][area_y + 1] - 6:
                    contour_matrix[area_x][area_y] = contour_matrix[area_x][area_y + 1] - 3

    return contour_matrix


def create_bin_image(image, contour_matrix, nb_x_area, nb_y_area, area_border=False):
    width, height = image.size
    bin_image = Image.new("RGBA", (width, height))
    area_width = width//nb_x_area
    area_height = height//nb_y_area

    for area_x in range(nb_x_area):
        for area_y in range(nb_y_area):

            if contour_matrix[area_x][area_y] > 0:
                for x in range(area_width):
                    for y in range(area_height):
                        if area_border is True and (y == area_height - 1 or x == area_width - 1):
                            bin_image.putpixel((area_width*area_x + x, area_height * area_y + y), (255, 0, 255, 255))
                        else:
                            bin_image.putpixel((area_width*area_x + x, area_height*area_y + y), image.getpixel((area_width*area_x + x, area_height*area_y + y)))

    return bin_image


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

    img_histogram = get_image_histogram(img_l)
    print(img_histogram)

    contrast = get_image_l_contrast(max_l, min_l, avg_l)
    print(contrast)

    img_no_bg = remove(img)
    img_no_bg.show()

    msk_bin = create_bin_mask(img_no_bg)
    msk_bin.show()

    bin_matrix = contour_matrix_test(img, msk_bin, 8, 8)
    print(bin_matrix)

    img_bin = create_bin_image(img, bin_matrix, 8, 8)
    img_bin.show()

