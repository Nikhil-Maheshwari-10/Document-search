import logging

def setup_logger():
    try:
        import colorlog 
        logger = colorlog.getLogger('docsearch')
        if not logger.hasHandlers():
            handler = colorlog.StreamHandler()
            handler.setFormatter(colorlog.ColoredFormatter(
                '%(log_color)s%(levelname)s:%(name)s:%(reset)s %(message)s',
                log_colors={
                    'DEBUG': 'cyan',
                    'INFO': 'green',
                    'WARNING': 'yellow',
                    'ERROR': 'red',
                    'CRITICAL': 'bold_red',
                }
            ))
            logger.addHandler(handler)
        logger.setLevel(logging.DEBUG)
    except ImportError:
        logger = logging.getLogger('docsearch')
        if not logger.hasHandlers():
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(levelname)s:%(name)s: %(message)s')
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        logger.setLevel(logging.DEBUG)
    return logger

logger = setup_logger()
