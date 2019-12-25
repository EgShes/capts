import torch
import torch.nn as nn
import torchvision
from torchvision.models.detection import faster_rcnn, fasterrcnn_resnet50_fpn
import pickle


def load_weights(model, weights):
    try:
        state_dict = weights['model_state_dict']
        missing_keys, unexpected_keys = model.load_state_dict(state_dict, strict=False)
        if len(missing_keys) != 0 or len(unexpected_keys) != 0:
            raise ValueError()

    except FileNotFoundError:
        print('Invalid model weights file! Model is initialized randomly')
    except ValueError:
        print('Weights dont match with model! Model is initialized randomly')
    except KeyError:
        print('Invalid model weights! Key model_state_dict is absent')

    return None


class FNSCaptchasNet(nn.Module):
    """
    class for net for solving captchas from https://service.nalog.ru/ (Федеральная налоговая служба)
    """
    def __init__(self, vocab_path, weights_path=None):
        super().__init__()
        self.vocab = pickle.load(open(vocab_path, 'rb'))
        self.weights = torch.load(weights_path) if weights_path else None

        self.model = self.make_model(n_classes=len(self.vocab) + 1)
        if self.weights:
            load_weights(self.model, self.weights)

    def make_model(self, n_classes):
        model = fasterrcnn_resnet50_fpn(pretrained=False)

        in_features = model.roi_heads.box_predictor.cls_score.in_features
        model.roi_heads.box_predictor = faster_rcnn.FastRCNNPredictor(in_features, n_classes)

        return model

    def forward(self, inputs):
        return self.model(inputs)


class DeclarationCaptchasNet(nn.Module):
    """
    class for net for solving captchas from https://service.alcolicenziat.ru/ (Информационная система Cубъекта
    Российской Федерации по приему деклараций)
    """

    def __init__(self, vocab_path, weights_path=None):
        super().__init__()
        self.vocab = pickle.load(open(vocab_path, 'rb'))
        self.weights = torch.load(weights_path) if weights_path else None

        self.model = self.make_model(n_classes=len(self.vocab) + 1)
        if self.weights:
            load_weights(self.model, self.weights)

    def make_model(self, n_classes):
        backbone = torchvision.models.mobilenet_v2(pretrained=False).features
        backbone.out_channels = 1280

        anchor_generator = faster_rcnn.AnchorGenerator(sizes=((32, 64, 128, 256, 512),),
                                                       aspect_ratios=((0.5, 1.0, 2.0),))

        roi_pooler = torchvision.ops.MultiScaleRoIAlign(featmap_names=[0], output_size=7, sampling_ratio=2)

        model = faster_rcnn.FasterRCNN(backbone, num_classes=n_classes,
                                       rpn_anchor_generator=anchor_generator,
                                       box_roi_pool=roi_pooler)
        return model

    def forward(self, inputs):
        return self.model(inputs)
