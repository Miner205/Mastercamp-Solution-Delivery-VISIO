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
    r_max = 0
    r_min = 255
    r_avg = 0

    g_max = 0
    g_min = 255
    g_avg = 0

    b_max = 0
    b_min = 255
    b_avg = 0

    width, height = image.size

    for x in range(width):
        for y in range(height):
            pixel = image.getpixel((x, y))

            if pixel[0] > r_max:
                r_max = pixel[0]
            if pixel[0] < r_min:
                r_min = pixel[0]
            r_avg += pixel[0]

            if pixel[1] > g_max:
                g_max = pixel[1]
            if pixel[1] < g_min:
                g_min = pixel[1]
            g_avg += pixel[1]

            if pixel[2] > b_max:
                b_max = pixel[2]
            if pixel[2] < b_min:
                b_min = pixel[2]
            b_avg += pixel[2]

    nb_pixels = width*height
    return r_avg/nb_pixels, g_avg/nb_pixels, b_avg/nb_pixels, (r_min, r_max), (g_min, g_max), (b_min, g_max)


def get_image_l(image):
    return image.convert("L")


def get_image_l_stats(image):
    l_max = 0
    l_min = 255
    l_avg = 0

    image_size = image.size

    for x in range(image_size[0]):
        for y in range(image_size[1]):
            pixel = image.getpixel((x, y))

            if pixel > l_max:
                l_max = pixel
            if pixel < l_min:
                l_min = pixel
            l_avg += pixel

    return l_avg/(image_size[0] * image_size[1]), (l_min, l_max)


def get_image_histogram(image):
    if image.mode == "RGBA":
        width, height = image.size
        hist = [0]*768
        for x in range(width):
            for y in range(height):
                r, g, b, a = image.getpixel((x, y))
                if a != 0:
                    hist[r] += 1
                    hist[g + 256] += 1
                    hist[b + 512] += 1
        return hist

    return image.histogram()


def get_image_l_contrast(l_max, l_min):
    return (l_max - l_min)/(l_max + l_min)


def get_hue_pixel(image, x, y):
    if image.mode == "RGBA":
        r, g, b, a = image.getpixel((x, y))
        if a == 0:
            return 360
    else:
        r, g, b = image.getpixel((x, y))
    pixel_hue = round(math.atan2(math.sqrt(3)*(g - b), 2*r - g - b)*(180/math.pi))
    if pixel_hue < 0:
        return 360 + pixel_hue
    return pixel_hue


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


def create_bin_image_old(image, bin_mask, nb_x_area, nb_y_area, area_border=False):  # not used
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


def create_contour_matrix(image, bin_mask, nb_x_area, nb_y_area):
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

    for distance in range(3):
        for area_x in range(nb_x_area):
            for area_y in range(nb_y_area):
                if area_y > 0 and contour_matrix[area_x][area_y] <= contour_matrix[area_x][area_y - 1] - 2:
                    contour_matrix[area_x][area_y] = contour_matrix[area_x][area_y - 1] - 1
                if area_x > 0 and contour_matrix[area_x][area_y] <= contour_matrix[area_x - 1][area_y] - 4:
                    contour_matrix[area_x][area_y] = contour_matrix[area_x - 1][area_y] - 2
                if area_x < nb_x_area - 1 and contour_matrix[area_x][area_y] <= contour_matrix[area_x + 1][area_y] - 4:
                    contour_matrix[area_x][area_y] = contour_matrix[area_x + 1][area_y] - 2
                if area_y < nb_y_area - 1 and contour_matrix[area_x][area_y] <= contour_matrix[area_x][area_y + 1] - 6:
                    contour_matrix[area_x][area_y] = contour_matrix[area_x][area_y + 1] - 3

    return contour_matrix


def test_contour_matrix():  # not used
    nb_x_area, nb_y_area = 24, 24
    contour_matrix = [
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 8, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 7, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 6, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 5, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 4, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 3, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 2, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    ]

    for distance in range(3):
        for area_x in range(nb_x_area):
            for area_y in range(nb_y_area):
                if area_y > 0 and contour_matrix[area_x][area_y] <= contour_matrix[area_x][area_y - 1] - 2:
                    contour_matrix[area_x][area_y] = contour_matrix[area_x][area_y - 1] - 1
                if area_x > 0 and contour_matrix[area_x][area_y] <= contour_matrix[area_x - 1][area_y] - 4:
                    contour_matrix[area_x][area_y] = contour_matrix[area_x - 1][area_y] - 2
                if area_x < nb_x_area - 1 and contour_matrix[area_x][area_y] <= contour_matrix[area_x + 1][area_y] - 4:
                    contour_matrix[area_x][area_y] = contour_matrix[area_x + 1][area_y] - 2
                if area_y < nb_y_area - 1 and contour_matrix[area_x][area_y] <= contour_matrix[area_x][area_y + 1] - 6:
                    contour_matrix[area_x][area_y] = contour_matrix[area_x][area_y + 1] - 3
        print()
        print(str(distance) + ":")
        for area_y in range(nb_y_area):
            if area_y != 0:
                print()
            for area_x in range(nb_x_area):
                if contour_matrix[area_x][area_y] == 0:
                    print("\t ", end="")
                else:
                    print("\t" + str(contour_matrix[area_x][area_y]), end="")

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


def get_hue_histogram(image):
    width, height = image.size
    hue_hist = [0]*360
    for x in range(width):
        for y in range(height):
            pixel_hue = get_hue_pixel(image, x, y)
            if pixel_hue != 360:
                hue_hist[pixel_hue] += 1
    return hue_hist


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

    contrast = get_image_l_contrast(max_l, min_l)
    print(contrast)

    img_no_bg = remove(img)
    img_no_bg.show()

    msk_bin = create_bin_mask(img_no_bg)
    msk_bin.show()

    bin_matrix = create_contour_matrix(img, msk_bin, 8, 8)
    print(bin_matrix)

    img_bin = create_bin_image(img, bin_matrix, 8, 8)
    img_bin.show()

    img_bin_histogram = get_image_histogram(img_bin)
    print(img_bin_histogram)
    print(img_bin_histogram[0:256], img_bin_histogram[512:768])
    print(sum(img_bin_histogram[0:256]))

    hue_histogram = get_hue_histogram(img_bin)
    print(hue_histogram)
    print(sum(hue_histogram))

    # test contour matrix repartition
    #test_contour_matrix()
