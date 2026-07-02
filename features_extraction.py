import math
import os
# TODO: ExifTags? (also comments in the main)
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


def get_hue_histogram(image):
    width, height = image.size
    hue_hist = [0]*360
    for x in range(width):
        for y in range(height):
            pixel_hue = get_hue_pixel(image, x, y)
            if pixel_hue != 360:
                hue_hist[pixel_hue] += 1
    return hue_hist


def create_bin_mask(image):
    width, height = image.size
    bin_mask = Image.new("L", (width, height))
    for x in range(width):
        for y in range(height):
            pixel_hue = get_hue_pixel(image, x, y)
            if 60 <= pixel_hue <= 180:
                bin_mask.putpixel((x, y), 255)
    return bin_mask


def compute_nb_area(mask, test_view=False):
    width, height = mask.size
    bin_coordinate = [-1, -1, -1, -1]
    x = 0
    while x < width:
        y = 0
        while y < height:
            current_pixel = mask.getpixel((x, y))
            if current_pixel != 0:
                if bin_coordinate[0] < 0:
                    bin_coordinate[0] = x
                    bin_coordinate[1] = y
                    bin_coordinate[2] = x
                    bin_coordinate[3] = y
                elif bin_coordinate[1] > y:
                    bin_coordinate[1] = y
                elif bin_coordinate[2] < x:
                    bin_coordinate[2] = x
                elif bin_coordinate[3] < y:
                    bin_coordinate[3] = y
            y += 1
        x += 1

    approximate_zone_size = ((bin_coordinate[2] - bin_coordinate[0])/6, (bin_coordinate[3] - bin_coordinate[1])/6)
    nb_zone = [0, 0]

    divisors = [1, 1]
    potential_zone_sizes = [width, width]
    test_divisor = 0
    while test_divisor <= math.floor(math.sqrt(width)) and potential_zone_sizes[1] > approximate_zone_size[0]:
        test_divisor += 1
        if width % test_divisor == 0:
            divisors[0] = divisors[1]
            divisors[1] = test_divisor
            potential_zone_sizes[0] = potential_zone_sizes[1]
            potential_zone_sizes[1] = width//divisors[1]

    if abs(approximate_zone_size[0] - potential_zone_sizes[1]) > width//8 and abs(approximate_zone_size[0] - potential_zone_sizes[0]) > width//8:
        nb_zone[0] = 8
    elif potential_zone_sizes[1] >= approximate_zone_size[0] or approximate_zone_size[0] - potential_zone_sizes[1] <= potential_zone_sizes[0] - approximate_zone_size[0]:
        nb_zone[0] = divisors[1]
    else:
        nb_zone[0] = divisors[0]

    divisors = [1, 1]
    potential_zone_sizes = [height, height]
    test_divisor = 0
    while test_divisor <= math.floor(math.sqrt(height)) and potential_zone_sizes[1] > approximate_zone_size[1]:
        test_divisor += 1
        if height % test_divisor == 0:
            divisors[0] = divisors[1]
            divisors[1] = test_divisor
            potential_zone_sizes[0] = potential_zone_sizes[1]
            potential_zone_sizes[1] = height//divisors[1]

    if abs(approximate_zone_size[1] - potential_zone_sizes[1]) > height//8 and abs(approximate_zone_size[1] - potential_zone_sizes[0]) > height//8:
        nb_zone[1] = 8
    elif potential_zone_sizes[1] >= approximate_zone_size[1] or approximate_zone_size[1] - potential_zone_sizes[1] <= potential_zone_sizes[0] - approximate_zone_size[1]:
        nb_zone[1] = divisors[1]
    else:
        nb_zone[1] = divisors[0]

    if test_view is True:
        print("approximate", approximate_zone_size)
        print("nb zone:", nb_zone)
        zone_size = (width//nb_zone[0], height//nb_zone[1])
        print("zone size:", zone_size)
        test_zones = Image.new("RGB", (width, height))
        for x in range(width):
            for y in range(height):
                if (x % zone_size[0]) == zone_size[0] - 1 or (y % zone_size[1]) == zone_size[1] - 1:
                    test_zones.putpixel((x, y), (255, 0, 255))
                elif bin_coordinate[0] <= x <= bin_coordinate[2] and bin_coordinate[1] <= y <= bin_coordinate[3]:
                    test_zones.putpixel((x, y), (255, 255, 255))
                else:
                    test_zones.putpixel((x, y), (0, 0, 0))
        test_zones.show()

    return nb_zone[0], nb_zone[1]


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
                        if area_border is True and (x == area_width - 1 or y == area_height - 1):
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
                        if area_border is True and (x == area_width - 1 or y == area_height - 1):
                            bin_image.putpixel((area_width*area_x + x, area_height * area_y + y), (255, 0, 255, 255))
                        else:
                            bin_image.putpixel((area_width*area_x + x, area_height*area_y + y), image.getpixel((area_width*area_x + x, area_height*area_y + y)))

    return bin_image


if __name__ == '__main__':
    file_size = get_file_size(default_image_path)
    print("file size:", file_size)

    img = get_image(default_image_path)
    img.show()

    #exif = {ExifTags.TAGS[k]: v for k, v in img.getexif().items() if k in ExifTags.TAGS}
    #print(exif)

    img_size = get_image_size(img)
    print("image size:", img_size)

    avg_r, avg_g, avg_b, (min_r, max_r), (min_g, max_g), (min_b, max_b) = get_image_color_stats(img)
    print("average RGB:", (avg_r, avg_g, avg_b))
    print("min/max R:", min_r, max_r)
    print("min/max G:", min_g, max_g)
    print("min/max B:", min_b, max_b)

    img_l = get_image_l(img)
    #img_l.show()

    avg_l, (min_l, max_l) = get_image_l_stats(img_l)
    print("average L:", avg_l)
    print("min/max L:", min_l, max_l)

    img_histogram = get_image_histogram(img)
    print("histogram RGB:", img_histogram)

    img_l_histogram = get_image_histogram(img_l)
    print("histogram L:", img_l_histogram)

    contrast = get_image_l_contrast(max_l, min_l)
    print("contrast:", contrast)

    hue_histogram = get_hue_histogram(img)
    print("histogram hue:", hue_histogram)

    img_no_bg = remove(img)
    #img_no_bg.show()

    msk_bin = create_bin_mask(img_no_bg)
    msk_bin.show()

    nb_area = compute_nb_area(msk_bin, test_view=True)
    print("nb area:", nb_area)

    bin_matrix = create_contour_matrix(img, msk_bin, nb_area[0], nb_area[1])
    print("bin matrix:", bin_matrix)

    img_bin = create_bin_image(img, bin_matrix, nb_area[0], nb_area[1])
    img_bin.show()

    img_bin_histogram = get_image_histogram(img_bin)
    print("nb pixel bin:", sum(img_bin_histogram[0:256]))
    print("histogram bin:", img_bin_histogram)
    print("histogram bin (no G):", img_bin_histogram[0:256], img_bin_histogram[512:768])

    hue_histogram_bin = get_hue_histogram(img_bin)
    print("histogram hue bin:", hue_histogram_bin)

    # test contour matrix repartition
    #test_contour_matrix()
