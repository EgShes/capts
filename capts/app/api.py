from flask import Flask, request, jsonify, abort, make_response
import torch
import numpy as np
import matplotlib.pyplot as plt
from capts.businesslogic.nets import FNSCaptchasNet, DeclarationCaptchasNet

app = Flask(__name__)


fns_model = FNSCaptchasNet('weights/vocab_fns.pkl', 'weights/fns_model_weights.ptr').eval()
decl_model = DeclarationCaptchasNet('weights/vocab_declaration.pkl', 'weights/declaration_model_weigths.ptr').eval()
print('Models loaded')


def norm_image(im, mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]):
    im = im / 255
    return (im - mean) / std


def predict(im, net, threshold=0.9):
    im = torch.FloatTensor(im).permute(2, 0, 1)
    with torch.no_grad():
        pred = net.model([im])
    pred_class = [net.vocab[i] for i in list(pred[0]['labels'].detach().cpu().numpy())]
    pred_boxes = [[(i[0], i[1]), (i[2], i[3])] for i in list(pred[0]['boxes'].detach().cpu().numpy())]
    pred_score = pred[0]['scores'].detach().cpu().numpy()

    keep = pred_score > threshold
    pred_class, pred_boxes, pred_score = np.array(pred_class)[keep], np.array(pred_boxes)[keep], pred_score[keep]

    indxs = np.argsort([i[0][0] for i in pred_boxes])
    res = ''.join(np.array(pred_class)[indxs])
    confidence = np.prod(pred_score)

    return res, confidence


def error_response(text):
    abort(make_response(jsonify(success=False,
                                message=text), 500))


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


if __name__ == '__main__':

    app.run(debug=True)
