import cv2
import pytesseract
import glob
import pandas as pd
import numpy as np

folder = "/Users/nicobrand/Library/Mobile Documents/com~apple~CloudDocs/Python projects/bon/" 
filename_output_bonnen = folder + 'bonnen_output.csv'
filename_log_txt = folder + 'log.txt'

def find_files(folder=folder):
    files = []
    for filepath in glob.iglob(f'''{folder}/*'''):
        files.append(filepath)
    return files

def read_table_from_image(image_path, datum='19000101', winkel='Onbekend'):
    """
    Read a table from an image file.
    Args:
        image_path (str): The path to the image file.
    Returns:
        list: A list of lists containing the text from the table.
    """
    # try:
    image = cv2.imread(image_path)
    grayscale_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    threshold_image = cv2.threshold(grayscale_image, 127, 255, cv2.THRESH_BINARY_INV)[1]

    text = pytesseract.image_to_string(threshold_image, lang="eng")
    text_lines = text.split("\n")

    table_data = []

    list_desc = []
    list_val = []
    list_valdot = []
    list_n = []

    for line in text_lines:
        new_line_val = line.rsplit(' ', 1)[-1]
        
        #Split on comma in last part of string
        if ',' in new_line_val:
            value = new_line_val
        else:
            value = ''
        list_val.append(value)
        new_line_val_dot = line.rsplit(' ', 1)[-1]
        
        #Split on dot in last part of string
        if '.' in new_line_val_dot:
            valuedot = new_line_val_dot.replace('B','')
        else:
            valuedot = ''
        list_valdot.append(valuedot)
        new_line_n = line.rsplit(' ', -1)[0]
        
        #Split on space in last part of string
        if len(new_line_n) < 2:
            n = new_line_n
        else:
            n = ''
        list_n.append(n)

        #Replace string on value and dot
        new_line_desc = line.replace(value,'').replace(n,'').replace(valuedot,'').replace(' B', '')
        list_desc.append(new_line_desc)

        table_data.append(line.split())

    df = pd.DataFrame(
        {'Aantal': list_n,
        'Omschrijving': list_desc,
        'Bedrag': list_val,
        'Bedragpunt': list_valdot,
        'Winkel': winkel,
        'Datum': datum
        })
    df = df.loc[(df['Aantal'] == '1') | (df['Aantal'] == '2') | (df['Aantal'] == '3') | (df['Aantal'] == '4')| (df['Aantal'] == '5')| (df['Aantal'] == '6')| (df['Aantal'] == '7')| (df['Aantal'] == '8')| (df['Aantal'] == '9') | (df['Aantal'] == '10')]
    df['Bedrag'] = np.where(df['Bedrag'] == '',df['Bedragpunt'],df['Bedrag'])
    del df['Bedragpunt']
    print(df)

        
    return df


files = find_files(folder=folder)
# print(files)

for i in files:
    if 'ah' in i and 'jpeg' in i and '25' in i:
        print(i)
        read_table_from_image(i)