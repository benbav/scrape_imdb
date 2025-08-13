#!/usr/bin/env python3

import asyncio
from imdb_scraper import main
import os
import platform

if __name__ == "__main__":
    if platform.system() == "Linux":
        tmp_dir = os.path.expanduser('~/tmp')
        os.makedirs(tmp_dir, exist_ok=True)  # This will create the directory if it doesn't exist
        os.environ['TMPDIR'] = tmp_dir
    asyncio.run(main())