from configparser import ConfigParser, NoOptionError, NoSectionError
from collections import deque
from pathlib import Path
from typing import Optional, Type, Union

from pybliometrics.utils.constants import CONFIG_FILE, RATELIMITS, DEFAULT_PATHS, VIEWS
from pybliometrics.utils.create_config import create_config

CONFIG = None
CUSTOM_KEYS = None
CUSTOM_INSTTOKENS = None

_throttling_params = {k: deque(maxlen=v) for k, v in RATELIMITS.items()}


def init(config_dir: Union[str, Path] = CONFIG_FILE,
         keys: Optional[list[str]] = None,
         inst_tokens: Optional[list[str]] = None) -> None:
    """
    Function to initialize the Pybliometrics library. For more information go to the
    [documentation](https://pybliometrics.readthedocs.io/en/stable/configuration.html).
    
    Parameters
    ----------
    config_dir : str
        Path to the configuration file
    keys : lst
        List of API keys
    inst_tokens : lst
        List of tokens. The corresponding keys position in the list must match the
        position of the token in the list.
        
    """
    global CONFIG
    global CUSTOM_KEYS
    global CUSTOM_INSTTOKENS

    config_dir = Path(config_dir)

    if not config_dir.exists():
        CONFIG = create_config(config_dir, keys, inst_tokens)
    else:
        CONFIG = ConfigParser()
        CONFIG.optionxform = str
        CONFIG.read(config_dir)

    check_sections(CONFIG)
    check_default_paths(CONFIG, config_dir)
    create_cache_folders(CONFIG)

    CUSTOM_KEYS = keys
    CUSTOM_INSTTOKENS = inst_tokens
    check_keys_tokens()


def check_sections(config: ConfigParser) -> None:
    """Auxiliary function to check if all sections exist."""
    for section in ['Directories', 'Authentication', 'Requests']:
        if not config.has_section(section):
            raise NoSectionError(section)


def check_default_paths(config: ConfigParser, config_path: Path) -> None:
    """Auxiliary function to check if default cache paths exist.
    If not, the paths are writen in the config.
    """
    for api, path in DEFAULT_PATHS.items():
        if not config.has_option('Directories', api):
            config.set('Directories', api, str(path))
            with open(config_path, 'w', encoding='utf-8') as ouf:
                config.write(ouf)


def check_keys_tokens() -> None:
    """Auxiliary function to check if keys or tokens are set."""
    if not (get_keys() or get_insttokens()):
        raise ValueError('No API keys or InstTokens found.  '
                         'Please provide at least one key or token.  '
                         'For more information visit: '
                         'https://pybliometrics.readthedocs.io/en/stable/configuration.html')


def create_cache_folders(config: ConfigParser) -> None:
    """Auxiliary function to create cache folders."""
    for api, path in config.items('Directories'):
        for view in VIEWS[api]:
            view_path = Path(path, view)
            view_path.mkdir(parents=True, exist_ok=True)


def get_config() -> ConfigParser:
    """Function to get the config parser."""
    if not CONFIG:
        raise FileNotFoundError('No configuration file found.'
                                'Please initialize Pybliometrics with init().\n'
                                'For more information visit: '
                                'https://pybliometrics.readthedocs.io/en/stable/configuration.html')
    return CONFIG


def get_insttokens() -> list[tuple[str, str]]:
    """Function to get the inst tokens and overwrite tokens in config if needed."""
    inst_tokens = []
    if CUSTOM_INSTTOKENS:
        inst_tokens = CUSTOM_INSTTOKENS
    else:
        try:
            raw_token_text = CONFIG.get('Authentication', 'InstToken')
            inst_tokens = [k.strip() for k in raw_token_text.split(",")]
        except NoOptionError:
            inst_tokens = []
    key_token_pairs = list(zip(get_keys(), inst_tokens))
    return key_token_pairs


def get_keys() -> list[str]:
    """Function to get the API keys and overwrite keys in config if needed."""
    if CUSTOM_KEYS:
        keys = CUSTOM_KEYS
    else:
        try:
            raw_keys_text = CONFIG.get('Authentication', 'APIKey')
            keys = [k.strip() for k in raw_keys_text.split(",")]
        except NoOptionError:
            keys = []
    return keys
