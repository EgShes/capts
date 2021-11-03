import argparse

from capts.businesslogic.nets import DeclarationCaptchasNet, FNSCaptchasNet
from capts.businesslogic.processor import AlcoCaptchaProcessor, FnsCaptchaProcessor
from capts.businesslogic.queue import Config, get_consumer_channel
from capts.config import CaptchaType, nn_logger

captcha_type2processor = {CaptchaType.fns.name: FnsCaptchaProcessor}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument("net_type", choices=[CaptchaType.fns.name, CaptchaType.alcolicenziat.name])
    args = parser.parse_args()

    if args.net_type == CaptchaType.fns.name:
        model = FNSCaptchasNet("/weights/vocab_fns.pkl", "/weights/fns_model_weights.ptr").eval()
        ProcessorClass = FnsCaptchaProcessor
        in_queue = Config.FNS_QUEUE
    elif args.net_type == CaptchaType.alcolicenziat.name:
        model = DeclarationCaptchasNet("weights/vocab_declaration.pkl", "weights/declaration_model_weigths.ptr").eval()
        ProcessorClass = AlcoCaptchaProcessor
        in_queue = Config.ALCO_QUEUE
    else:
        raise NotImplementedError
    nn_logger.info("Initialized model")

    channel = get_consumer_channel()
    nn_logger.info(f"Connected to channel {channel}")

    processor = ProcessorClass(model=model, channel=channel, in_queue=in_queue)
    nn_logger.info("Listening to messages")
    processor.start_consuming()
