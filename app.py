import streamlit as st
from azure.storage.blob import BlobServiceClient, BlobClient, ContainerClient
import pandas as pd
from PIL import Image
import io
import pytesseract
from streamlit_cropper import st_cropper
from credentials import connect_str, container_name
from datetime import date
from login import login
import numpy as np

# Initialize connection to Azure Blob Storage
blob_service_client = BlobServiceClient.from_connection_string(connect_str)
container_client = blob_service_client.get_container_client(container_name)

def upload_to_blob(file, filename):
    blob_client = container_client.get_blob_client(filename)
    blob_client.upload_blob(file, overwrite=True)

def list_blobs():
    blob_list = container_client.list_blobs()
    return [blob.name for blob in blob_list]

def download_blob(filename):
    blob_client = container_client.get_blob_client(filename)
    stream = io.BytesIO()
    stream.write(blob_client.download_blob().readall())
    stream.seek(0)
    return stream

def read_table_from_image(image, date=date.today(), shop='Onbekend'):
    """
    Read a table from an image file.
    Args:
        image: The PIL Image object.
        datum: Date string for the data.
        winkel: Shop name for the data.
    Returns:
        pd.DataFrame: A DataFrame containing the parsed table data.
    """
    # Convert PIL Image to OpenCV format
    image_array = np.array(image)
    # grayscale_image = cv2.cvtColor(image_array, cv2.COLOR_BGR2GRAY)
    # threshold_image = cv2.threshold(grayscale_image, 127, 255, cv2.THRESH_BINARY_INV)[1]
    # Convert the image to grayscale
    grayscale_image = np.dot(image_array[...,:3], [0.2989, 0.5870, 0.1140])

    # Apply thresholding
    threshold_image = np.where(grayscale_image > 127, 255, 0).astype(np.uint8)

    # Invert the binary image
    threshold_image = 255 - threshold_image

    text = pytesseract.image_to_string(threshold_image, lang="eng")
    text_lines = text.split("\n")

    list_n = []
    list_amount = []
    list_discount = []
    list_item = []
    list_date = []
    list_shop = []

    for line in text_lines:
        # st.write(line)
        line = line.replace('.','').replace('|','').replace(':','').replace('=','').lower()
        line_to_string = line.split(' ')
        if len(line_to_string) > 1:
            if line_to_string[-1] != '':
                amount = line_to_string[-1]
                item = ' '.join(line_to_string[:-1])
            elif line_to_string[-1] == '':
                amount = line_to_string[-2]
                item = ' '.join(line_to_string[:-2])
            else:
                item = ''
                amount = ''
            # st.write(str(line_to_string), ' / ', item, ' / ', amount)
            list_n.append(1)
            list_amount.append(amount)
            list_item.append(item)
            list_shop.append(shop)
            list_date.append(date)
            list_discount.append(0)

    df = pd.DataFrame(
        {'Aantal': list_n,
         'Omschrijving': list_item,
         'Bedrag': list_amount,
         'Korting': list_discount,
         'Winkel': list_shop,
         'Datum': list_date
        })
    
    return df

if login() == 1:

    # Streamlit interface
    st.set_page_config(page_title="DONI", layout="wide")
    st.title("Supermarket Receipt Analyzer")

    option = st.radio("Choose input method:", ('Upload file', 'Take picture with camera'))

    uploaded_file = None
    if option == 'Take picture with camera':
        uploaded_file = st.camera_input('Take picture of receipt')
    elif option == 'Upload file':
        uploaded_file = st.file_uploader('Upload an image file', type=['jpg', 'jpeg', 'png'])

    shop = st.text_input('Naam winkel', value='ah')
    total_amount = st.text_input('Totaalbedrag kassabon', value='0')

    if uploaded_file is not None:
        image = Image.open(uploaded_file)
        # st.image(image, caption='Uploaded Receipt.', use_column_width=True)

        # Resize the image using PIL
        # resized_image = image.resize((300, int(300 * image.height / image.width)))  # Maintain aspect ratio\
        resized_image=image
        image1= resized_image
        image2= resized_image    

        # Create two columns for cropping
        col1, col2, col3, col4 = st.columns([3, 3, 2, 4])

        with col1:
            cropped_image1 = st_cropper(image1, aspect_ratio=None, key=1)
            # st.image(cropped_image1, caption='Cropped Receipt Part 1', use_column_width=True)

        with col2:
            cropped_image2 = st_cropper(image2, aspect_ratio=None, key=2)
            # st.image(cropped_image2, caption='Cropped Receipt Part 2', use_column_width=True)

        with col3:
            # Combine the two cropped images
            combined_image_width = cropped_image1.width + cropped_image2.width
            combined_image_height = max(cropped_image1.height, cropped_image2.height)
            combined_image = Image.new('RGB', (combined_image_width, combined_image_height))

            combined_image.paste(cropped_image1, (0, 0))
            combined_image.paste(cropped_image2, (cropped_image1.width, 0))
            st.image(combined_image, caption='Combined Receipt', use_column_width=True)

        with col4:
        # Extracting table from combined image
            df = read_table_from_image(combined_image, shop=shop)
        # st.write("Extracted Data:")
            edited_df = st.data_editor(df, hide_index=True)
        
        if st.button('Save Receipt Data'):
            receipt_filename = f"receipt_{shop}_{total_amount}_{str(date.today()).replace('-','')}.csv"
            csv_data = edited_df.to_csv(index=False, sep=';').encode()
            upload_to_blob(io.BytesIO(csv_data), receipt_filename)
            st.success(f"Receipt data saved as {receipt_filename}")

    # receipts = list_blobs()
    # selected_receipt = st.selectbox("Select a receipt to load:", receipts)
    # if selected_receipt:
    #     stream = download_blob(selected_receipt)
    #     df = pd.read_csv(stream)
    #     st.write("Loaded Receipt Data:")
    #     st.dataframe(df)

    # # Load all receipts for plotting
    # all_data = []
    # for receipt in receipts:
    #     stream = download_blob(receipt)
    #     df = pd.read_csv(stream)
    #     all_data.append(df)

    # if all_data:
    #     all_receipts_df = pd.concat(all_data)
    #     all_receipts_df['Year-Week'] = pd.to_datetime(all_receipts_df['Date']).dt.strftime('%Y-%U')
    #     spending_per_week = all_receipts_df.groupby('Year-Week')['Price'].sum().reset_index()
    #     fig = px.line(spending_per_week, x='Year-Week', y='Price', title='Total Spending per Year-Week')
    #     st.plotly_chart(fig)
