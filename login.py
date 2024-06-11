import streamlit as st
import datetime
from urllib.request import urlopen
import re as r
from azure.storage.blob import BlobServiceClient
import io
from credentials import connect_str, container_name_acces
from PIL import Image

# Initialize Blob Service Client and Container Client
blob_service_client = BlobServiceClient.from_connection_string(connect_str)
container_client = blob_service_client.get_container_client(container_name_acces)


# Function to upload a file to Blob Storage
def upload_to_blob(file, filename):
    blob_client = container_client.get_blob_client(filename)
    blob_client.upload_blob(file, overwrite=True)

# Function to list blobs in the container
def list_blobs():
    blob_list = container_client.list_blobs()
    return [blob.name for blob in blob_list]

# Function to download a blob from Blob Storage
def download_blob(filename):
    blob_client = container_client.get_blob_client(filename)
    stream = io.BytesIO()
    stream.write(blob_client.download_blob().readall())
    stream.seek(0)
    return stream

# Function to get the user's public IP address
def get_user_ip():
    d = str(urlopen('http://checkip.dyndns.com/').read())
    return r.compile(r'Address: (\d+\.\d+\.\d+\.\d+)').search(d).group(1)

# Function to check if the IP address is registered and return the last registration date
def is_ip_registered(ip):
    try:
        blob_data = download_blob('registered_ips.txt').read().decode()
        for line in blob_data.splitlines():
            parts = line.split('_')
            if len(parts) == 2 and ip == parts[0]:
                return True, parts[1]  # Return IP registration status and date
        return False, None
    except Exception as e:
        st.error(f"Error reading blob data: {e}")
        return False, None

# Function to register IP address with current date and time
def register_ip(ip):
    current_datetime = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    try:
        blob_data = download_blob('registered_ips.txt').read().decode()
    except:
        blob_data = ""
    updated_data = blob_data + f'{ip}_{current_datetime}\n'
    upload_to_blob(updated_data.encode(), 'registered_ips.txt')

# Function to retrieve the PIN code from the pin.txt file stored in Azure Blob Storage
def get_pin_code():
    try:
        blob_client = container_client.get_blob_client("pin.txt")
        pin_data = blob_client.download_blob().readall().decode()
        return pin_data.strip()  # Remove any leading/trailing whitespace
    except Exception as e:
        st.error(f"Error retrieving PIN code: {e}")
        return None

# Main function to run the Streamlit app
def login():

    pin_code = get_pin_code()
    
    try:
        user_ip = get_user_ip()
    except Exception as e:
        st.error(f"Error fetching IP address: {e}")
        return

    is_registered, last_registration_date = is_ip_registered(user_ip)
    
    if is_registered:
        try:
            last_registration_datetime = datetime.datetime.strptime(last_registration_date, '%Y-%m-%d %H:%M:%S')
            time_since_last_registration = datetime.datetime.now() - last_registration_datetime
            # Convert the duration to hours
            time_since_last_registration_in_hours = round(time_since_last_registration.total_seconds() / 3600, 2)     
            
            if time_since_last_registration.days < 1:
                # st.success("IP Address is already registered.")
                # st.info(f"Laatst verleende toegang was {time_since_last_registration_in_hours} uur geleden.")
                return 1
            else:
                st.title("Login myntydanalyser")
                st.warning("IP Address registered but more than 1 day ago.")
                pin = st.text_input("Enter the PIN to re-register your IP:", type='password')
                if pin == pin_code:  # Replace '1234' with the desired PIN code
                    register_ip(user_ip)
                    st.success("IP Address re-registered successfully.")
                else:
                    st.error("Incorrect PIN. Please try again.")
        except ValueError as ve:
            st.error(f"Error parsing date: {ve}")
    else:
        st.set_page_config(page_title="Login")
        st.warning("Geen toegang. Login 1 dag geldig per uniek IP")
        pin = st.text_input("Voer pincode in:", type='password')
        if pin == pin_code:  # Replace '1234' with the desired PIN code
            register_ip(user_ip)
            st.success("IP Address registered successfully.")
            st.info('Reload page!')
