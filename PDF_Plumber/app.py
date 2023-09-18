from flask import Flask, render_template, request
import pdfplumber
import pandas as pd
import numpy as np
import re
import os

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
        selected_ven = request.form['vendor']
        if pdf_file:
            path = os.path.join(app.config['UPLOAD_FOLDER'], pdf_file.filename)
            if os.path.exists(path):
                os.remove(path)
            pdf_file.save(path)
        file_path = os.listdir(UPLOAD_FOLDER)
        # List the vendors of interest here. Every individual here needs unique logic.
        # Currenlty, there are only 3 vendors we have configured.
        # Test ONLY the inovoices of the vendors mentioned here
        v_list = ['Select One Vendor', 'Costco Canada', 'Acme Dry Ice', 'Edgewater Properties LLC']
        try:
            if selected_ven == "Costco Canada":
                with pdfplumber.open(UPLOAD_FOLDER+"/"+file_path[0]) as pdf:
                    table = pdf.pages[0].extract_tables()
                    text = pdf.pages[0].extract_text(layout=False)
                line_table = table[2]
                other_table = table[0]

                data_frame = pd.DataFrame(line_table)
                data_frame.columns = data_frame.iloc[0]
                data_frame = data_frame.drop(0)

                data_frame.columns = data_frame.columns.str.replace('\n', ' ')
                column_names = column_names.split(",")
                if '' in column_names: column_names.remove('')
                required_columns = list(map(lambda text: re.sub(r'\s+', ' ', text.strip()), column_names))

                column_name = ['LINE']
                required_columns.extend(column_name)
                required_columns = np.unique(required_columns)
                for col in required_columns:
                    if col not in list(data_frame.columns):
                        context = {'json_output_line':[], 'final_dic_other':[], 'v_list':v_list, 'col_not':col}
                        return render_template("index.html", context=context)
                selected_df = data_frame[required_columns].copy()

                selected_df = selected_df.iloc[:-1]
                selected_df = selected_df.replace('\n',' ', regex=True)
                final_df = selected_df.set_index("LINE")
                json_output_line = final_df.to_dict()

                vendor_name = "Costco Canada"
                result = other_table[0] + other_table[1] + other_table[3]
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
                context = {'json_output_line':json_output_line, 'final_dic_other':final_dic_other, 'v_list':v_list}
                return render_template("index.html", context=context)
            
            elif selected_ven == "Acme Dry Ice":
                with pdfplumber.open(UPLOAD_FOLDER+"/"+file_path[0]) as pdf:
                    table = pdf.pages[0].extract_tables()
                line_table = table[4]
                data_frame = pd.DataFrame(line_table)
                data_frame.columns = data_frame.iloc[0]
                data_frame = data_frame.drop(0)
                del data_frame[None]
                data_frame.dropna(inplace=True)
                if data_frame['Description'].values[-1] != "Shipping Charges":
                    data_frame = data_frame.drop(data_frame.index[-1])
                data_frame = data_frame.rename_axis('LINE')
                # data_frame.columns = [column.upper() for column in data_frame.columns]
                # print("data_frame", data_frame)
                column_names = column_names.split(",")
                if '' in column_names: column_names.remove('')
                # print("column_names", column_names)
                required_columns = list(map(lambda text: re.sub(r'\s+', ' ', text.strip()), column_names))
                for col in required_columns:
                    if col not in list(data_frame.columns):
                        context = {'json_output_line':[], 'final_dic_other':[], 'v_list':v_list, 'col_not':col}
                        return render_template("index.html", context=context)
                selected_df = data_frame[required_columns].copy()
                json_output_line = selected_df.to_dict()
                other_table = table[0]
                vendor_name = "Acme Dry Ice Co./Acme Ice Co."
                final_dic_other = {}
                final_dic_other['Vendor Name'] = vendor_name
                final_dic_other['Date'] = other_table[1][0]
                final_dic_other['Invoice No'] = other_table[1][1]
                final_dic_other['Ship to'] = table[2][1][0].replace('\n',' ')
                path = os.path.join(app.config['UPLOAD_FOLDER'], file_path[0])
                if os.path.exists(path):
                    os.remove(path)
                context = {'json_output_line':json_output_line, 'final_dic_other':final_dic_other, 'v_list':v_list}
                return render_template("index.html", context=context)
            
            elif selected_ven == "Edgewater Properties LLC":
                with pdfplumber.open(UPLOAD_FOLDER+"/"+file_path[0]) as pdf:
                    table_other = pdf.pages[0].extract_tables()
                    table_line = pdf.pages[0].extract_tables(table_settings={"horizontal_strategy": "text"})
                    data_frame = pd.DataFrame(table_line[2])
                data_frame.columns = data_frame.iloc[0]
                data_frame = data_frame.drop(0)
                data_frame['Description'].replace('', np.nan, inplace=True)
                data_frame.dropna(inplace=True)
                data_frame = data_frame.reset_index(drop=True)
                data_frame = data_frame.rename_axis('LINE')
                data_frame.index += 1
                column_names = column_names.split(",")
                if '' in column_names: column_names.remove('')
                required_columns = list(map(lambda text: re.sub(r'\s+', ' ', text.strip()), column_names))
                for col in required_columns:
                    if col not in list(data_frame.columns):
                        context = {'json_output_line':[], 'final_dic_other':[], 'v_list':v_list, 'col_not':col}
                        return render_template("index.html", context=context)
                selected_df = data_frame[required_columns].copy()
                json_output_line = selected_df.to_dict()
                vendor_name = "Edgewater Properties LLC"
                final_dic_other = {}
                final_dic_other['Vendor Name'] = vendor_name
                final_dic_other['Date'] = table_other[0][1][0]
                final_dic_other['Invoice No'] = table_other[0][1][1]
                final_dic_other['Bill To'] = table_other[1][1][0].replace('\n',' ')
                context = {'json_output_line':json_output_line, 'final_dic_other':final_dic_other, 'v_list':v_list}
                return render_template("index.html", context=context)
        except:
            path = os.path.join(app.config['UPLOAD_FOLDER'], file_path[0])
            if os.path.exists(path):
                os.remove(path)
            context = {'json_output_line':[], 'final_dic_other':[], 'v_list':v_list}
            return render_template("index.html", context=context)
    else:
        v_list = ['Select One Vendor', 'Costco Canada', 'Acme Dry Ice', 'Edgewater Properties LLC']
        context = {'json_output_line':[], 'final_dic_other':[], 'v_list':v_list}
        return render_template("index.html", context=context)

if __name__ == "__main__":
    app.run(debug=True)
