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
        v_list = ['Select One Vendor', 'Costco Canada', 'Acme Dry Ice', 'Edgewater Properties LLC', 'Cambrige']
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
            elif selected_ven == "Cambrige":
                 def extracting_miscellaneous_item(miscellaneous_list,result_dict):
                    if 'Miscellaneous' not in result_dict:
                        mis_item = {}
                        mis_item[miscellaneous_list[0][0]] = miscellaneous_list[1][0]
                        mis_item[miscellaneous_list[0][1]] = miscellaneous_list[1][1]
                        mis_item[miscellaneous_list[0][2]] = miscellaneous_list[1][2]
                        result_dict['Miscellaneous'] = mis_item
                 def extract_item_information_from_Cambridge_Scientific(item_tables,result_dict):
                        item_table = [[item for item in sublist if item is not None] for sublist in item_tables]
                        miscellaneous_list = item_table[:2]
                        result_dict = extracting_miscellaneous_item(miscellaneous_list,result_dict)
                        filtered_list = item_table[2:-3]
                        item_list = [item for item in filtered_list if any(subitem.strip() != '' for subitem in item)]
                        df = pd.DataFrame(item_list[1:], columns=item_list[0])
                        df_dict = df.to_dict(orient='records')
                        if 'ITEM' not in result_dict:
                            result_dict['ITEM'] = []
                        result_dict['ITEM'].append(df_dict)
                        return result_dict 
                 def extract_invoice_number_information_Cambridge_Scientific(table,result_dict):
                        df = pd.DataFrame(table[1:], columns=table[0])
                        column_names = df.columns.tolist()
                        df_dict = df.to_dict(orient='records')
                        df_dict = [item for item in df_dict if item is not None]
                        result_dict[column_names[0]] = df_dict[0][column_names[0]]
                        result_dict[column_names[1]] = df_dict[0][column_names[1]]
                        return result_dict 
                 def extract_BillTo_ShipTo_from_Cambridge_Scientific(bill_table,ship_table,result_dict):
                        result_dict[bill_table[0][0]] = bill_table[1][0]
                        result_dict[ship_table[0][0]] = ship_table[1][0]
                        return result_dict 
                 def get_total_values_from_Cambridge_Scientific(total_tables,result_dict):
                        total_table = [[item for item in sublist if item is not None] for sublist in total_tables]
                        text = total_table[-1][0]
                        new_text = re.sub(r'\(cid:\d+\)', '$', text)
                        result_dict['Total'] = new_text
                        return result_dict 
                 def extract_invoice_table_from_Cambridge_Scientific(pdf_path):
                        
                        test_table_settings = {
                            "horizontal_strategy":"lines",
                            "vertical_strategy":"lines"
                        }
                        test_tables = []
                        result_dict = {}
                        with pdfplumber.open(pdf_path) as pdf:
                            for page_number in range(len(pdf.pages)):
                                page = pdf.pages[page_number]
                                extracted_tables = page.extract_tables(test_table_settings)
                                print("result_dictvvvvvvvvvvvvvvvv", extracted_tables)
                                if page_number==0:
                                    result_dict = extract_invoice_number_information_Cambridge_Scientific(extracted_tables[0],result_dict)
                                    result_dict = extract_BillTo_ShipTo_from_Cambridge_Scientific(extracted_tables[1],extracted_tables[2],result_dict)
                                if page_number==(len(pdf.pages)-1):
                                    result_dict = get_total_values_from_Cambridge_Scientific(extracted_tables[-1],result_dict)
                                    result_dict = extract_item_information_from_Cambridge_Scientific(extracted_tables[3],result_dict)
                            print("result_dictvvvvvvvvvvvvvvvv", result_dict)
                        return result_dict 
                 def process_of_extracting_Cambridge_Scientific_template(pdf_path):
                        result_dict = extract_invoice_table_from_Cambridge_Scientific (pdf_path)
                        return result_dict
                 pdf_path = UPLOAD_FOLDER+"/"+file_path[0]
                 print("pdf_path",  pdf_path)
                 results = process_of_extracting_Cambridge_Scientific_template(UPLOAD_FOLDER+"/"+file_path[0]) 
                 print("results", results)
                 context = {'json_output_line':results, 'final_dic_other':final_dic_other, 'v_list':v_list}
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
                column_names = column_names.split(",")
                if '' in column_names: column_names.remove('')
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
        v_list = ['Select One Vendor', 'Costco Canada', 'Acme Dry Ice', 'Edgewater Properties LLC', 'Cambrige']
        context = {'json_output_line':[], 'final_dic_other':[], 'v_list':v_list}
        return render_template("index.html", context=context)

if __name__ == "__main__":
    app.run(debug=True)
