"""Fix Pydantic model_ namespace warnings by configuring protected namespaces."""

import warnings
from pydantic import BaseModel

# Configure Pydantic to allow model_ fields without warnings
BaseModel.model_config["protected_namespaces"] = ("settings_",)

# Suppress the specific warnings about model_ namespace conflicts
warnings.filterwarnings(
    "ignore",
    message='Field "model_.*" in .* has conflict with protected namespace "model_"',
    category=UserWarning
)
