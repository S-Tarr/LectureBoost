#
# import os
#
# import boto3
# from flask import Flask, flash, request, redirect, url_for
# from flask import send_from_directory
# from werkzeug.utils import secure_filename
#
# s3 = boto3.client(
#     "s3",
#     aws_access_key_id=os.getenv('AWS_ACCESS_KEY'),
#     aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY')
# )
#
# UPLOAD_FOLDER = './uploads'
# ALLOWED_EXTENSIONS = {'mp4', 'py', 'txt'}
#
# app = Flask(__name__)
# app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
# app.add_url_rule(
#     "/uploads/<name>", endpoint="download_file", build_only=True
# )
#
#
# def upload_file_to_s3(file, acl="public-read"):
#     filename = secure_filename(file.filename)
#     try:
#         s3.upload_fileobj(
#             file,
#             os.getenv("AWS_BUCKET_NAME"),
#             file.filename,
#             ExtraArgs={
#                 "ACL": acl,
#                 "ContentType": file.content_type
#             }
#         )
#
#     except Exception as e:
#         # This is a catch all exception, edit this part to fit your needs.
#         print("Something Happened: ", e)
#         return e
#
#     # after upload file to s3 bucket, return filename of the uploaded file
#     return file.filename
#
# def allowed_file(filename):
#     return '.' in filename and \
#            filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS
#
# @app.route('/uploads/shravan')
# def return_shravan():
#     return {"hello " : "shravan"}
#
#
# @app.route('/uploads/<name>')
# def download_file(name):
#     return send_from_directory(app.config["UPLOAD_FOLDER"], name)
#
# @app.route('/methods/<whitespace>/<whitespace_val>/<subtitles>/<transcript>/<slideshow>', methods=['POST'])
# def methods(whitespace, whitespace_val, subtitles, transcript, slideshow):
#     if request.method == 'POST':
#         print(whitespace_val)
#
#     return '<!doctype html>'
#
# @app.route('/file', methods=['GET', 'POST'])
# def upload_file():
#     if request.method == 'POST':
#         # check if the post request has the file part
#         if 'file' not in request.files:
#             flash('No file part')
#             return redirect(request.url)
#         file = request.files['file']
#         print(file.content_type)
#         # If the user does not select a file, the browser submits an
#         # empty file without a filename.
#         if file.filename == '':
#             flash('No selected file')
#             return redirect(request.url)
#         if file and allowed_file(file.filename):
#
#             print("got file: ", file.filename)
#             print("file: ", file)
#
#             # TODO delete later; testing upload to s3 from here
#             output = upload_file_to_s3(file)
#             if output:
#                 print("success uploading to s3")
#             else:
#                 print("upload failed")
#
#             filename = secure_filename(file.filename)
#             #file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
#             return redirect(url_for('download_file', name=filename))
#     return '''
#     <!doctype html>
#     <title>Upload new File</title>
#     <h1>Upload new File</h1>
#     <form method=post enctype=multipart/form-data>
#       <input type=file name=file>
#       <input type=submit value=Upload>
#     </form>
#     '''
#
# if __name__ == '__main__':
#     print('running')
#     app.secret_key = 'super secret key'
#     app.config['SESSION_TYPE'] = 'filesystem'
#     app.run(debug=True, port=8001)


import os

import boto3
from flask import Flask, flash, request, redirect, jsonify
from flask import send_from_directory
from werkzeug.utils import secure_filename

from generateSlides import generate_slides
from subtitles import add_subtitles
from transcribe import transcribe
from whiteSpace import removeWhiteSpace

s3 = boto3.client(
    "s3",
    aws_access_key_id='***REMOVED***',
    aws_secret_access_key='***REMOVED***',
)

UPLOAD_FOLDER = './uploads'
ALLOWED_EXTENSIONS = {'mp4', 'py', 'txt'}

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.add_url_rule(
    "/uploads/<name>", endpoint="download_file", build_only=True
)

def upload_pdf_to_s3(filename):
    resource = boto3.resource(
        "s3",
        aws_access_key_id='***REMOVED***',
        aws_secret_access_key='***REMOVED***')
    resource.Object("lecture-boost", filename).upload_file(filename)
    location = s3.get_bucket_location(Bucket=os.environ.get("AWS_BUCKET_NAME"))['LocationConstraint']
    url = "https://s3-%s.amazonaws.com/%s/%s" % (location, os.environ.get("AWS_BUCKET_NAME"), filename)

    return url

def upload_file_to_s3(file, filename, acl="public-read"):
    try:
        s3.upload_fileobj(
            file,
            os.getenv("AWS_BUCKET_NAME"),
            filename,
        )

    except Exception as e:
        # This is a catch all exception, edit this part to fit your needs.
        print("Something Happened: ", e)
        return e

    # after upload file to s3 bucket, return filename of the uploaded file
    location = s3.get_bucket_location(Bucket=os.environ.get("AWS_BUCKET_NAME"))['LocationConstraint']
    print(location)
    url = "https://s3-%s.amazonaws.com/%s/%s" % (location, os.environ.get("AWS_BUCKET_NAME"), filename)
    print(url)

    return url


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/uploads/shravan')
def return_shravan():
    return {"hello ": "shravan"}


@app.route('/uploads/<name>')
def download_file(name):
    return send_from_directory(app.config["UPLOAD_FOLDER"], name)


@app.route('/file/<whitespace>/<whitespace_val>/<subtitles>/<transcript>/<slideshow>', methods=['GET', 'POST'])
def upload_file(whitespace, whitespace_val, subtitles, transcript, slideshow):
    response = {
        "transcript": "",
        "video": "",
        "textFromSlides": "",
        "slides": ""
    }
    if request.method == 'POST':
        # check if the post request has the file part
        print("============================")
        print(whitespace_val)
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)
        file = request.files['file']

        print("file content_length", file.content_length)
        # If the user does not select a file, the browser submits an
        # empty file without a filename.
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))


            if whitespace == "true":
                print("whitespace is true")
                removeWhiteSpace(folderName="uploads/", videoName=file.filename)
                white_space_filename = "uploads/" + file.filename[:-4] + "_cut.mp4"
                if subtitles == "true":
                    add_subtitles(white_space_filename)
                if transcript == "true":
                    transcribe(white_space_filename)
                    with open("uploads/transcription.txt", "rb") as f:
                        response_from_s3 = upload_file_to_s3(f, white_space_filename)
                        response["transcript"] = response_from_s3
                        if response_from_s3:
                            print("success uploading transcript to s3", response_from_s3)
                        else:
                            print("transcript upload failed")
                if slideshow == "true":
                    generate_slides(white_space_filename)
                    with open("uploads/slides.pdf", "rb") as f:
                        with open("uploads/textFromSlides.txt", "rb") as f2:
                            response_from_s3 = upload_file_to_s3(f, "uploads/slides.pdf")
                            response["slides"] = upload_pdf_to_s3("uploads/slides.pdf")
                            if response_from_s3:
                                print("success uploading slides to s3", response_from_s3)
                            else:
                                print("slides upload failed")
                            response_from_s3 = upload_file_to_s3(f2, "uploads/textFromSlides.txt")
                            response["textFromSlides"] = response_from_s3
                            if response_from_s3:
                                print("success uploading text fr slide to s3", response_from_s3)
                            else:
                                print("text from slide upload failed")

                with open(white_space_filename, "rb") as f:
                    response_from_s3 = upload_file_to_s3(f, white_space_filename)
                    response["video"] = response_from_s3
                    if response_from_s3:
                        print("success uploading to s3", response_from_s3)
                    else:
                        print("upload failed")
            else:
                print("whitespace is false")

                no_white_space_filename = "uploads/" + file.filename
                if subtitles == "true":
                    add_subtitles(no_white_space_filename)
                if transcript == "true":
                    transcribe(no_white_space_filename)
                    transcription_to_upload = open("uploads/transcription.txt", "rb")
                    response_from_s3 = upload_file_to_s3(transcription_to_upload, "uploads/transcription.txt")
                    response["transcript"] = response_from_s3
                    if response_from_s3:
                        print("success uploading transcript to s3", response_from_s3)
                    else:
                        print("transcript upload failed")
                if slideshow == "true":
                    generate_slides(no_white_space_filename)
                    slides_to_upload = open("uploads/slides.pdf", "rb")
                    text_from_slides_to_upload = open("uploads/textFromSlides.txt", "rb")
                    response_from_s3 = upload_file_to_s3(slides_to_upload, "uploads/slides.pdf")
                    response["slides"] = upload_pdf_to_s3("uploads/slides.pdf")
                    if response_from_s3:
                        print("success uploading slides to s3", response_from_s3)
                    else:
                        print("slides upload failed")
                    response_from_s3 = upload_file_to_s3(text_from_slides_to_upload, "uploads/textFromSlides.txt")
                    response["textFromSlides"] = response_from_s3
                    if response_from_s3:
                        print("success uploading text fr slide to s3", response_from_s3)
                    else:
                        print("text from slide upload failed")

                file_to_upload = open(no_white_space_filename, "r")
                response_from_s3 = upload_file_to_s3(file_to_upload, no_white_space_filename)
                response["video"] = response_from_s3
                if response_from_s3:
                    print("success uploading to s3", response_from_s3)
                else:
                    print("upload failed")

    final_response = jsonify(response)
    final_response.headers.add('Access-Control-Allow-Origin', '*')
    return final_response
    # return '''
    # <!doctype html>
    # <title>Upload new File</title>
    # <h1>Upload new File</h1>
    # <form method=post enctype=multipart/form-data>
    #   <input type=file name=file>
    #   <input type=submit value=Upload>
    # </form>
    # '''


# @app.route('/file', methods=['GET', 'POST'])
# def upload_file():
#     if request.method == 'POST':
#         # check if the post request has the file part
#         if 'file' not in request.files:
#             flash('No file part')
#             return redirect(request.url)
#         file = request.files['file']
#         print(file.content_type)
#         # If the user does not select a file, the browser submits an
#         # empty file without a filename.
#         if file.filename == '':
#             flash('No selected file')
#             return redirect(request.url)
#         if file and allowed_file(file.filename):
#
#             print()
#             print(request.values)
#             print(request.method)
#             print(request.headers)
#
#             print("file len", file.content_length)
#             print("got file: ", file.filename)
#             print("file: ", file)
#
#             # TODO delete later; testing upload to s3 from here
#             output = upload_file_to_s3(file)
#             if output:
#                 print("success uploading to s3", output)
#             else:
#                 print("upload failed")
#
#             #filename = secure_filename(file.filename)
#             #file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
#             #return redirect(url_for('download_file', name=filename))
#     return '''
#     <!doctype html>
#     <title>Upload new File</title>
#     <h1>Upload new File</h1>
#     <form method=post enctype=multipart/form-data>
#       <input type=file name=file>
#       <input type=submit value=Upload>
#     </form>
#     '''

if __name__ == '__main__':
    print('running')
    app.secret_key = 'super secret key'
    app.config['SESSION_TYPE'] = 'filesystem'
    # app.run(debug=True, port=8001)
    app.run(host='0.0.0.0', port=8080)
    print(os.environ.get("AWS_BUCKET_NAME"))
