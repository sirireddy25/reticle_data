from django.shortcuts import render
from django.http import HttpResponse
import numpy as np
from PIL import Image
import tempfile
import os

# Create your views here.
def home(request):
    x = 0
    index = 0
    Reticle_array = []

    if request.method == "POST" and request.FILES.get('uploadedImage'):
        x = 1
        uploaded_file = request.FILES['uploadedImage']

        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            for chunk in uploaded_file.chunks():
                temp_file.write(chunk)

        img = Image.open(temp_file.name)
        img = img.convert("L")

        img = np.asarray(img)

        X_POS = []
        Y_POS = []
        LEN_L = []
        DIR_L = []

        '''
        height = 560
        width = 704
        '''

        height, width = img.shape

        encountered_pixels = np.zeros((height, width))


        for y_idx in range(height):
            for x_idx in range(width):
                if img[y_idx, x_idx] > 0x7f or encountered_pixels[y_idx, x_idx]:
                    continue
               
                elif img[y_idx, x_idx] <= 0x7f:
                    #horizontal scan
                    encountered_pixel_count = 0
                    h_length = 0
                    h_start = x_idx
                    while h_start < width and img[y_idx, h_start] <= 0x7f and encountered_pixel_count < 2:
                        if encountered_pixels[y_idx, h_start] == 1:
                            encountered_pixel_count += 1
                        h_length += 1
                        h_start += 1
                   
                    if encountered_pixel_count >= 2:
                        h_length -= 2
                        h_start -=2
                   
                    #vertical scan
                    encountered_pixel_count = 0
                    v_length = 0
                    v_start = y_idx
                    while v_start < height and img[v_start, x_idx] <= 0x7f and encountered_pixel_count < 2:
                        if encountered_pixels[v_start, x_idx] == 1:
                            encountered_pixel_count += 1
                        v_length += 1
                        v_start += 1
                   
                    if encountered_pixel_count >= 2:
                        v_length -= 2
                        v_start -=2


                    if h_length > v_length:
                        #mark horizontal line as encountered
                        for h_x in range(x_idx, x_idx + h_length):
                            encountered_pixels[y_idx, h_x] = 1
                        X_POS.append(x_idx)
                        Y_POS.append(y_idx)
                        LEN_L.append(h_length)
                        DIR_L.append(0)
                        index += 1
                    else:
                        #mark vertical line as encountered
                        for v_y in range(y_idx, y_idx + v_length):
                            encountered_pixels[v_y, x_idx] = 1
                        X_POS.append(x_idx)
                        Y_POS.append(y_idx)
                        LEN_L.append(v_length)
                        DIR_L.append(1)
                        index += 1

        # Populate Reticle_array
        for idx in range(len(X_POS)):
            reticle_data = ((DIR_L[idx] & 0x03) << 30) | ((LEN_L[idx] & 0x3ff) << 20) | ((Y_POS[idx] & 0x3ff) << 10) | (X_POS[idx] & 0x3ff)
            Reticle_array.append(hex(reticle_data))


        cleaned_array = [hex_val.strip().replace("'", "") for hex_val in Reticle_array]


        reticle_string = ', '.join(cleaned_array)

        
        temp_file.close()

        # Generate response
        response = HttpResponse(content_type='text/plain')

        # Set filename for download based on uploaded file name
        original_filename = uploaded_file.name
        base_filename, file_extension = os.path.splitext(original_filename)
        download_filename = f"{base_filename}_reticle_data.txt"  # Example: originalfile_reticle_data.txt

        response['Content-Disposition'] = f'attachment; filename="{download_filename}"'
        response.write('retical_data[' + str(index) + '] = {' + reticle_string +'};')

        return response

    return render(request, "home.html", {})

