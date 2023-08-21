from flask import Flask, render_template, request, redirect
import pdfplumber
import pandas as pd
import re
import os

app = Flask(__name__)

UPLOAD_FOLDER = "static/files"

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER


@app.route('/', methods=['GET', 'POST'])
def home():
    return render_template("index.html")

@app.route('/upload', methods=['POST'])
def upload():
    pdf_file = request.files['pdf_file']
    column_names = request.form['columns']
    if pdf_file:
        path = os.path.join(app.config['UPLOAD_FOLDER'], pdf_file.filename)
        if os.path.exists(path):
            os.remove(path)
        pdf_file.save(path)
    file_path = os.listdir(UPLOAD_FOLDER)
    
    with pdfplumber.open(UPLOAD_FOLDER+"/"+file_path[0]) as pdf:
        table = pdf.pages[0].extract_table()
    data_frame = pd.DataFrame(table)
    data_frame.columns = data_frame.iloc[0]
    data_frame = data_frame.drop(0)

    data_frame.columns = data_frame.columns.str.replace('\n', ' ')
    # required_columns = ['LINE', 'SKU', 'DESCRIPTION LINE ITEM COMMENTS', 'UNIT COST/ RETAIL PRICE', 'QTY', 'ITEM TOTAL']
    column_names = column_names.split(",")
    required_columns = list(map(lambda text: re.sub(r'\s+', ' ', text.strip()), column_names))
    selected_df = data_frame[required_columns].copy()

    selected_df = selected_df.iloc[:-1]
    selected_df = selected_df.replace('\n',' ', regex=True)
    final_df = selected_df.set_index("LINE")
    json_output = final_df.to_json(orient = 'columns')

    path = os.path.join(app.config['UPLOAD_FOLDER'], file_path[0])
    if os.path.exists(path):
        os.remove(path)

    return render_template("index.html", json_output=json_output)


if __name__ == "__main__":
    app.run(debug=True)
