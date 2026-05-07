""" Configuration file for the Business Impact Analyser API. """

# BIA GUI config
BIA_GUI_ADDRESS = "127.0.0.1"
BIA_GUI_PORT = "8003"

# Saving file config
SAVING_DIRECTORY = "BIA_api/savedRequests"
PREFIX_FILENAME = SAVING_DIRECTORY + "/bia_apiRequest_"
SUFFIX_FILENAME = '.log'
DEFAULT_MODEL_FILENAME = f'{SAVING_DIRECTORY}/defaultModel.json'
