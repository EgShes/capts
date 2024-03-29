import logging.config
from pathlib import Path
from typing import Union

import numpy as np
import torch
import yaml


class Logger:
    @classmethod
    def from_config(cls, logger_name: str, config_path: Union[str, Path]) -> logging.Logger:
        with open(config_path, "r") as f:
            config = yaml.safe_load(f.read())
        assert (
            logger_name in config["loggers"]
        ), f"No config found for the {logger_name} logger. Expected names {config['loggers']}"
        config["disable_existing_loggers"] = False
        logging.config.dictConfig(config)
        return logging.getLogger(logger_name)


def norm_image(im, mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]):
    im = im / 255
    return (im - mean) / std


def predict(im, net, threshold=0.9):
    im = torch.FloatTensor(im).permute(2, 0, 1)
    with torch.no_grad():
        pred = net.model([im])
    pred_class = [net.vocab[i] for i in list(pred[0]["labels"].detach().cpu().numpy())]
    pred_boxes = [[(i[0], i[1]), (i[2], i[3])] for i in list(pred[0]["boxes"].detach().cpu().numpy())]
    pred_score = pred[0]["scores"].detach().cpu().numpy()

    keep = pred_score > threshold
    pred_class, pred_boxes, pred_score = (
        np.array(pred_class)[keep],
        np.array(pred_boxes)[keep],
        pred_score[keep],
    )

    indxs = np.argsort([i[0][0] for i in pred_boxes])
    res = "".join(np.array(pred_class)[indxs])
    confidence = np.prod(pred_score)

    return res, confidence
