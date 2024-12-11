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
        Path to the configuration file.
    keys : lst
        List of API keys.
    inst_tokens : lst
        List of InstTokens. The corresponding API keys must match the position of the InstTokens.
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


def check_sections(config: Type[ConfigParser]) -> None:
    """Auxiliary function to check if all sections exist."""
    for section in ['Directories', 'Authentication', 'Requests']:
        if not config.has_section(section):
            raise NoSectionError(section)


def check_default_paths(config: Type[ConfigParser], config_path: Path) -> None:
    """Auxiliary function to check if default cache paths exist.
    If not, the paths are writen in the config.
    """
    for api, path in DEFAULT_PATHS.items():
        if not config.has_option('Directories', api):
            config.set('Directories', api, str(path))
            with open(config_path, 'w', encoding='utf-8') as ouf:
                config.write(ouf)


def check_keys_tokens() -> None:
    """Auxiliary function to check if API keys or InstTokens are set."""
    keys = get_keys()
    insttokens = get_insttokens()
    # 3 problematic cases
    no_keys_no_insttokens = True if not keys and not insttokens else False
    insttokens_no_keys = True if insttokens and not keys else False
    keys_and_insttokens = True if keys and insttokens else False
    keys_tokens_diff = len(keys) - len(insttokens)

    if no_keys_no_insttokens:
        raise ValueError('No API keys or InstTokens found. '
                         'Please provide at least one API key or InstToken. '
                         'For more information visit: '
                         'https://pybliometrics.readthedocs.io/en/stable/configuration.html')
    elif insttokens_no_keys:
        raise ValueError('InstTokens found but not corresponding API keys. '
                         'Please provide the API keys that correspond to the InstTokens. '
                         'For more information visit: '
                         'https://pybliometrics.readthedocs.io/en/stable/configuration.html')
    elif keys_and_insttokens:
        if keys_tokens_diff < 0:
            raise ValueError('More InstTokens than API keys found. '
                             'Please provide all the API keys that correspond to the InstTokens. '
                             'For more information visit: '
                             'https://pybliometrics.readthedocs.io/en/stable/configuration.html')


def create_cache_folders(config: Type[ConfigParser]) -> None:
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
    """Function to get the InstToken and overwrite InstToken in config if needed."""
    inst_tokens = []
    if CUSTOM_INSTTOKENS:
        inst_tokens = CUSTOM_INSTTOKENS
    else:
        if not CUSTOM_KEYS: # if custom keys are set, config inst tokens are not needed
            try:
                raw_token_text = CONFIG.get('Authentication', 'InstToken')
                inst_tokens = [k.strip() for k in raw_token_text.split(",")]
            except NoOptionError:
                inst_tokens = []

    #key_token_pairs = list(zip(get_all_keys(), inst_tokens))
    return inst_tokens


def get_keys() -> list[str]:
    """Function to get all the API keys and overwrite keys in config if needed."""
    if CUSTOM_KEYS:
        keys = CUSTOM_KEYS
    else:
        try:
            raw_keys_text = CONFIG.get('Authentication', 'APIKey')
            keys = [k.strip() for k in raw_keys_text.split(",")]
        except NoOptionError:
            keys = []
    return keys
