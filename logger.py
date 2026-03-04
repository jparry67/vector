import logging

def get_logger(name: str) -> logging.Logger:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[
            logging.FileHandler("logs.txt", encoding='utf-8'),
            # logging.StreamHandler() # also write logs to stdout
        ]
    )
    return logging.getLogger(name)