# from flask import Flask
# from capts.businesslogic.nets import FNSCaptchasNet, DeclarationCaptchasNet
#
# app = Flask(__name__)
# fns_model = FNSCaptchasNet('weights/vocab_fns.pkl', 'weights/fns_model_weights.ptr').eval()
# decl_model = DeclarationCaptchasNet('weights/vocab_declaration.pkl', 'weights/declaration_model_weigths.ptr').eval()
# print('Models loaded')
#
# from capts.app import routes
