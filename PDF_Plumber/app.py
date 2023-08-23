from flask import Flask, render_template, request, redirect
import pdfplumber
import pandas as pd
import numpy as np
import re
import os
from itertools import chain

app = Flask(__name__)

UPLOAD_FOLDER = "static/files"

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER


@app.route('/', methods=['GET', 'POST'])
def home():
    if request.method == "POST":
        pdf_file = request.files['pdf_file']
        column_names = request.form['columns']

        if pdf_file:
            path = os.path.join(app.config['UPLOAD_FOLDER'], pdf_file.filename)
            if os.path.exists(path):
                os.remove(path)
            pdf_file.save(path)
        file_path = os.listdir(UPLOAD_FOLDER)
        
        try:
            with pdfplumber.open(UPLOAD_FOLDER+"/"+file_path[0]) as pdf:
                table = pdf.pages[0].extract_tables()
                text = pdf.pages[0].extract_text(layout=False)

            table.sort(key=len)
            table = table[-2:]

            if table[0][0][0] == "LINE":
                line_table = table[0]
                other_table = table[1]
            else:
                line_table = table[1]
                other_table = table[0]

            data_frame = pd.DataFrame(line_table)
            data_frame.columns = data_frame.iloc[0]
            data_frame = data_frame.drop(0)

            data_frame.columns = data_frame.columns.str.replace('\n', ' ')
            # required_columns = ['LINE', 'SKU', 'DESCRIPTION LINE ITEM COMMENTS', 'UNIT COST/ RETAIL PRICE', 'QTY', 'ITEM TOTAL']
            column_names = column_names.split(",")
            required_columns = list(map(lambda text: re.sub(r'\s+', ' ', text.strip()), column_names))
            column_name = ['LINE']
            required_columns.extend(column_name)
            required_columns = np.unique(required_columns)
            # print("required_columns", required_columns)
            selected_df = data_frame[required_columns].copy()

            selected_df = selected_df.iloc[:-1]
            selected_df = selected_df.replace('\n',' ', regex=True)
            final_df = selected_df.set_index("LINE")
            json_output_line = final_df.to_json(orient = 'columns')

            vendor_name = "Costco Canada"
            result = list(chain(other_table[0], other_table[1], other_table[3]))
            order_number_pattern = r'Order #:\s+(\d+)'
            match = re.search(order_number_pattern, text)
            order_num = match.group(1)
            result = list(map(lambda text: text.replace('\n', ''), result))

            dic_all_item = {}
            pattern_a = r":(.+)"
            pattern_b = r"(.+):"
            for itter in result:
                match_bef = re.search(pattern_b, itter)
                match_aft = re.search(pattern_a, itter)
                dic_all_item[match_bef.group(1)] = match_aft.group(1)

            list_other = ["PO Date", "Requested Ship Date", "Requested Delivery Date", "Cancel Date", "Vendor #"]
            final_dic_other = {}
            final_dic_other['Vendor Name'] = vendor_name
            final_dic_other['Order Number'] = order_num
            for zzz in dic_all_item:
                if zzz in list_other:
                    final_dic_other[zzz] = dic_all_item[zzz]

            path = os.path.join(app.config['UPLOAD_FOLDER'], file_path[0])
            if os.path.exists(path):
                os.remove(path)
            context = {'json_output_line':json_output_line, 'final_dic_other':final_dic_other}
            return render_template("index.html", context=context)
        except:
            path = os.path.join(app.config['UPLOAD_FOLDER'], file_path[0])
            if os.path.exists(path):
                os.remove(path)
            context = {'json_output_line':[], 'final_dic_other':[]}
            return render_template("index.html", context=context)
    else:
        context = {'json_output_line':[], 'final_dic_other':[]}
        return render_template("index.html", context=context)

if __name__ == "__main__":
    app.run(debug=True)
