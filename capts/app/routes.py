from flask import request, jsonify, abort, make_response
from capts.app import app, fns_model, decl_model
from capts.businesslogic.utils import norm_image, predict
import matplotlib.pyplot as plt


@app.route('/prediction', methods=['POST'])
def prediction():
    """
    You must provide one argument - captcha_type ['fns', 'declaration']
                     one file - binary of image [accepted image types - png, jpg, bin (loaded from fns site)]
    :return: json: success: true or false
                   confidence: confidence score of prediction (in case of success)
                   text: captcha recognized text (in case of success)
                   message: message describing what went wrong (in case of failure)

    """
    if 'image' not in request.files:
        error_response("You should pass image and captcha_type attributes")
    if 'captcha_type' not in request.args:
        error_response(f'Parameter not sent. You must provide captcha_type attribute')
    if request.args['captcha_type'] not in ['fns', 'declaration']:
        error_response(f'Invalid captcha type. Must be fns or declaration. Got {request.args["captcha_type"]}')

    try:
        img = plt.imread(request.files['image'])
    except:
        error_response("provided image must represent binaries of captcha")

    if request.args['captcha_type'] == 'fns':
        if img.shape != (100, 200, 4) and img.shape != (100, 200, 3):
            error_response(f'Invalid image size. For fns captcha size must be (100, 200, 4). Got {img.shape}')
    elif request.args['captcha_type'] == 'declaration':
        if img.shape != (80, 160, 3):
            error_response(f'Invalid image size. For fns captcha size must be (80, 160, 3). Got {img.shape}')

    img = img[:, :, :3]

    if request.args['captcha_type'] == 'fns':
        img = img / 255.
        result, confidence = predict(img, fns_model)
    if request.args['captcha_type'] == 'declaration':
        img = norm_image(img)
        result, confidence = predict(img, decl_model)

    response = jsonify(dict(
        success=True,
        confidence=str('{:.4f}'.format(confidence)),
        text=result,
    ))

    return response


def error_response(text):
    abort(make_response(jsonify(success=False,
                                message=text), 500))