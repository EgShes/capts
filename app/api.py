from flask import Flask, escape, request, jsonify, abort, make_response
import torch
import numpy as np
import matplotlib.pyplot as plt
import pickle
from businesslogic.nets import FNSCaptchasNet, DeclarationCaptchasNet

app = Flask(__name__)


def prepare_image(im, mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]):
    im = im / 255
    return (im - mean) / std


def predict(im, net, threshold=0.9):
    im = torch.FloatTensor(im).permute(2, 0, 1).cuda()
    with torch.no_grad():
        pred = net.model([im])
    pred_class = [net.vocab[i] for i in list(pred[0]['labels'].detach().cpu().numpy())]
    pred_boxes = [[(i[0], i[1]), (i[2], i[3])] for i in list(pred[0]['boxes'].detach().cpu().numpy())]
    pred_score = pred[0]['scores'].detach().cpu().numpy()

    indxs = np.argsort([i[0][0] for i in pred_boxes])
    res = ''.join(np.array(pred_class)[indxs])
    confidence = np.prod(pred_score)

    return res, confidence


def error_response(text):
    abort(make_response(jsonify(success=False,
                                message=text), 500))


@app.route('/prediction', methods=['POST'])
def api():
    if 'image' not in request.files or 'captcha_type' not in request.files:
        error_response("You should pass image and captcha_type attributes")
    if request.files['captcha_type'] not in ['fns', 'declaration']:
        error_response(f'Invalid captcha type. Must be fns or declaration. Got {request.files["captcha_type"]}')

    try:
        img = plt.imread(request.files['image'])
    except:
        error_response("'image' field must contain binaries of png captcha from declaration site")

    try:
        if request.files['captcha_type'] == 'fns':
            assert img.shape == (100, 200, 4), \
                'Invalid image size. For fns captcha size must be (100, 200, 4). Got {img.shape}'
        if request.files['captcha_type'] == 'declaration':
            assert img.shape == (80, 160, 4), \
                'Invalid image size. For fns captcha size must be (80, 160, 4). Got {img.shape}'
    except AssertionError as e:
        error_response(e)

    img = prepare_image(img[:, :, :3])

    if request.files['captcha_type'] == 'fns':
        result, confidence = predict(img, FNSCaptchasNet)
    if request.files['captcha_type'] == 'declaration':
        result, confidence = predict(img, DeclarationCaptchasNet)

    response = jsonify(dict(
        success=True,
        confidence=str('{:.4f}'.format(confidence)),
        text=result,
    ))

    return response


if __name__ == '__main__':
    fns_model = FNSCaptchasNet('../weights/vocab_fns.pkl', '../weights/fns_model_weights.ptr')
    decl_model = DeclarationCaptchasNet('../weights/vocab_declaration.pkl', '../weights/declaration_model_weigths.ptr')
    app.run(debug=False)
